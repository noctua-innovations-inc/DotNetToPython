using Microsoft.AspNetCore.Components;
using Microsoft.AspNetCore.Components.Web;
using Microsoft.JSInterop;
using System.ComponentModel;

namespace BlazorServerFrontend.Pages;

public partial class Index
{
    private string Prompt { get; set; } = string.Empty;

    public event PropertyChangedEventHandler PropertyChanged;

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

    private void OnPropertyChanged(string propertyName)
    {
        PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));
        StateHasChanged(); // Notify Blazor of the change
    }


    [Inject]
    public required LlamaService.LlamaServiceClient LlamaServiceClient { get; set; }


    private async Task GenerateText()
    {
        if (string.IsNullOrWhiteSpace(Prompt) || IsProcessing)
            return;

        IsProcessing = true;
        try
        {
            var reply = await LlamaServiceClient.GenerateTextAsync(new TextRequest { Prompt = Prompt });
            GeneratedText = reply.GeneratedText;
        }
        finally
        {
            IsProcessing = false;
        }
    }

}
