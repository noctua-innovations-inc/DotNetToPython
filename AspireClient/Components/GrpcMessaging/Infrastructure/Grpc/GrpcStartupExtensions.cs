using Grpc.Net.Client;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;

namespace GrpcMessaging.Infrastructure.Grpc;

/// <summary>
/// Provides extension methods for configuring gRPC services in a .NET application.
/// </summary>
/// <remarks>
/// gRPC (gRPC Remote Procedure Call) is a high-performance RPC framework that uses Protocol Buffers for serialization and HTTP/2 for transport.
/// Key features include:
/// <list type="bullet">
///   <item><description><strong>High Performance</strong>: Designed for low latency and high throughput communication.</description></item>
///   <item><description><strong>Protocol Buffers</strong>: Uses Protocol Buffers (protobuf) as its interface definition language (IDL) and message format.</description></item>
///   <item><description><strong>HTTP/2</strong>: Built on top of HTTP/2, which provides features like multiplexing, header compression, and bidirectional streaming.</description></item>
///   <item><description><strong>Cross-Language Support</strong>: Supports multiple programming languages, including C#, Java, Python, Go, JavaScript, and more.</description></item>
///   <item><description><strong>Strongly Typed API</strong>: Generates client and server code from .proto files, ensuring type safety and reducing boilerplate code.</description></item>
///   <item><description><strong>Streaming</strong>: Supports four types of communication patterns:
///     <list type="bullet">
///       <item><description>Unary (single request, single response)</description></item>
///       <item><description>Server streaming (single request, multiple responses)</description></item>
///       <item><description>Client streaming (multiple requests, single response)</description></item>
///       <item><description>Bidirectional streaming (multiple requests, multiple responses)</description></item>
///     </list>
///   </description></item>
/// </list>
/// </remarks>
public static class GrpcStartupExtensions
{
    /// <summary>
    /// Adds a gRPC channel to the service collection using configuration options.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to add the gRPC channel to.</param>
    /// <param name="configuration">The <see cref="IConfiguration"/> containing gRPC options.</param>
    /// <returns>The <see cref="IServiceCollection"/> for chaining.</returns>
    /// <remarks>
    /// This method configures a gRPC channel using the <see cref="GrpcOptions"/> specified in the configuration.
    /// It also sets a custom timeout for the underlying <see cref="HttpClient"/>.
    /// </remarks>
    /// <example>
    /// <code>
    /// var services = new ServiceCollection();
    /// var configuration = new ConfigurationBuilder().AddJsonFile("appsettings.json").Build();
    /// services.AddGrpcChannel(configuration);
    /// </code>
    /// </example>
    public static IServiceCollection AddGrpcChannel(this IServiceCollection services, IConfiguration configuration)
    {
        var grpcOptions = new GrpcOptions();
        configuration.GetSection(GrpcOptions.SectionName).Bind(grpcOptions);

        // Create the GrpcChannel with the custom HttpClient
        var channel = GrpcChannel.ForAddress(grpcOptions.Address, new GrpcChannelOptions
        {
            // Create the HttpClient with a custom timeout
            HttpClient = new HttpClient
            {
                // Set a longer timeout for the HttpClient.
                // The need to do this suggests that communications would be better served using a Message Queue Pattern.
                Timeout = TimeSpan.FromSeconds(grpcOptions.Timeout)
            }
        });

        // Register the gRPC client in the DI container
        services.AddSingleton(channel);

        return services;
    }

    /// <summary>
    /// Registers a gRPC client in the service collection and binds it to the specified channel.
    /// </summary>
    /// <typeparam name="TClient">The type of the gRPC client, which must inherit from <see cref="global::Grpc.Core.ClientBase{TClient}"/>.</typeparam>
    /// <param name="services">The <see cref="IServiceCollection"/> to add the gRPC client to.</param>
    /// <returns>The <see cref="IServiceCollection"/> for chaining.</returns>
    /// <remarks>
    /// This method registers a transient gRPC client in the dependency injection container.
    /// The client is instantiated using the provided <see cref="GrpcChannel"/>.
    /// </remarks>
    /// <example>
    /// <code>
    /// var services = new ServiceCollection();
    /// services.AddGrpcProtocolToChannel&lt;Greeter.GreeterClient&gt;();
    /// </code>
    /// </example>
    public static IServiceCollection AddGrpcProtocolToChannel<TClient>(this IServiceCollection services)
        where TClient : global::Grpc.Core.ClientBase<TClient>
    {
        // Register a transient service for the gRPC client in the dependency injection container.
        // A transient service means a new instance is created each time it is requested.
        services.AddTransient(provider =>
        {
            // Retrieve the GrpcChannel instance from the dependency injection container.
            // The GrpcChannel is typically registered as a singleton in the DI container.
            var channel = provider.GetRequiredService<GrpcChannel>();

            // Create an instance of the gRPC client (TClient) using ActivatorUtilities.
            // ActivatorUtilities.CreateInstance allows dependency injection to resolve any additional
            // dependencies required by the gRPC client's constructor, in addition to the GrpcChannel.
            return ActivatorUtilities.CreateInstance<TClient>(provider, channel);
        });

        // Return the IServiceCollection for method chaining.
        return services;
    }
}