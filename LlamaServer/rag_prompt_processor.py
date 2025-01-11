import pika
import logging
import sys
import os
import requests
from bs4 import BeautifulSoup
from transformers import AutoModelForCausalLM, AutoTokenizer
from typing import List, NotRequired, TypedDict
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

    def format_search_results_for_llama(self, search_results: str) -> str:
        if not search_results:
            logging.warnr("No search results found for prompt.")
            return ""
        relevant_info = [result.get("content", "") for result in search_results]
        formatted_text = "\n".join(relevant_info)
        return f"Actual RealWeb Search Results:\n{formatted_text}\n"

    def create_system_prompt_for_llama(self, query: str, search_results: str) -> str:
        """
        create Llama 3.2 3B templated prompt.
        See also... https://www.llama.com/docs/how-to-guides/prompting/
        """
        # Format the prompt using the Llama 3.2 prompt template
        system_prompt = (
            "<|start_header_id|>system<|end_header_id|>\n"
            "You are a helpful and knowledgeable assistant. Your knowledge is based on data available up until October 2022. "
            "For any information or events that occurred after this date, you will rely on the search results provided below. "
            "Use the search results to answer the user's query accurately and provide up-to-date information.\n\n"
            f"**Search Results:**\n{search_results}\n\n"
            "When responding:\n"
            "1. If the user's query relates to events or information after October 2022, prioritize the search results.\n"
            "2. If the search results are insufficient or irrelevant, inform the user that you cannot provide an answer based on the available information.\n"
            "3. Always cite the search results when using them to answer the user's query.\n"
            "<|eot_id|>\n"
            f"<|start_header_id|>user<|end_header_id|>\n"
            f"{query}\n"
            "<|eot_id|>\n"
            "<|start_header_id|>assistant<|end_header_id|>"
        )

        return system_prompt

    def format_output_from_llama(self, llama_output: str) -> str:
        # Remove the final `<|end_of_text|>` token if present
        eot_token = "<|end_of_text|>"
        if llama_output.endswith(eot_token):
            llama_output = llama_output[:-len(eot_token)].strip()

        # Extract the assistant's response from the generated text
        assistant_keyword = "<|start_header_id|>assistant<|end_header_id|>"
        if assistant_keyword in llama_output:
            llama_output = llama_output.split(assistant_keyword, 1)[1].strip()

        return llama_output

    def submit_prompt_to_llama(self, input_text: str) -> str:
        """
        Generate text using the Llama 3.2 3B model.
        """
        # Tokenize the input text
        inputs = self.tokenizer(
            input_text,                                     # The input text to tokenize
            return_tensors="pt",                            # Return PyTorch tensors (required for the model)
            truncation=True,                                # Enable truncation if the input exceeds the max_length
            max_length=32000,                               # Set the maximum number of tokens for the input
            truncation_strategy="longest_first"             # Truncate the longest part of the input if necessary
        ).to("cuda")                                        # Move the tokenized inputs to the GPU for faster processing

        # Generate text using the model.
        outputs = self.model.generate(
            inputs["input_ids"],                            # Token IDs of the input prompt
            attention_mask=inputs["attention_mask"],        # Attention mask to indicate which tokens are actual input
            max_new_tokens=64000,                           # Maximum number of new tokens to generate (excluding the input tokens)
            pad_token_id=self.tokenizer.eos_token_id,       # Use the end-of-sequence (EOS) token as the padding token
            no_repeat_ngram_size=2,                         # Prevent the model from repeating 2-grams (pairs of words)
            num_beams=5,                                    # Use beam search with 5 beams to explore multiple candidate sequences
            early_stopping=True                             # Stop generation early if all beam candidates reach the EOS token
        )

        # Decode the generated token IDs back into text.
        return self.tokenizer.decode(outputs[0], skip_special_tokens=False)

    def submit_prompt_with_context_to_llama(self, prompt: str, context: str) -> str:
        prompt_for_llama = self.create_system_prompt_for_llama(prompt, context)
        reply_from_llama = self.submit_prompt_to_llama(prompt_for_llama)
        return self.format_output_from_llama(reply_from_llama)

# Define the TypedDict classes
class SearchResult(TypedDict):
    title: str
    url: str
    content: str
    engine: str
    score: NotRequired[float]


def fetch_search_results(query: str, max_results: int = MAX_SEARCH_RESULTS) -> List[SearchResult]:
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
        return response.json().get("results", [])
    except Exception as e:
        logging.error(f"Error fetching search results: {e}")
        return []

def extract_webpage_content(url: str) -> str:
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

def process_prompt(prompt: str) -> str:
    """
    Process the prompt using SearXNG and Llama 3.2 3B.
    """
    logging.info(f"Processing prompt: {prompt}")

    # Step 1: Fetch search results from SearXNG
    search_results = fetch_search_results(prompt)

    # Step 2: Extract relevant information from the search results
    context = llama_service.format_search_results_for_llama(search_results)

    # Step 3: Generate a response using Llama 3.2 3B
    return llama_service.submit_prompt_with_context_to_llama(prompt, context)


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


llama_service = LlamaService()


if __name__ == "__main__":
    start_consumer()
