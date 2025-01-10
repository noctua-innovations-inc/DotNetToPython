import pika
import logging
import sys
import os
import requests
from bs4 import BeautifulSoup
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Configuration
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")             # RabbitMQ server host
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", 5672))               # RabbitMQ server port
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "dev_user")              # RabbitMQ username
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "dev_password")  # RabbitMQ password
FRONTEND_TO_BACKEND_QUEUE = "frontend_to_backend"
SEARXNG_INSTANCE = "http://127.0.0.1:8080/"                         # Replace with your SearXNG instance URL
MAX_SEARCH_RESULTS = 16                                             # Maximum number of search results to process

logging.info(f"RabbitMQ Host: {RABBITMQ_HOST}")

class LlamaService:
    def __init__(self):
        # Load the pre-trained Llama 3.2 3B Instruct model using Hugging Face's AutoModelForCausalLM.
        # This model is designed for causal language modeling tasks (e.g., text generation).
        self.model = AutoModelForCausalLM.from_pretrained(
            "meta-llama/Llama-3.2-3B-Instruct",             # Model identifier on Hugging Face Hub
            device_map="auto",                              # Automatically distribute the model across available GPUs
            torch_dtype=torch.float16                       # Use half-precision (16-bit floating point) for better performance
        )

        # Load the tokenizer associated with the Llama 3.2 3B Instruct model.
        # The tokenizer converts text into tokens (e.g., words or subwords) that the model can process.
        self.tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-3.2-3B-Instruct")

    def generate_text(self, prompt, context=""):
        """
        Generate text using the Llama 3.2 3B model.
        """
        # Combine the context and prompt for the model
        input_text = f"Context:\n{context}\n\nQuestion: {prompt}\nAnswer:"
        inputs = self.tokenizer(
            input_text,                                     # The input text to tokenize
            return_tensors="pt",                            # Return PyTorch tensors (required for the model)
            truncation=True,                                # Enable truncation if the input exceeds the max_length
            max_length=8000,                                # Set the maximum number of tokens for the input
            truncation_strategy="longest_first"             # Truncate the longest part of the input if necessary
        ).to("cuda")                                        # Move the tokenized inputs to the GPU for faster processing

        # Generate text using the model.
        # The model takes the tokenized input and produces a sequence of tokens as output.
        outputs = self.model.generate(
            inputs["input_ids"],                            # Token IDs of the input prompt
            attention_mask=inputs["attention_mask"],        # Attention mask to indicate which tokens are actual input
            max_new_tokens=16000,                           # Maximum number of new tokens to generate (excluding the input tokens)
            pad_token_id=self.tokenizer.eos_token_id,       # Use the end-of-sequence (EOS) token as the padding token
            no_repeat_ngram_size=2,                         # Prevent the model from repeating 2-grams (pairs of words)
            num_beams=5,                                    # Use beam search with 5 beams to explore multiple candidate sequences
            early_stopping=True                             # Stop generation early if all beam candidates reach the EOS token
        )

        # Decode the generated token IDs back into human-readable text.
        # The `skip_special_tokens=True` argument removes special tokens like [EOS] from the output.
        generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

        answer_keyword = "Answer:"

        # Remove the input prompt from the generated text (if present).
        # This ensures that only the newly generated text is returned.
        if generated_text.startswith(input_text):
            generated_text = generated_text[len(input_text):].strip()
        else:
            if answer_keyword in generated_text:
                generated_text = generated_text.split(answer_keyword, 1)[1]  # Get the part after "Answer:"

        return generated_text


def fetch_search_results(query, max_results=MAX_SEARCH_RESULTS):
    """
    Fetch search results from SearXNG.
    """
    try:
        params = {
            "q": query,
            "format": "json",
            "language": "en",
            "safesearch": 1,
            "count": max_results
        }
        response = requests.get(f"{SEARXNG_INSTANCE}/search", params=params)
        response.raise_for_status()
        results = response.json().get("results", [])
        return results[:max_results]
    except Exception as e:
        logging.error(f"Error fetching search results: {e}")
        return []


def extract_webpage_content(url):
    """
    Extract text content from a webpage.
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        # Extract text from the webpage
        text = soup.get_text(separator="\n", strip=True)
        return text
    except Exception as e:
        logging.error(f"Error extracting content from {url}: {e}")
        return ""


def process_prompt(prompt):
    """
    Process the prompt using SearXNG and Llama 3.2 3B.
    """
    logging.info(f"Processing prompt: {prompt}")

    # Step 1: Fetch search results from SearXNG
    search_results = fetch_search_results(prompt)
    if not search_results:
        return "No relevant search results found."

    # # Step 2: Extract content from the top search results
    # context = ""
    # for result in search_results:
    #     url = result.get("url")
    #     if url:
    #         content = extract_webpage_content(url)
    #         if content:
    #             context += f"Source: {url}\nContent: {content}\n\n"

    relevant_info = [result.get("content", "") for result in search_results]
    context = "\n".join(relevant_info)

    # Step 3: Generate a response using Llama 3.2 3B
    llama_service = LlamaService()
    reply = llama_service.generate_text(prompt, context)

    return reply


def setup_rabbitmq_connection():
    """
    Set up and return a RabbitMQ connection and channel.
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
    Callback function to process incoming messages.
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
                    delivery_mode=1                             # Make messages transient
                )
            )
            logging.info(f"Processed and replied to prompt: {prompt}")
        else:
            logging.error("No ReplyTo property found in the incoming message.")
    except Exception as e:
        logging.error(f"Error processing message: {e}")


def start_consumer():
    """
    Start the RabbitMQ consumer.
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