"""
Web scraping and HTML processing for the Tokyo Parking Crawler.

This module provides a WebScraper class for fetching HTML content from URLs
with retries and random user agents. It also includes functions to convert
HTML to Markdown and to clean up the HTML before conversion.

Example:
    >>> from src.scraper import WebScraper, html_to_markdown
    >>> from src.utils import DEFAULT_CONFIG
    >>> scraper = WebScraper(config=DEFAULT_CONFIG)
    >>> html = scraper.fetch("http://example.com")
    >>> if html:
    ...     markdown = html_to_markdown(html)
    ...     print(markdown)
"""

import random
import time
from typing import Any, Dict, List, Optional
import warnings

import requests
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
from markdownify import markdownify as md

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

# ==============================================================================
# CONSTANTS
# ==============================================================================

USER_AGENTS: List[str] = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15",
]

# ==============================================================================
# CLASSES
# ==============================================================================

class WebScraper:
    """A robust web scraper with anti-bot measures."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the WebScraper.

        Args:
            config: The application configuration dictionary.
        """
        self.config = config

    def _get_headers(self) -> Dict[str, str]:
        """Return a dictionary of headers with a random User-Agent."""
        return {"User-Agent": random.choice(USER_AGENTS)}

    def _retry_request(self, url: str, attempts: int = 3) -> Optional[str]:
        """
        Attempt to fetch a URL with retries on failure.

        Args:
            url: The URL to fetch.
            attempts: The number of times to retry.

        Returns:
            The HTML content as a string, or None if all attempts fail.
        """
        for i in range(attempts):
            try:
                response = requests.get(url, headers=self._get_headers(), timeout=15)
                response.raise_for_status()
                return response.text
            except requests.RequestException as e:
                print(f"Attempt {i+1}/{attempts} failed for {url}: {e}")
                time.sleep(2 ** i)  # Exponential backoff
        return None

    def fetch(self, url: str) -> Optional[str]:
        """
        Fetch the HTML content of a given URL.

        Args:
            url: The URL to fetch.

        Returns:
            The HTML content as a string, or None on failure.
        """
        return self._retry_request(url)

# ==============================================================================
# FUNCTIONS
# ==============================================================================

def clean_html(soup: BeautifulSoup) -> BeautifulSoup:
    """
    Remove unnecessary elements from a BeautifulSoup object.

    This function removes scripts, styles, navigation, footers, and other
    elements that are unlikely to contain relevant parking information.

    Args:
        soup: The BeautifulSoup object to clean.

    Returns:
        The cleaned BeautifulSoup object.
    """
    for element in soup(["script", "style", "header", "footer", "nav", "aside"]):
        element.decompose()
    return soup

def html_to_markdown(html: str) -> str:
    """
    Convert HTML content to clean Markdown.

    Args:
        html: The HTML content as a string.

    Returns:
        The converted Markdown content as a string.
    """
    soup = BeautifulSoup(html, "lxml")
    cleaned_soup = clean_html(soup)
    # Use markdownify to convert the cleaned HTML to Markdown
    return md(str(cleaned_soup.body), heading_style="ATX", bullets="* ")
