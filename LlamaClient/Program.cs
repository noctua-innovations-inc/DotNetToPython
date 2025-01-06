using Grpc.Net.Client;
using System.Text;

internal class Program
{
    private static async Task Main(string[] args)
    {
        // Create a gRPC channel and client
        using var channel = GrpcChannel.ForAddress("http://localhost:50051");
        var client = new LlamaService.LlamaServiceClient(channel);

        // Set up a cancellation token for Ctrl+C
        var cts = new CancellationTokenSource();
        Console.CancelKeyPress += (sender, eventArgs) =>
        {
            Console.WriteLine("\nExiting...");
            cts.Cancel();
            eventArgs.Cancel = true; // Prevent the process from terminating immediately
        };

        Console.WriteLine("gRPC client started. Enter a prompt (Ctrl+C to exit):");

        // Loop to continuously prompt for user input
        while (!cts.Token.IsCancellationRequested)
        {
            try
            {
                // Read user input
                Console.Write("> ");
                var prompt = Console.ReadLine();

                if (string.IsNullOrWhiteSpace(prompt))
                {
                    Console.WriteLine("Please enter a valid prompt.");
                    continue;
                }

                // Send the prompt to the gRPC server
                var reply = await client.GenerateTextAsync(new TextRequest { Prompt = prompt });

                // Output the server's reply with formatted wrapping
                Console.WriteLine("Server reply:");
                FormatAndPrintText(reply.GeneratedText, 120);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error: {ex.Message}");
            }
        }

        Console.WriteLine("Client stopped.");
    }

    /// <summary>
    /// Formats and prints text so that each line does not exceed the specified maximum length.
    /// Ensures that words and punctuation are not split across lines.
    /// </summary>
    /// <param name="text">The text to format and print.</param>
    /// <param name="maxLineLength">The maximum length of each line.</param>
    private static void FormatAndPrintText(string text, int maxLineLength)
    {
        var words = text.Split(' '); // Split the text into words
        var currentLine = new StringBuilder();

        foreach (var word in words)
        {
            // Check if adding the next word would exceed the max line length
            if (currentLine.Length + word.Length + 1 > maxLineLength)
            {
                // Print the current line and start a new one
                Console.WriteLine(currentLine.ToString().TrimEnd());
                currentLine.Clear();
            }

            // Add the word to the current line
            currentLine.Append(word + " ");
        }

        // Print any remaining text in the current line
        if (currentLine.Length > 0)
        {
            Console.WriteLine(currentLine.ToString().TrimEnd());
        }
    }
}