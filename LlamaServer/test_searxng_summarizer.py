import unittest
from unittest.mock import patch, Mock
from searxng_summarizer import SearxngSummarizer

class TestSearxngSummarizer(unittest.TestCase):
    def setUp(self):
        self.searxng_instance_url = "http://example.com"
        self.summarizer = SearxngSummarizer(self.searxng_instance_url)

    @patch("requests.get")
    def test_search_searxng(self, mock_get):
        # Mock the response from SearXNG
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {"title": "Test Result 1", "url": "http://example.com/1", "score": 0.9},
                {"title": "Test Result 2", "url": "http://example.com/2", "score": 0.8},
            ]
        }
        mock_get.return_value = mock_response

        # Test the search function
        results = self.summarizer.search_searxng("test query")
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["title"], "Test Result 1")
        self.assertEqual(results[1]["url"], "http://example.com/2")

    @patch("requests.get")
    def test_fetch_webpage_content(self, mock_get):
        # Mock the response from a webpage
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "<html><body><p>Test content</p></body></html>"
        mock_get.return_value = mock_response

        # Test the fetch function
        content = self.summarizer.fetch_webpage_content("http://example.com")
        self.assertEqual(content, "Test content")

    @patch.object(SearxngSummarizer, "summarizer", new_callable=Mock)
    def test_summarize_text(self, mock_summarizer):
        # Mock the summarization pipeline
        mock_summarizer.return_value = [{"summary_text": "Test summary"}]

        # Test the summarize function
        summary = self.summarizer.summarize_text("Test content")
        self.assertEqual(summary, "Test summary")

    @patch("searxng_summarizer.SearxngSummarizer.search_searxng")
    @patch("searxng_summarizer.SearxngSummarizer.fetch_webpage_content")
    @patch("searxng_summarizer.SearxngSummarizer.summarize_text")
    def test_process_query(self, mock_summarize, mock_fetch, mock_search):
        # Mock the search, fetch, and summarize functions
        mock_search.return_value = [
            {"title": "Test Result", "url": "http://example.com", "score": 0.9}
        ]
        mock_fetch.return_value = "Test content"
        mock_summarize.return_value = "Test summary"

        # Test the process_query function
        results = self.summarizer.process_query("test query")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["title"], "Test Result")
        self.assertEqual(results[0]["summary"], "Test summary")


if __name__ == "__main__":
    unittest.main()
