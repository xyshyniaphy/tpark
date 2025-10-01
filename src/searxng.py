"""
SearXNG client for performing web searches.

This module provides a client to interact with a SearXNG instance,
allowing the application to perform web searches and retrieve results
in a structured format.

Example:
    >>> from src.searxng import SearXNGClient
    >>> from src.utils import DEFAULT_CONFIG
    >>> client = SearXNGClient(instance_url="http://127.0.0.1:8888", config=DEFAULT_CONFIG)
    >>> query = client.build_query("Shibuya", DEFAULT_CONFIG["search_query_template"])
    >>> results = client.search(query, max_results=5)
    >>> for result in results:
    ...     print(result["url"])
"""

from typing import Any, Dict, List

import requests

# ==============================================================================
# CLASSES
# ==============================================================================

class SearXNGClient:
    """A client for interacting with a SearXNG meta-search engine instance."""

    def __init__(self, instance_url: str, config: Dict[str, Any]):
        """
        Initialize the SearXNGClient.

        Args:
            instance_url: The base URL of the SearXNG instance.
            config: The application configuration dictionary.
        """
        self.instance_url = instance_url.rstrip("/")
        self.config = config

    def search(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """
        Perform a search using the SearXNG instance.

        Args:
            query: The search query string.
            max_results: The maximum number of results to return.

        Returns:
            A list of search result dictionaries.
        """
        params = {
            "q": query,
            "format": "json",
            "safesearch": 1,
            "language": "ja-JP",
        }
        try:
            response = requests.get(self.instance_url, params=params, timeout=10)
            response.raise_for_status()  # Raise an exception for bad status codes
            results = response.json().get("results", [])
            return self.filter_parking_results(results)[:max_results]
        except requests.RequestException as e:
            print(f"Error connecting to SearXNG instance: {e}")
            return []

    def filter_parking_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter search results to identify potential parking lot listings.

        Args:
            results: A list of raw search result dictionaries from SearXNG.

        Returns:
            A filtered list of search result dictionaries.
        """
        filtered = []
        for result in results:
            # Basic filtering logic (can be improved)
            if "park" in result.get("url", "") or "parking" in result.get("url", ""):
                filtered.append(result)
        return filtered

    def build_query(self, location: str, template: str) -> str:
        """
        Build a search query from a location and a template.

        Args:
            location: The location to search for (e.g., "Shibuya").
            template: The query template string with a {location} placeholder.

        Returns:
            The formatted search query string.
        """
        return template.format(location=location)
