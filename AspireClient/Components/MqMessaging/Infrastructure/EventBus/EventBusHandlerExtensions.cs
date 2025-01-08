using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Configuration;
using MqMessaging.Infrastructure.EventBus.Abstractions;

namespace MqMessaging.Infrastructure.EventBus;

public static class EventBusHandlerExtensions
{
    public static IServiceCollection AddEventHandler<TEvent, THandler>(this IServiceCollection serviceCollection)
        where TEvent : Event
        where THandler : class, IEventHandler<TEvent>
    {
        serviceCollection.AddKeyedTransient<IEventHandler, THandler>(typeof(TEvent));

        serviceCollection.Configure<EventHandlerRegistration>(o =>
        {
            o.EventTypes[typeof(TEvent).Name] = typeof(TEvent);
        });

        return serviceCollection;
    }
}