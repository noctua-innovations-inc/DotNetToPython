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

    [Inject]
    public required IConnection MqConnection { get; set; }

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
        var updateView = () =>
        {
            // Notify Blazor UI of property value changes.
            PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));
            StateHasChanged();
        };

        // Ensure execution on UI thread
        if (SynchronizationContext.Current != null)
        {
            updateView();
        }
        else
        {
            Task.Run(async () => await InvokeAsync(updateView));
        }
    }

    #endregion

    #region --[ Overrides ]--

    protected override async Task OnAfterRenderAsync(bool firstRender)
    {
        if (firstRender)
        {
            await ConfigureReceiver();
        }
        await base.OnAfterRenderAsync(firstRender);
    }

    #endregion

    private async Task GenerateText()
    {
        if (string.IsNullOrWhiteSpace(Prompt) || IsProcessing)
            return;

        IsProcessing = true;
        /*
         *GHOSTED CODE: This gRPC implementation is no longer in use but is kept for reference.
         * It was replaced with a message queue pattern due to timeout issues and the need for
         * better support for Retrieval-Augmented Generation (RAG) workflows.
         *
         * Original gRPC implementation:
         *//*
        try
        {
            var reply = await LlamaServiceClient.GenerateTextAsync(new TextRequest { Prompt = Prompt });
            GeneratedText = reply.GeneratedText;
        }
        finally
        {
            IsProcessing = false;
        }
        await Task.CompletedTask;
        */
        await SendRequest();
    }


    private async Task SendRequest()
    {
        using var channel = await MqConnection.CreateChannelAsync();

        await channel.QueueDeclareAsync(
            queue: "frontend_to_backend",
            durable: false,
            exclusive: false,
            autoDelete: false,
            arguments: null);

        ReadOnlyMemory<byte> body = Encoding.UTF8.GetBytes(Prompt);

        await channel.BasicPublishAsync(
            exchange: "",
            routingKey: "frontend_to_backend",
            mandatory: false,
            body: body);
    }

    private async Task ConfigureReceiver()
    {
        /* using */ var channel = await MqConnection.CreateChannelAsync();

        await channel.QueueDeclareAsync(
            queue: "backend_to_frontend",
            durable: false,
            exclusive: false,
            autoDelete: false,
            arguments: null);

        var consumer = new AsyncEventingBasicConsumer(channel);

        consumer.ReceivedAsync += (model, ea) =>
        {
            var body = ea.Body.ToArray();
            var message = Encoding.UTF8.GetString(body);

            GeneratedText = message;
            IsProcessing = false;

            return Task.CompletedTask;
        };

        await channel.BasicConsumeAsync(
            queue: "backend_to_frontend",
            autoAck: true,
            consumer: consumer);
    }
}
