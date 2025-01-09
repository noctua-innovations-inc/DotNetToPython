################################################################################
#
# Initial gRPC server implementation.
# Depreciated in favour of a Message Queue Pattern approach.
# Please use prompt_processor.py as your startup project.
#
################################################################################

import grpc
from concurrent import futures
import llama_service_pb2
import llama_service_pb2_grpc
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
import torch


class LlamaService(llama_service_pb2_grpc.LlamaServiceServicer):
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


    def GenerateText(self, request, context):

        # Extract the prompt from the gRPC request.
        prompt = request.prompt

        # Tokenize the input prompt using the tokenizer.
        # This converts the text into a format that the model can understand (e.g., token IDs).
        inputs = self.tokenizer(
            prompt,                                         # The input text to tokenize
            return_tensors="pt",                            # Return PyTorch tensors (required for the model)
            truncation=True,                                # Enable truncation if the input exceeds the max_length
            max_length=512,                                 # Set the maximum number of tokens for the input
            truncation_strategy="longest_first"             # Truncate the longest part of the input if necessary
        ).to("cuda")                                        # Move the tokenized inputs to the GPU for faster processing

        # Generate text using the model.
        # The model takes the tokenized input and produces a sequence of tokens as output.
        outputs = self.model.generate(
            inputs["input_ids"],                            # Token IDs of the input prompt
            attention_mask=inputs["attention_mask"],        # Attention mask to indicate which tokens are actual input
            max_new_tokens=1024,                            # Maximum number of new tokens to generate (excluding the input tokens)
            pad_token_id=self.tokenizer.eos_token_id,       # Use the end-of-sequence (EOS) token as the padding token
            no_repeat_ngram_size=2,                         # Prevent the model from repeating 2-grams (pairs of words)
            num_beams=5,                                    # Use beam search with 5 beams to explore multiple candidate sequences
            early_stopping=True                             # Stop generation early if all beam candidates reach the EOS token
        )

        # Decode the generated token IDs back into human-readable text.
        # The `skip_special_tokens=True` argument removes special tokens like [EOS] from the output.
        generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Remove the input prompt from the generated text (if present).
        # This ensures that only the newly generated text is returned.
        if generated_text.startswith(prompt):
            generated_text = generated_text[len(prompt):].strip()

        # Return the generated text as a gRPC response.
        return llama_service_pb2.TextResponse(generated_text=generated_text)


def serve():
    # Create a gRPC server with a thread pool of 10 worker threads.
    # The ThreadPoolExecutor allows the server to handle multiple requests concurrently.
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    # Register the LlamaService implementation with the gRPC server.
    # LlamaService() is an instance of the service implementation, and `add_LlamaServiceServicer_to_server`
    # binds the service methods defined in the protobuf file to the server.
    llama_service_pb2_grpc.add_LlamaServiceServicer_to_server(LlamaService(), server)

    # Bind the server to a specific port (50051) on all available network interfaces ('[::]').
    # The server will listen for incoming gRPC requests on this port.
    # The port is marked as "insecure" because it does not use SSL/TLS encryption.
    server.add_insecure_port('[::]:50051')

    # Start the gRPC server.
    # This begins listening for incoming requests and processing them using the registered service.
    server.start()

    # Block the main thread until the server is terminated (e.g., via Ctrl+C or a shutdown signal).
    # This ensures the server remains running and continues to handle requests.
    server.wait_for_termination()


if __name__ == '__main__':
    serve()

