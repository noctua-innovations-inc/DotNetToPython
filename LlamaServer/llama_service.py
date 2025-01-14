import logging
from typing import Optional
import re
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class LlamaService:
    """
    A service to interact with the Llama 3.2 3B Instruct model for text generation and query processing.
    """

    def __init__(self):
        """
        Initialize the LlamaService by loading the pre-trained model and tokenizer.
        """
        # Load the pre-trained Llama 3.2 3B Instruct model
        self.model = AutoModelForCausalLM.from_pretrained(
            "meta-llama/Llama-3.2-3B-Instruct",             # Model identifier on Hugging Face Hub
            device_map="auto",                              # Automatically distribute the model across available GPUs
            torch_dtype=torch.float16,                      # Use half-precision for better performance
        )

        # Load the tokenizer associated with the Llama 3.2 3B Instruct model
        self.tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-3.2-3B-Instruct")

    def create_prompt_for_llama(self, query: str) -> str:
        """
        Create a basic prompt for Llama 3.2 3B Instruct model.

        Args:
            query (str): The user's query.

        Returns:
            str: A formatted prompt for the model.
        """
        system_prompt = (
            "<|begin_of_text|>\n"
            "<|start_header_id|>system<|end_header_id|>\n"
            "You are a helpful AI assistant. Do not make up any information. Provide a concise answer.\n\n"
            "<|eot_id|>\n"
            f"<|start_header_id|>user<|end_header_id|>\n"
            f"{query}\n"
            "<|eot_id|>\n"
            "<|start_header_id|>assistant<|end_header_id|>"
        )
        return system_prompt

    def create_prompt_restricted_to_context_info_for_llama(self, query: str, context_information: str) -> str:
        """
        Create a context-restricted prompt for Llama 3.2 3B Instruct model.

        Args:
            query (str): The user's query.
            context_information (str): Contextual information to restrict the model's response.

        Returns:
            str: A formatted prompt for the model.
        """
        system_prompt = (
            "<|begin_of_text|>\n"
            "<|start_header_id|>system<|end_header_id|>\n"
            "You are a helpful AI assistant. "
            "Provide one Answer ONLY based on the context provided below. "
            "Do not generate or answer any other questions. "
            "Do not make up or infer any information that is not directly stated in the context. "
            f"Provide a concise answer.  context:\n\n"
            f"{context_information}"
            "<|eot_id|>\n"
            f"<|start_header_id|>user<|end_header_id|>\n"
            f"{query}\n"
            "<|eot_id|>\n"
            "<|start_header_id|>assistant<|end_header_id|>"
        )
        return system_prompt

    def create_response_test_prompt_for_llama(self, query: str, text_to_check: str) -> str:
        """
        Create a prompt to test if the provided text contains an answer to the query.

        Args:
            query (str): The user's query.
            text_to_check (str): The text to evaluate.

        Returns:
            str: A formatted prompt for the model.
        """
        system_prompt = (
            "<|begin_of_text|>\n"
            "<|start_header_id|>system<|end_header_id|>\n"
            "Determine if the following text contains an answer to the question. Respond with \"Yes\" or \"No\".\n"
            "<|start_header_id|>user<|end_header_id|>\n"
            f"Question: {query}\n"
            f"Text: {text_to_check}\n"
            "<|start_header_id|>assistant<|end_header_id|>\n"
            "Answer: <|end_of_text|>\n"
        )
        return system_prompt

    def format_output_from_llama(self, llama_output: str) -> str:
        """
        Format the output generated by the Llama model.

        Args:
            llama_output (str): The raw output from the model.

        Returns:
            str: The formatted output.
        """
        # Remove the final `<|end_of_text|>` token if present
        eot_token = "<|end_of_text|>"
        if llama_output.endswith(eot_token):
            llama_output = llama_output[: -len(eot_token)].strip()

        # Extract the assistant's response from the generated text
        assistant_keyword = "<|start_header_id|>assistant<|end_header_id|>"
        if assistant_keyword in llama_output:
            llama_output = llama_output.split(assistant_keyword, 1)[1].strip()

        return llama_output

    def submit_prompt_to_llama(self, input_text: str) -> str:
        """
        Generate text using the Llama 3.2 3B model.

        Args:
            input_text (str): The input prompt for the model.

        Returns:
            str: The generated text.
        """
        # Tokenize the input text
        inputs = self.tokenizer(
            input_text,                                 # The input text to tokenize
            return_tensors="pt",                        # Return PyTorch tensors
            truncation=True,                            # Enable truncation if the input exceeds the max_length
            max_length=32000,                           # Set the maximum number of tokens for the input
            truncation_strategy="longest_first",        # Truncate the longest part of the input if necessary
        ).to("cuda")                                    # Move the tokenized inputs to the GPU

        # Generate text using the model
        outputs = self.model.generate(
            inputs["input_ids"],                        # Token IDs of the input prompt
            attention_mask=inputs["attention_mask"],    # Attention mask for the input tokens
            max_new_tokens=64000,                       # Maximum number of new tokens to generate
            pad_token_id=self.tokenizer.eos_token_id,   # Use the EOS token as the padding token
            no_repeat_ngram_size=2,                     # Prevent the model from repeating 2-grams
            num_beams=5,                                # Use beam search with 5 beams
            early_stopping=True,                        # Stop generation early if all beam candidates reach the EOS token
        )

        # Decode the generated token IDs back into text
        reply_from_llama = self.tokenizer.decode(outputs[0], skip_special_tokens=False)
        return self.format_output_from_llama(reply_from_llama)

    def submit_query_without_context_to_llama(self, query: str) -> str:
        """
        Submit a query to the Llama model without additional context.

        Args:
            query (str): The user's query.

        Returns:
            str: The model's response.
        """
        prompt_for_llama = self.create_prompt_for_llama(query)
        return self.submit_prompt_to_llama(prompt_for_llama)

    def submit_query_with_context_to_llama(self, query: str, context: str) -> str:
        """
        Submit a query to the Llama model with additional context.

        Args:
            query (str): The user's query.
            context (str): Contextual information to restrict the model's response.

        Returns:
            str: The model's response.
        """
        prompt_for_llama = self.create_prompt_restricted_to_context_info_for_llama(query, context)
        return self.submit_prompt_to_llama(prompt_for_llama)

    def was_query_likely_answered(self, query: str, reply: str) -> Optional[re.Match]:
        """
        Check if the provided reply likely answers the query.

        Args:
            query (str): The user's query.
            reply (str): The model's reply.

        Returns:
            Optional[re.Match]: A match object if the reply contains "Yes", otherwise None.
        """
        test_reply_prompt = self.create_response_test_prompt_for_llama(query, reply)
        result = self.submit_prompt_to_llama(test_reply_prompt)
        return re.search(r"\byes\b", result, re.IGNORECASE)
