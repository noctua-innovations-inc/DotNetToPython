using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using MqMessaging.Infrastructure.EventBus.Abstractions;
using RabbitMQ.Client;

namespace MqMessaging.Infrastructure.RabbitMq;

public static class RabbitMqStartupExtensions
{
    public static async Task<IServiceCollection> AddRabbitMqEventBus(this IServiceCollection services, IConfigurationManager configuration)
    {
        var rabbitMqOptions = new RabbitMqConnectionOptions();
        configuration.GetSection(RabbitMqConnectionOptions.SectionName).Bind(rabbitMqOptions);

        // TODO: Remove this hack.  Time is needed for the queue to be in a state that accepts connections.
        Thread.Sleep(6000);

        var factory = new ConnectionFactory()
        {
            HostName = rabbitMqOptions.Host,
            Port = rabbitMqOptions.Port,
            UserName = rabbitMqOptions.UserName,
            Password = rabbitMqOptions.Password
        };

        // Blocking the thread is acceptable during application startup but should be avoided in other contexts.
        var connection = await factory.CreateConnectionAsync();
        services.AddSingleton(connection);

        return services;
    }

    //public static IServiceCollection AddRabbitMqEventPublisher(this IServiceCollection services)
    //{
    //    services.AddScoped<IEventBus, RabbitMqEventBus>();
    //    return services;
    //}

    //public static IServiceCollection AddRabbitMqSubscriberService(this IServiceCollection services, IConfigurationManager configuration)
    //{
    //    services.Configure<EventBusOptions>(configuration.GetSection(EventBusOptions.EventBusSectionName));
    //    services.AddHostedService<RabbitMqHostedService>();
    //    return services;
    //}
}