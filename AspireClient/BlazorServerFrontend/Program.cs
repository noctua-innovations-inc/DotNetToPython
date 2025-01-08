/*
 *GHOSTED CODE: This gRPC implementation is no longer in use but is kept for reference.
 * It was replaced with a message queue pattern due to timeout issues and the need for
 * better support for Retrieval-Augmented Generation (RAG) workflows.
 *
 * Original gRPC implementation:
 *//*
using Grpc.Net.Client;
using GrpcMessaging.Infrastructure.Grpc;
 */

using MqMessaging.Infrastructure.RabbitMq;

var builder = WebApplication.CreateBuilder(args);

// Add service defaults & Aspire components.
builder.AddServiceDefaults();

// Add services to the container.
builder.Services.AddRazorPages();
builder.Services.AddServerSideBlazor();

/*
 * Initial .NET-to-Python communications were implemented using gRPC. However, the need
 * to increase the default communication timeout and the desire to implement Retrieval-Augmented
 * Generation (RAG) suggest that communications would be better served using a Message Queue Pattern.
 * 
 * Key Considerations:
 * - gRPC's default timeout may not be sufficient for long-running operations.
 * - Message queues provide better support for asynchronous, decoupled communication.
 * - RAG workflows often involve batch processing and event-driven architectures, which align well with message queues.
 *
 * GHOSTED CODE: This gRPC implementation is no longer in use but is kept for reference.
 * It was replaced with a message queue pattern due to timeout issues and the need for
 * better support for Retrieval-Augmented Generation (RAG) workflows.
 *
 * Original gRPC implementation:
 *//*
builder.Services.AddGrpcChannel(builder.Configuration);
builder.Services.AddGrpcProtocolToChannel<LlamaService.LlamaServiceClient>();
 */

await builder.Services.AddRabbitMqEventBus(builder.Configuration);

var app = builder.Build();

// Configure the HTTP request pipeline.
if (!app.Environment.IsDevelopment())
{
    app.UseExceptionHandler("/Error");
    // The default HSTS value is 30 days. You may want to change this for production scenarios, see https://aka.ms/aspnetcore-hsts.
    app.UseHsts();
}

app.UseHttpsRedirection();
app.UseStaticFiles();
app.UseRouting();

app.MapBlazorHub();
app.MapFallbackToPage("/_Host");

app.MapDefaultEndpoints();

app.Run();
