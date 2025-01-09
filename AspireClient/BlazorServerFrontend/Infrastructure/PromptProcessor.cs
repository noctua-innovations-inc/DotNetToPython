using BlazorServerFrontend.Infrastructure.Abstractions;
using Polly;
using Polly.Retry;
using RabbitMQ.Client;
using RabbitMQ.Client.Events;
using RabbitMQ.Client.Exceptions;
using System.Collections.Concurrent;
using System.Net.Sockets;
using System.Text;

namespace BlazorServerFrontend.Infrastructure;

/// <summary>
/// A class responsible for processing prompts by interacting with RabbitMQ queues.
/// It handles registering/unregistering event handlers, sending requests, and managing RabbitMQ channels.
/// </summary>
public class PromptProcessor(IConnection _mqConnection, ILogger<PromptProcessor> _logger) : IDisposable, IPromptProcessor
{
    private bool disposedValue;

    /// <summary>
    /// Represents a subscription to a RabbitMQ queue, including the channel and consumer.
    /// </summary>
    private record Subscription(IChannel Channel, AsyncEventingBasicConsumer Consumer);

    /// <summary>
    /// A thread-safe dictionary to store event handlers and their associated subscriptions.
    /// The key is the event handler, and the value is a dictionary of queue names and their corresponding subscriptions.
    /// </summary>
    private readonly ConcurrentDictionary<AsyncEventHandler<BasicDeliverEventArgs>, ConcurrentDictionary<string, Subscription>> handlers = [];

    /// <summary>
    /// A retry policy to handle transient faults such as network issues or RabbitMQ server unavailability.
    /// It retries up to 3 times with exponential backoff.
    /// </summary>
    private readonly AsyncRetryPolicy retryPolicy = Policy
        .Handle<SocketException>()
        .Or<BrokerUnreachableException>()
        .Or<OperationInterruptedException>()
        .Or<Exception>() // Fallback for other exceptions
        .WaitAndRetryAsync(3, retryAttempt => TimeSpan.FromSeconds(Math.Pow(2, retryAttempt)));

    /// <summary>
    /// Creates a RabbitMQ channel with retry logic in case of transient failures.
    /// </summary>
    /// <returns>The created RabbitMQ channel.</returns>
    private async Task<IChannel> CreateChannelAsync()
    {
        IChannel? result = default;
        await retryPolicy.ExecuteAsync(async () =>
        {
            try
            {
                result = await _mqConnection.CreateChannelAsync();
                _logger.LogDebug("Successfully created RabbitMQ channel.");
            }
            catch (Exception ex)
            {
                _logger.LogCritical("Could not create channel due to exception: {message}", ex.ToString());
                result?.Dispose(); // Dispose the channel if it was created but an exception occurred.
                throw;
            }
        });
        return result!;
    }

    /// <summary>
    /// Declares a RabbitMQ queue with retry logic in case of transient failures.
    /// </summary>
    /// <param name="channel">The RabbitMQ channel to use for declaring the queue.</param>
    /// <param name="queue">The name of the queue to declare.</param>
    private async Task DeclareQueueWithRetryAsync(IChannel channel, string queue)
    {
        await retryPolicy.ExecuteAsync(async () =>
        {
            try
            {
                await channel.QueueDeclareAsync(
                    queue: queue,
                    durable: false,
                    exclusive: false,
                    autoDelete: false,
                    arguments: null);
                _logger.LogDebug("Successfully declared queue: {queue}.", queue);
            }
            catch (Exception ex)
            {
                _logger.LogCritical("Could not declare queue {queue} due to exception: {message}", queue, ex.ToString());
                throw;
            }
        });
    }

    /// <summary>
    /// Registers an event handler to consume messages from a specified RabbitMQ queue.
    /// If the event handler is already registered for the queue, no action is taken.
    /// </summary>
    /// <param name="asyncEventHandler">The event handler to register.</param>
    /// <param name="queue">The name of the queue to consume messages from. Defaults to "backend_to_frontend".</param>
    public async Task RegisterEventHandlerAsync(AsyncEventHandler<BasicDeliverEventArgs> asyncEventHandler, string queue = "backend_to_frontend")
    {
        if (asyncEventHandler == null)
        {
            throw new ArgumentNullException(nameof(asyncEventHandler));
        }

        // Use thread-safe operations to add the event handler.
        var handlerSubscriptions = handlers.GetOrAdd(asyncEventHandler, _ => new ConcurrentDictionary<string, Subscription>());

        if (handlerSubscriptions.ContainsKey(queue))
        {
            _logger.LogDebug("Event handler is already registered for queue: {queue}.", queue);
            return;
        }

        // Create a RabbitMQ channel and declare the queue.
        var channel = await CreateChannelAsync();
        await DeclareQueueWithRetryAsync(channel, queue);

        await retryPolicy.ExecuteAsync(async () =>
        {
            var consumer = new AsyncEventingBasicConsumer(channel);
            consumer.ReceivedAsync += asyncEventHandler;

            try
            {
                await channel.BasicConsumeAsync(
                    queue: queue,
                    autoAck: true,
                    consumer: consumer);
                _logger.LogDebug("Successfully subscribed to queue: {queue}.", queue);
            }
            catch (Exception ex)
            {
                _logger.LogCritical("Could not subscribe to queue {queue} due to exception: {message}", queue, ex.ToString());
                throw;
            }

            // Add the subscription atomically.
            handlerSubscriptions[queue] = new Subscription(channel, consumer);
        });
    }

    /// <summary>
    /// Unregisters an event handler from consuming messages from a specified RabbitMQ queue.
    /// If the event handler is not registered for the queue, no action is taken.
    /// </summary>
    /// <param name="asyncEventHandler">The event handler to unregister.</param>
    /// <param name="queue">The name of the queue to stop consuming messages from. Defaults to "backend_to_frontend".</param>
    public async Task UnRegisterEventHandlerAsync(AsyncEventHandler<BasicDeliverEventArgs> asyncEventHandler, string queue = "backend_to_frontend")
    {
        if (asyncEventHandler == null)
        {
            throw new ArgumentNullException(nameof(asyncEventHandler));
        }

        await retryPolicy.ExecuteAsync(async () =>
        {
            // Check if the event handler is registered for the specified queue.
            if (!handlers.TryGetValue(asyncEventHandler, out var value))
            {
                _logger.LogDebug("Event handler is not registered for any queue.");
                return;
            }
            if (!value.TryGetValue(queue, out var entry))
            {
                _logger.LogDebug("Event handler is not registered for queue: {queue}.", queue);
                return;
            }

            // Remove the subscription from the handlers dictionary.
            value.Remove(queue, out var _);
            if (value.IsEmpty)
            {
                handlers.Remove(asyncEventHandler, out var _);
            }

            // Unsubscribe the event handler and dispose of the channel.
            entry.Consumer.ReceivedAsync -= asyncEventHandler;
            await entry.Channel.DisposeAsync();
            _logger.LogDebug("Successfully unregistered event handler for queue: {queue}.", queue);
        });
    }

    /// <summary>
    /// Sends a prompt message to a specified RabbitMQ queue.
    /// </summary>
    /// <param name="prompt">The message to send.</param>
    /// <param name="queue">The name of the queue to send the message to. Defaults to "frontend_to_backend".</param>
    public async Task SendRequestAsync(string prompt, string queue = "frontend_to_backend")
    {
        // Create a RabbitMQ channel and declare the queue.
        using var channel = await CreateChannelAsync();
        await DeclareQueueWithRetryAsync(channel, queue);

        // Convert the prompt message to a byte array.
        var body = Encoding.UTF8.GetBytes(prompt);

        // Publish the message to the queue with retry logic.
        await retryPolicy.ExecuteAsync(async () =>
        {
            try
            {
                await channel.BasicPublishAsync(
                    exchange: "",
                    routingKey: queue,
                    mandatory: false,
                    body: body);
                _logger.LogDebug("Successfully published message to queue: {queue}.", queue);
            }
            catch (Exception ex)
            {
                _logger.LogCritical("Could not publish to queue {queue} due to exception: {message}", queue, ex.ToString());
                throw;
            }
        });
    }

    /// <summary>
    /// Disposes of resources used by the PromptProcessor, including RabbitMQ channels and consumers.
    /// </summary>
    /// <param name="disposing">True if called explicitly; false if called by the finalizer.</param>
    protected virtual async void Dispose(bool disposing)
    {
        if (disposedValue)
        {
            return;
        }
        if (!disposing)
        {
            return;
        }

        // Clean up all registered event handlers and their associated channels.
        foreach (var handler in handlers)
        {
            foreach (var entry in handler.Value)
            {
                entry.Value.Consumer.ReceivedAsync -= handler.Key;
                await entry.Value.Channel.DisposeAsync(); // Use DisposeAsync instead of Dispose.
            }
            handler.Value.Clear();
        }
        handlers.Clear();

        disposedValue = true;
        _logger.LogDebug("PromptProcessor resources have been disposed.");
    }

    /// <summary>
    /// Finalizer to ensure resources are cleaned up if Dispose is not called explicitly.
    /// </summary>
    ~PromptProcessor()
    {
        Dispose(disposing: true); // Dispose of both managed and unmanaged resources.
    }

    /// <summary>
    /// Disposes of resources used by the PromptProcessor.
    /// </summary>
    public void Dispose()
    {
        Dispose(disposing: true);
        GC.SuppressFinalize(this);
    }
}