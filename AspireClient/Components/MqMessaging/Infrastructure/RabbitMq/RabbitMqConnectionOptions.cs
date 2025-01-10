namespace MqMessaging.Infrastructure.RabbitMq;

/// <summary>
/// Represents the configuration options for establishing a connection to RabbitMQ.
/// </summary>
/// <remarks>
/// This class is used to bind RabbitMQ connection settings from the application configuration (e.g., appsettings.json).
/// </remarks>
public class RabbitMqConnectionOptions
{
    /// <summary>
    /// The name of the configuration section where RabbitMQ connection settings are stored.
    /// </summary>
    public const string SectionName = "RabbitMqConnection";

    /// <summary>
    /// Gets or sets the host name or IP address of the RabbitMQ server.
    /// </summary>
    /// <value>
    /// The default value is an empty string.
    /// </value>
    public string Host { get; set; } = string.Empty;

    /// <summary>
    /// Gets or sets the port number of the RabbitMQ server.
    /// </summary>
    /// <value>
    /// The default value is 5672, which is the default port for RabbitMQ.
    /// </value>
    public int Port { get; set; } = 5672;

    /// <summary>
    /// Gets or sets the network recovery interval (in seconds) for the RabbitMQ connection.
    /// </summary>
    /// <value>
    /// The default value is 10 seconds.
    /// </value>
    public int NetworkRecoveryInterval { get; set; } = 10;

    /// <summary>
    /// Gets or sets the username for authenticating with the RabbitMQ server.
    /// </summary>
    /// <value>
    /// The default value is an empty string.
    /// </value>
    public string UserName { get; set; } = string.Empty;

    /// <summary>
    /// Gets or sets the password for authenticating with the RabbitMQ server.
    /// </summary>
    /// <value>
    /// The default value is an empty string.
    /// </value>
    public string Password { get; set; } = string.Empty;
}