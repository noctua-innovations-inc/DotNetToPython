
using Grpc.Net.Client;

var builder = WebApplication.CreateBuilder(args);

// Add service defaults & Aspire components.
builder.AddServiceDefaults();

// Add services to the container.
builder.Services.AddRazorPages();
builder.Services.AddServerSideBlazor();

// Create the HttpClient with a custom timeout
var httpClient = new HttpClient
{
    Timeout = TimeSpan.FromMinutes(5) // Set a longer timeout for the HttpClient
};

// Create the GrpcChannel with the custom HttpClient
var channel = GrpcChannel.ForAddress(builder.Configuration["GrpcService:Address"]!, new GrpcChannelOptions
{
    HttpClient = httpClient
});

// Register the gRPC client in the DI container
builder.Services.AddSingleton(channel);
builder.Services.AddTransient(provider => new LlamaService.LlamaServiceClient(provider.GetRequiredService<GrpcChannel>()));

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
