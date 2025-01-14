#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
rag_prompt_processor.py

RAG (Retrieval-Augmented Generation) Prompt Processor

This script processes user queries by combining the capabilities of a large language model (LLM)
and a search-based summarizer (SearXNG) to generate accurate and contextually relevant responses.
It listens for incoming messages from a RabbitMQ queue, processes the queries, and sends back
responses using a reply-to queue.

Key Features:
- Uses the LlamaService to generate responses from a large language model.
- Integrates with SearXNG to retrieve and summarize relevant information from the web.
- Communicates with a RabbitMQ message broker for asynchronous query processing.

Dependencies:
- pika: For RabbitMQ communication.
- llama_service: Custom service for interacting with the Llama model.
- searxng_summarizer: Custom module for summarizing search results from SearXNG.

Configuration:
- RabbitMQ connection details are configured via environment variables or default values.
- The SearXNG instance URL is hardcoded but can be modified as needed.

Usage:
1. Ensure RabbitMQ is running and accessible.
2. Set up the LlamaService and SearXNG summarizer.
3. Run this script to start the consumer:
   python rag_prompt_processor.py
4. Send queries to the RabbitMQ queue frontend_to_backend with a reply_to property.

Example:

 - A query is sent to the queue.
 - The script processes the query using the Llama model and/or SearXNG summarizer.
 - The response is sent back to the reply_to queue.

Author: Christopher Zielinski
Date: 2025-01-13
Version: 1.0

License:
    MIT License

Disclaimer:
    This script is provided "as-is" without any warranties. Use at your own risk.

"""

from datetime import datetime
import os
import logging
import sys
import pika
from llama_service import LlamaService
from searxng_summarizer import SearxngSummarizer

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Configuration
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")             # RabbitMQ server host
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", 5672))               # RabbitMQ server port
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "dev_user")              # RabbitMQ username
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "dev_password")  # RabbitMQ password
FRONTEND_TO_BACKEND_QUEUE = "frontend_to_backend"

# Initialize LlamaService
llama_service = LlamaService()


def process_prompt(query: str) -> str:
    """
    Process a user query by generating a response using the Llama model and/or SearXNG summarizer.

    Args:
        query (str): The user's query.

    Returns:
        str: The generated response.
    """
    logging.info(f"Processing query: {query}")

    try:
        # First, attempt to answer the query without additional context
        llama_reply = llama_service.submit_query_without_context_to_llama(query)

        # Check if the query was likely answered
        if llama_service.was_query_likely_answered(query, llama_reply):
            return llama_reply
        else:
            # If not, use SearXNG to gather additional context
            searxng_instance_url = "http://127.0.0.1:8080/"
            summarizer = SearxngSummarizer(searxng_instance_url)
            search_result = (
                f"For reference, today is {datetime.now().strftime('%A, %d %B %Y')}, "
                "but the following information could be older...\n\n"
                f"{summarizer.process_query(query)}"
            )

            # Submit the query with the gathered context
            return llama_service.submit_query_with_context_to_llama(query, context=search_result)
    except Exception as e:
        logging.error(f"Error processing query: {e}")
        return ""


def setup_rabbitmq_connection():
    """
    Set up and return a RabbitMQ connection and channel.

    Returns:
        tuple: A tuple containing the RabbitMQ connection and channel.
    """
    try:
        credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=RABBITMQ_HOST,
                port=RABBITMQ_PORT,
                credentials=credentials,
            )
        )
        channel = connection.channel()
        channel.queue_declare(queue=FRONTEND_TO_BACKEND_QUEUE, durable=False)
        logging.info("RabbitMQ connection and dedicated queue set up successfully.")
        return connection, channel
    except pika.exceptions.AMQPError as e:
        logging.error(f"Failed to set up RabbitMQ connection: {e}")
        sys.exit(1)


def callback(ch, method, properties, body):
    """
    Callback function to process incoming messages from RabbitMQ.

    Args:
        ch: The RabbitMQ channel.
        method: The method frame.
        properties: The message properties.
        body: The message body.
    """
    try:
        prompt = body.decode("utf-8")
        reply = process_prompt(prompt)

        # Use the ReplyTo property from the incoming message to send the reply
        if properties.reply_to:
            ch.basic_publish(
                exchange="",
                routing_key=properties.reply_to,                # Use the ReplyTo queue
                body=reply.encode("utf-8"),
                properties=pika.BasicProperties(
                    correlation_id=properties.correlation_id,   # Include the correlation ID
                    delivery_mode=1,                            # Make messages transient
                ),
            )
            logging.info(f"Processed and replied to prompt: {prompt}")
        else:
            logging.error("No ReplyTo property found in the incoming message.")
    except Exception as e:
        logging.error(f"Error processing message: {e}")


def start_consumer():
    """
    Start the RabbitMQ consumer to listen for incoming messages.
    """
    connection, channel = setup_rabbitmq_connection()
    try:
        channel.basic_consume(
            queue=FRONTEND_TO_BACKEND_QUEUE,
            on_message_callback=callback,
            auto_ack=True,
        )
        logging.info("Waiting for messages. To exit, press CTRL+C")
        channel.start_consuming()
    except KeyboardInterrupt:
        logging.info("Consumer interrupted by user. Shutting down gracefully...")
    except Exception as e:
        logging.error(f"Error in consumer: {e}")
    finally:
        if connection and connection.is_open:
            connection.close()
            logging.info("RabbitMQ connection closed.")


if __name__ == "__main__":
    start_consumer()