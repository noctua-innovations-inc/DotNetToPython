"""
Script Name: text_summarization.py
Description: This script uses the Hugging Face Transformers library to perform text summarization
             using the LongT5 model. It is designed to handle long input texts (up to 16,384 tokens)
             and generate concise summaries.

Usage:
    python text_summarization.py

Dependencies:
    - transformers: Install via `pip install transformers`.
    - torch: Install via `pip install torch`.

Author: Christopher Zielinski
Version: 1.0.0
Date: 2025-01-12
"""

from transformers import T5Tokenizer, LongT5ForConditionalGeneration
from multiprocessing import freeze_support
import torch

if __name__ == '__main__':
    from multiprocessing import freeze_support
    freeze_support()
    
    # Define the custom directory for storing the model
    custom_model_dir = "Z:/Research/long-t5/cache"

    # Load the tokenizer and model, specifying the cache directory
    tokenizer = T5Tokenizer.from_pretrained("google/long-t5-tglobal-base", cache_dir=custom_model_dir)
    model = LongT5ForConditionalGeneration.from_pretrained("google/long-t5-tglobal-base", cache_dir=custom_model_dir)

    # Input text for summarization
    input_text = """
    The Hugging Face Transformers library is a powerful tool for natural language processing (NLP). 
    It provides pre-trained models for tasks like text classification, question answering, and text summarization. 
    The library is built on PyTorch and TensorFlow, making it highly flexible and compatible with various deep learning frameworks. 
    With support for over 100 languages, developers can easily integrate advanced NLP capabilities into their applications. 
    Hugging Face also offers a Model Hub, where users can share and download pre-trained models for a wide range of tasks. 
    """

    # Preprocess the input text
    input_ids = tokenizer(
        "summarize: " + input_text,  # Add task prefix for summarization
        return_tensors="pt",         # Return PyTorch tensors
        max_length=16384,            # 
        truncation=True              # Truncate input if necessary
    ).input_ids

    input_length = input_ids.size(1)  # Get the number of tokens from the tensor shape

    # Set min_length and max_length dynamically (to prevent hallucinations or making the summary too long)
    min_length = max(10, int(0.1 * input_length))   # At least 10 tokens, or 10% of input length
    max_length = min(150, int(0.3 * input_length))  # At most 150 tokens, or 30% of input length

    # Generate the summary
    summary_ids = model.generate(
        input_ids,
        max_length=max_length,      # Set max_length dynamically
        min_length=min_length,      # Set min_length dynamically
        length_penalty=2.0,         # Encourage longer summaries (within the maximum length)
        num_beams=2,                # Use beam search for better quality
        no_repeat_ngram_size=3,     # Avoid repeating n-grams
        early_stopping=True         # If approppreate, stop generation early
    )

    # Decode the summary
    summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)

    # Print the summary
    print("Summary:")
    print(summary)
