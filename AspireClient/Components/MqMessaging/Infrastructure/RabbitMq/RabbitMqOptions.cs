namespace MqMessaging.Infrastructure.RabbitMq;

public class RabbitMqOptions
{
    public const string RabbitMqSectionName = "RabbitMq";

    public string HostName { get; set; } = string.Empty;
    public string HostPort { get; set; } = string.Empty;

    // TODO: Move to Key Vault
    public string User { get; set; } = string.Empty;
    public string Password { get; set; } = string.Empty;
}