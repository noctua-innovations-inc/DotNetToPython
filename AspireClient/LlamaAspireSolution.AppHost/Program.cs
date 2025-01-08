
var builder = DistributedApplication.CreateBuilder(args);

// Add RabbitMQ container
var rabbitMq = builder
    .AddRabbitMQ("ai-queue")
    .WithEndpoint("amqp", endpoint =>
    {
        // Specify the external AMQP port (default is 5672)
        endpoint.Port = 5672;
        // Specify the internal AMQP port (default is 5672 inside the container)
        endpoint.TargetPort = 5672;
    })
    .WithManagementPlugin()
    .WithEnvironment("RABBITMQ_DEFAULT_USER", "dev_user")  // Custom username
    .WithEnvironment("RABBITMQ_DEFAULT_PASS", "dev_password");  // Custom password

// Add the Blazor Server front-end
var blazorFrontend = builder.AddProject<Projects.BlazorServerFrontend>("blazor-frontend")
    .WithReference(rabbitMq);

builder
    .Build()
    .Run();