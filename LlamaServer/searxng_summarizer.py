#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
searxng_summarizer.py

A Python script to search and summarize results from a SearXNG instance using the LongT5 model.
This script allows users to perform web searches via a SearXNG instance, retrieve the results,
and generate concise summaries of the content using the LongT5 model, which is specialized for
long-input sequences.

Author: Christopher Zielinski
Date: 2025-01-13
Version: 1.0

Usage:
    python searxng_summarizer.py <query>

    Example:
        python searxng_summarizer.py "What is the future of AI?"

Dependencies:
    - Python 3.8+
    - requests
    - transformers
    - torch

Configuration:
    - Set the `searxng_instance_url` to the URL of your SearXNG instance.
    - Optionally, configure the `custom_model_dir` to specify where the LongT5 model is cached.

Features:
    - Searches a SearXNG instance for a given query.
    - Filters and sorts search results by relevance.
    - Summarizes the combined content of search results using the LongT5 model.
    - Logs all operations to a file (`searxng_summarizer.log`) and the console.

License:
    MIT License

Disclaimer:
    This script is provided "as-is" without any warranties. Use at your own risk.
"""

import requests
import os
import logging

from typing import List, TypedDict, NotRequired
from transformers import T5Tokenizer, LongT5ForConditionalGeneration

# Define the custom directory for storing the model
LLM_LONG_T5_CACHE = os.getenv("LLM_LONG_T5_CACHE", "Z:/Research/long-t5/cache")

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,                                    # Set the logging level (INFO, WARNING, ERROR, etc.)
    format="%(asctime)s - %(levelname)s - %(message)s",     # Define log format
    handlers=[
        logging.StreamHandler()                             # Log to the console
    ],
)
logger = logging.getLogger(__name__)

class SearxngSummarizer:
    """
    A class to search and summarize results from a SearXNG instance using the LongT5 model.
    """

    class SearchResult(TypedDict):
        """
        A TypedDict to define the structure of a search result.
        """
        title: str
        url: str
        content: str
        score: NotRequired[float]

    def __init__(self, searxng_instance_url: str, headers: dict = None):
        """
        Initialize the SearxngSummarizer.

        :param searxng_instance_url: URL of the SearXNG instance.
        :param headers: Optional headers for HTTP requests.
        """
        self.searxng_instance_url = searxng_instance_url
        self.headers = headers or {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

    def search_searxng(self, query: str) -> List[SearchResult]:
        """
        Search a SearXNG instance for the given query and return sorted results.

        :param query: The search query.
        :return: List of search results, filtered and sorted by score.
        """
        params = {"q": query, "format": "json"}
        try:
            response = requests.get(self.searxng_instance_url, params=params, headers=self.headers)
            response.raise_for_status()  # Raise an exception for HTTP errors
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch results from SearXNG: {e}")
            raise

        results: List[self.SearchResult] = response.json().get("results", [])

        # Filter out low-scoring results
        filtered_results = [result for result in results if result.get("score", 0) >= 1.5]

        logger.info(f"Found {len(filtered_results)} results after filtering.")
        return filtered_results

    def summarize(self, input_text: str) -> str:
        """
        Summarize the input text using the LongT5 model.

        The LongT5 excels at summarizong long documents, such as academic papers,
        reports, or books, into concise summaries while preserving key information.

        :param input_text: The text to summarize.
        :return: The summarized text.
        """

        try:
            # Load the tokenizer and model, specifying the cache directory
            tokenizer = T5Tokenizer.from_pretrained("google/long-t5-tglobal-base", cache_dir=LLM_LONG_T5_CACHE)
            model = LongT5ForConditionalGeneration.from_pretrained("google/long-t5-tglobal-base", cache_dir=LLM_LONG_T5_CACHE)
        except Exception as e:
            logger.error(f"Failed to load tokenizer or model: {e}")
            raise

        # Prepare the input text with a summarization prompt
        prompt_text = f"summarize: {input_text}"

        # Tokenize the input text
        input_ids = tokenizer(
            prompt_text,
            return_tensors="pt",  # Return PyTorch tensors
            max_length=16384,     # Set maximum input length
            truncation=True       # Truncate input if necessary
        ).input_ids

        input_length = input_ids.size(1)  # Get the number of tokens in the input

        # Set dynamic min_length and max_length for the summary
        min_length = 1
        max_length = min(150, int(0.3 * input_length))  # At most 150 tokens, or 30% of input length

        # Generate the summary using the model
        summary_ids = model.generate(
            input_ids,
            max_length=max_length,      # Set max_length dynamically
            min_length=min_length,      # Set min_length dynamically
            length_penalty=1.5,         # Encourage longer summaries (within the maximum length)
            num_beams=5,                # Use beam search for better quality
            no_repeat_ngram_size=2,     # Avoid repeating n-grams
            early_stopping=False        # Stop generation early if appropriate
        )

        # Decode and return the summary
        summarized_text = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
        logger.debug(f"Summarized Search Results: {summarized_text}")
        return summarized_text

    def process_query(self, query: str) -> str:
        """
        Process a search query: search, fetch content, and summarize.

        :param query: The search query.
        :return: The summarized text of the search results.
        """
        logger.info(f"Processing query: {query}")
        query_results = self.search_searxng(query)

        # Combine titles, URLs, and content from search results into a single string
        summary_input = ""
        try:
            for result in query_results:
                summary_input += (
                    f"{result['title']}\n"
                    f"{result['url']}\n"
                    f"{result['content']}\n\n"
                )
        except Exception as e:
            logger.error(f"Error during search result processing: {e}")
            raise

        # Summarize the combined text
        logger.info("Summarizing search results...")

        # # Summarization of search engine results proved inconsistent across various sources, 
        # # making it difficult to achieve reliable and accurate summaries. Additionally, 
        # # webpage scraping introduced significant complexity, as many websites (e.g., news 
        # # platforms) did not provide data in a structured or easily consumable format. 
        # # Due to these challenges, summarization of the search summaries and webpage scraping
        # # was excluded from the scope of this research and demo application.
        # summary = self.summarize(summary_input)
        summary = summary_input
        return summary
