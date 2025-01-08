using BlazorServerFrontend.Infrastructure.Abstractions;
using RabbitMQ.Client;
using RabbitMQ.Client.Events;
using System.Text;

namespace BlazorServerFrontend.Services;

public class PromptProcessor(IConnection _mqConnection) : IDisposable, IPromptProcessor
{
    private bool disposedValue;

    private record Subscription(IChannel Channel, AsyncEventingBasicConsumer Consumer);

    private readonly Dictionary<AsyncEventHandler<BasicDeliverEventArgs>, Dictionary<string, Subscription>> handlers = [];

    public async Task RegisterEventHandlerAsync(AsyncEventHandler<BasicDeliverEventArgs> asyncEventHandler, string queue = "backend_to_frontend")
    {
        if (handlers.ContainsKey(asyncEventHandler))
        {
            // The event handler has already been registered,
            // but was it registered to the specified queue?
            if (handlers[asyncEventHandler].ContainsKey(queue))
            {
                // Yes, the event handler has already been registered with the specified queue.
                // Nothing left to do.
                return;
            }
        }
        else
        {
            // The event handler has not been registered,
            // so allocate an entry for the registration.
            handlers[asyncEventHandler] = [];
        }

        var channel = await _mqConnection.CreateChannelAsync();

        await channel.QueueDeclareAsync(
            queue: queue,
            durable: false,
            exclusive: false,
            autoDelete: false,
            arguments: null);

        var consumer = new AsyncEventingBasicConsumer(channel);

        consumer.ReceivedAsync += asyncEventHandler;

        handlers[asyncEventHandler][queue] = new Subscription(channel, consumer);

        await channel.BasicConsumeAsync(
            queue: queue,
            autoAck: true,
            consumer: consumer);
    }

    public async Task UnRegisterEventHandlerAsync(AsyncEventHandler<BasicDeliverEventArgs> asyncEventHandler, string queue = "backend_to_frontend")
    {
        try
        {
            var entry = handlers[asyncEventHandler][queue];

            handlers[asyncEventHandler].Remove(queue);
            if (handlers[asyncEventHandler].Count == 0)
            {
                handlers.Remove(asyncEventHandler);
            }

            entry.Consumer.ReceivedAsync -= asyncEventHandler;
            await entry.Channel.DisposeAsync();
        }
        catch (Exception ex)
        {
        }
    }

    public async Task SendRequestAsync(string prompt, string queue = "frontend_to_backend")
    {
        using var channel = await _mqConnection.CreateChannelAsync();

        await channel.QueueDeclareAsync(
            queue: queue,
            durable: false,
            exclusive: false,
            autoDelete: false,
            arguments: null);

        ReadOnlyMemory<byte> body = Encoding.UTF8.GetBytes(prompt);

        await channel.BasicPublishAsync(
            exchange: "",
            routingKey: queue,
            mandatory: false,
            body: body);
    }

    protected virtual void Dispose(bool disposing)
    {
        if (!disposedValue)
        {
            if (disposing)
            {
                foreach (var handler in handlers)
                {
                    foreach (var entry in handler.Value)
                    {
                        entry.Value.Consumer.ReceivedAsync -= handler.Key;
                        entry.Value.Channel.Dispose();
                    }
                    handler.Value.Clear();
                }
                handlers.Clear();
            }

            disposedValue = true;
        }
    }

    ~PromptProcessor()
    {
        // Do not change this code. Put cleanup code in 'Dispose(bool disposing)' method
        Dispose(disposing: false);
    }

    public void Dispose()
    {
        // Do not change this code. Put cleanup code in 'Dispose(bool disposing)' method
        Dispose(disposing: true);
        GC.SuppressFinalize(this);
    }
}