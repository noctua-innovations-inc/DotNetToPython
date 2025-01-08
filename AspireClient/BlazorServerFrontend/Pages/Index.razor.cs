using BlazorServerFrontend.Infrastructure.Abstractions;
using Microsoft.AspNetCore.Components;
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
    public required IPromptProcessor PromptProcessor { get; set; }

    #endregion --[ Injection ]--

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

    #endregion --[ Properties ]--

    #region --[ Overrides ]--

    protected override async Task OnAfterRenderAsync(bool firstRender)
    {
        if (firstRender)
        {
            await PromptProcessor.RegisterEventHandlerAsync(DataReceivedHandler);
        }
        await base.OnAfterRenderAsync(firstRender);
    }

    #endregion --[ Overrides ]--

    private async Task SubmitPrompt()
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
        await PromptProcessor.SendRequestAsync(Prompt);
    }

    private Task DataReceivedHandler(object channel, BasicDeliverEventArgs @event)
    {
        var body = @event.Body.ToArray();
        var message = Encoding.UTF8.GetString(body);

        GeneratedText = message;
        IsProcessing = false;

        return Task.CompletedTask;
    }
}