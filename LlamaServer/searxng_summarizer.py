import requests
from bs4 import BeautifulSoup
from transformers import pipeline
from typing import List, NotRequired, TypedDict

import re
import torch

from transformers import T5Tokenizer, LongT5ForConditionalGeneration

class SearxngSummarizer:

    # Define the TypedDict classes
    class SearchResult(TypedDict):
        title: str
        url: str
        content: str
        engine: str
        score: NotRequired[float]

    def __init__(self, searxng_instance_url, headers=None):
        """
        Initialize the SearxngSummarizer.

        :param searxng_instance_url: URL of the SearXNG instance.
        :param headers: Optional headers for HTTP requests.
        """
        self.searxng_instance_url = searxng_instance_url
        self.headers = headers or {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        self._summarizer = None  # Lazily initialize the summarizer

    def search_searxng(self, query):
        """
        Search a SearXNG instance for the given query and return sorted results.

        :param query: The search query.
        :return: List of search results.
        """
        params = {"q": query, "format": "json"}
        response = requests.get(self.searxng_instance_url, params=params, headers=self.headers)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch results from SearXNG: {response.status_code}")

        results: List[self.SearchResult] = response.json().get("results", [])

        # Sort results by score (highest to lowest)
        results = sorted(results, key=lambda x: x.get("score", 0), reverse=True)

        # Discard entries where 'score' is less than 0.3
        return [result for result in results if result['score'] >= 0.3]


    def fetch_webpage_content(self, url):
        """
        Fetch the content of a webpage.

        :param url: URL of the webpage.
        :return: Extracted text content from the webpage.
        """
        response = requests.get(url, headers=self.headers)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch webpage: {response.status_code}")

        soup = BeautifulSoup(response.text, "lxml")
        text = soup.get_text(separator=' ')

        # Step 1: Replace all whitespace (except newlines) with a single space
        text = re.sub(r'[^\S\n]+', ' ', text)

        # Step 2: Replace sequences of newlines (possibly with spaces) with a single newline
        text = re.sub(r'(\n[^\S\n]*)+', '\n', text)

        # Optionally, strip leading and trailing whitespace
        text = text.strip()

        return text

    def summarize(self, input_text):
        # Define the custom directory for storing the model
        custom_model_dir = "Z:/Research/long-t5/cache"

        # Load the tokenizer and model, specifying the cache directory
        tokenizer = T5Tokenizer.from_pretrained("google/long-t5-tglobal-base", cache_dir=custom_model_dir)
        model = LongT5ForConditionalGeneration.from_pretrained("google/long-t5-tglobal-base", cache_dir=custom_model_dir)

        prompt_text = f"summarize: {input_text}"

        # Preprocess the input text
        input_ids = tokenizer(
            prompt_text,                # Add task prefix for summarization
            return_tensors="pt",        # Return PyTorch tensors
            max_length=16384,           # 
            truncation=True             # Truncate input if necessary
        ).input_ids

        input_length = input_ids.size(1)  # Get the number of tokens from the tensor shape

        # Set min_length and max_length dynamically (to prevent hallucinations or making the summary too long)
        min_length = 1
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

        # Decode and return the reslt
        result = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
        return result


    def process_query(self, query):
        """
        Process a search query: search, fetch content, and summarize.

        :param query: The search query.
        :return: List of dictionaries containing title, URL, and summary.
        """
        query_results = self.search_searxng(query)

        summary = ""
        try:
            for i, result in enumerate(query_results, 1):
                summary += (
                    f"{result['title']}\n"
                    f"{result['url']}\n"
                    f"{result['content']}\n\n"
                )
        except Exception as e:
            print(f"Error during search: {e}")

        return self.summarize(summary)



def main():
    searxng_instance_url = "http://127.0.0.1:8080/"
    summarizer = SearxngSummarizer(searxng_instance_url)

    query = input("Enter your search query: ")
    print(f"Searching for: {query}")

    try:
        print(summarizer.process_query(query))
    except Exception as e:
        print(f"Error during search: {e}")


if __name__ == "__main__":
    main()