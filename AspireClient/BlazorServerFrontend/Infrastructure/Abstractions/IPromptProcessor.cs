using RabbitMQ.Client.Events;

namespace BlazorServerFrontend.Infrastructure.Abstractions;

public interface IPromptProcessor
{
    void Dispose();
    Task RegisterEventHandlerAsync(AsyncEventHandler<BasicDeliverEventArgs> asyncEventHandler, string queue = "backend_to_frontend");
    Task SendRequestAsync(string prompt, string queue = "frontend_to_backend");
    Task UnRegisterEventHandlerAsync(AsyncEventHandler<BasicDeliverEventArgs> asyncEventHandler, string queue = "backend_to_frontend");
}