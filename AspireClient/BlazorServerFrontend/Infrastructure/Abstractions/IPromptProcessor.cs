using RabbitMQ.Client.Events;

namespace BlazorServerFrontend.Infrastructure.Abstractions;

/// <summary>
/// Defines the contract for a processor that handles prompts and communicates with a message queue.
/// </summary>
public interface IPromptProcessor
{
    /// <summary>
    /// Releases all resources used by the <see cref="IPromptProcessor"/>.
    /// </summary>
    void Dispose();

    /// <summary>
    /// Registers an asynchronous event handler to process messages received from the message queue.
    /// </summary>
    /// <param name="asyncEventHandler">The asynchronous event handler to be registered.</param>
    /// <returns>A <see cref="Task"/> representing the asynchronous operation.</returns>
    Task RegisterEventHandlerAsync(AsyncEventHandler<BasicDeliverEventArgs> asyncEventHandler);

    /// <summary>
    /// Sends a prompt request to the specified message queue.
    /// </summary>
    /// <param name="prompt">The prompt to be sent.</param>
    /// <param name="queue">The name of the message queue to which the prompt is sent. Default is "frontend_to_backend".</param>
    /// <returns>A <see cref="Task"/> representing the asynchronous operation.</returns>
    Task SendRequestAsync(string prompt, string queue = "frontend_to_backend");

    /// <summary>
    /// Unregisters an asynchronous event handler from processing messages received from the message queue.
    /// </summary>
    /// <param name="asyncEventHandler">The asynchronous event handler to be unregistered.</param>
    /// <returns>A <see cref="Task"/> representing the asynchronous operation.</returns>
    Task UnRegisterEventHandlerAsync(AsyncEventHandler<BasicDeliverEventArgs> asyncEventHandler);
}