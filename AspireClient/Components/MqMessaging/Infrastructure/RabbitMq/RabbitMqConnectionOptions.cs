namespace MqMessaging.Infrastructure.RabbitMq;

public class RabbitMqConnectionOptions
{
    public const string SectionName = "RabbitMqConnection";

    public string Host { get; set; } = string.Empty;
    public int Port { get; set; } = 5672;

    public string UserName { get; set; } = string.Empty;
    public string Password { get; set; } = string.Empty;
}