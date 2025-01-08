namespace MqMessaging.Infrastructure.EventBus.Abstractions;

public class EventBusOptions
{
    public const string EventBusSectionName = "EventBus";
    public string QueueName { get; set; } = string.Empty;
}