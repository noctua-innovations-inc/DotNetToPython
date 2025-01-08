namespace GrpcMessaging.Infrastructure.Grpc;

/// <summary>
/// Represents configuration options for a gRPC service.
/// </summary>
public class GrpcOptions
{
    /// <summary>
    /// The name of the configuration section in appsettings.json or other configuration sources.
    /// </summary>
    public const string SectionName = "GrpcService";

    /// <summary>
    /// Gets or sets the scheme used for the gRPC service (e.g., "http" or "https").
    /// </summary>
    /// <remarks>
    /// The default value is "http".
    /// </remarks>
    public string Scheme { get; set; } = "http";

    /// <summary>
    /// Gets or sets the host of the gRPC service (e.g., "localhost" or an IP address).
    /// </summary>
    /// <remarks>
    /// The default value is an empty string, which means it must be set in configuration.
    /// </remarks>
    public string Host { get; set; } = string.Empty;

    /// <summary>
    /// Gets or sets the port number for the gRPC service.
    /// </summary>
    /// <remarks>
    /// The default value is 50051, which is a common port for gRPC services.
    /// </remarks>
    public int Port { get; set; } = 50051;

    /// <summary>
    /// Gets or sets the timeout duration (in milliseconds) for gRPC calls.
    /// </summary>
    /// <remarks>
    /// The default value is 0, which means no timeout is set by default.
    /// </remarks>
    public int Timeout { get; set; } = 0;

    /// <summary>
    /// Gets the full address of the gRPC service by combining the scheme, host, and port.
    /// </summary>
    /// <returns>
    /// A string representing the full address (e.g., "http://localhost:50051").
    /// </returns>
    /// <example>
    /// If Scheme is "http", Host is "localhost", and Port is 50051, the Address will be "http://localhost:50051".
    /// </example>
    public string Address => $"{Scheme}://{Host}:{Port}";
}