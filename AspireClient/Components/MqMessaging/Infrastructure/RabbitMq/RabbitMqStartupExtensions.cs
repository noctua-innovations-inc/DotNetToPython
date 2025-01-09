using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Polly;
using Polly.Retry;
using RabbitMQ.Client;

namespace MqMessaging.Infrastructure.RabbitMq;

public static class RabbitMqStartupExtensions
{
    public static async Task<IServiceCollection> AddRabbitMqEventBus(this IServiceCollection services, IConfiguration configuration, ILogger logger)
    {
        var rabbitMqOptions = new RabbitMqConnectionOptions();
        configuration.GetSection(RabbitMqConnectionOptions.SectionName).Bind(rabbitMqOptions);

        var factory = new ConnectionFactory()
        {
            HostName = rabbitMqOptions.Host,
            Port = rabbitMqOptions.Port,
            UserName = rabbitMqOptions.UserName,
            Password = rabbitMqOptions.Password,
            AutomaticRecoveryEnabled = true,
            NetworkRecoveryInterval = TimeSpan.FromSeconds(10)
        };

        // Define a retry policy with exponential backoff
        var retryPolicy = CreateRetryPolicy(logger);

        // Use the retry policy to attempt connection creation
        var connection = await retryPolicy.ExecuteAsync(async () =>
        {
            try
            {
                return await factory.CreateConnectionAsync();
            }
            catch (Exception ex)
            {
                // Log the exception if needed
                logger.LogCritical("Failed to create RabbitMQ connection: {message}", ex.Message);
                throw; // Re-throw to let Polly handle the retry
            }
        });

        // Using a singleton for the connection is a common practice to ensure that only one
        // connection is created and reused across the application.  This reduces overhead
        // and avoids connection churn.
        services.AddSingleton(connection);

        return services;
    }

    private static AsyncRetryPolicy<IConnection> CreateRetryPolicy(ILogger logger)
    {
        return Policy<IConnection>
            .Handle<Exception>() // Handle all exceptions (or specify specific ones)
            .WaitAndRetryAsync(
                retryCount: 5, // Maximum number of retries
                sleepDurationProvider: retryAttempt => TimeSpan.FromSeconds(Math.Pow(2, retryAttempt)), // Exponential backoff
                onRetry: (exception, delay, retryCount, context) =>
                {
                    // Log the retry attempt
                    logger.LogError("Retry {retryCount} of connecting to RabbitMQ. Waiting {delay} before next attempt...", retryCount, delay);
                });
    }
}