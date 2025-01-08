using Microsoft.AspNetCore.Components;
using Microsoft.AspNetCore.Components.Web;
using Microsoft.AspNetCore.Connections;
using Microsoft.JSInterop;
using RabbitMQ.Client;
using RabbitMQ.Client.Events;
using System.ComponentModel;
using System.Text;

namespace BlazorServerFrontend.Pages;

public partial class Index
{
    #region --[ Injection ]--

    /*
     *GHOSTED CODE: This gRPC implementation is no longer in use but is kept for reference.
     * It was replaced with a message queue pattern due to timeout issues and the need for
     * better support for Retrieval-Augmented Generation (RAG) workflows.
     *
     * Original gRPC implementation:
     *//*
    [Inject]
    public required LlamaService.LlamaServiceClient LlamaServiceClient { get; set; }
    */

    #endregion

    #region --[ Properties ]-- 

    private string Prompt { get; set; } = string.Empty;

    private string _generatedText = string.Empty;
    public string GeneratedText
    {
        get => _generatedText;
        set
        {
            if (_generatedText != value)
            {
                _generatedText = value;
                OnPropertyChanged(nameof(GeneratedText));
            }
        }
    }

    private bool _isProcessing = false;
    public bool IsProcessing
    {
        get => _isProcessing;
        set
        {
            if (_isProcessing != value)
            {
                _isProcessing = value;
                OnPropertyChanged(nameof(IsProcessing));
            }
        }
    }

    public event PropertyChangedEventHandler PropertyChanged;
    private void OnPropertyChanged(string propertyName)
    {
        // Notify Blazor UI of the change
        Task.Run(async () =>
        {
            // Ensure execution on UI thread
            await InvokeAsync(() =>
            {
                PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));
                StateHasChanged();
            });
        });
    }

    #endregion

    #region --[ Overrides ]--

    protected override async Task OnAfterRenderAsync(bool firstRender)
    {
        if (firstRender)
        {
            ConfigureReceiver();
        }
        await base.OnAfterRenderAsync(firstRender);
    }

    #endregion

    private async Task GenerateText()
    {
        if (string.IsNullOrWhiteSpace(Prompt) || IsProcessing)
            return;

        IsProcessing = true;
        try
        {
            /*
             *GHOSTED CODE: This gRPC implementation is no longer in use but is kept for reference.
             * It was replaced with a message queue pattern due to timeout issues and the need for
             * better support for Retrieval-Augmented Generation (RAG) workflows.
             *
             * Original gRPC implementation:
             *//*
            var reply = await LlamaServiceClient.GenerateTextAsync(new TextRequest { Prompt = Prompt });
            GeneratedText = reply.GeneratedText;
            */

            SendRequest();
        }
        finally
        {
            IsProcessing = false;
        }
        await Task.CompletedTask;
    }


    private void SendRequest()
    {
        var factory = new ConnectionFactory()
        {
            HostName = "localhost",
            Port = 5672,
            UserName = "dev_user",
            Password = "dev_password"
        };

        using var connection = factory.CreateConnection();

        using var channel = connection.CreateModel();

        channel.QueueDeclare(
            queue: "frontend_to_backend",
            durable: false,
            exclusive: false,
            autoDelete: false,
            arguments: null);

        var body = Encoding.UTF8.GetBytes(Prompt);

        channel.BasicPublish(
            exchange: "",
            routingKey: "frontend_to_backend",
            basicProperties: null,
            body: body);
    }

    private void ConfigureReceiver()
    {
        var factory = new ConnectionFactory()
        {
            HostName = "localhost",
            Port = 5672,
            UserName = "dev_user",
            Password = "dev_password"
        };

        /* using */
            var connection = factory.CreateConnection();
        /* using */ var channel = connection.CreateModel();

        channel.QueueDeclare(
            queue: "backend_to_frontend",
            durable: false,
            exclusive: false,
            autoDelete: false,
            arguments: null);

        var consumer = new EventingBasicConsumer(channel);
        consumer.Received += (model, ea) =>
        {
            var body = ea.Body.ToArray();
            var message = Encoding.UTF8.GetString(body);

            GeneratedText = message;
        };

        channel.BasicConsume(
            queue: "backend_to_frontend",
            autoAck: true,
            consumer: consumer);
    }
}
