using RabbitMQ.Client;

namespace MqMessaging.Infrastructure.RabbitMq;

public interface IRabbitMqConnection
{
    IConnection Connection { get; }
}