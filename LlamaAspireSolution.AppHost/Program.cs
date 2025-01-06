var builder = DistributedApplication.CreateBuilder(args);


// Add the Blazor Server front-end
var blazorFrontend = builder.AddProject<Projects.BlazorServerFrontend>("blazor-frontend");

builder
    .Build()
    .Run();