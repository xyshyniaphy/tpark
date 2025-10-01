"""
File-based cache management for the Tokyo Parking Crawler.

This module provides a CacheManager class to handle storing and retrieving
scraped HTML content (as Markdown) and extracted JSON data. The cache
supports a time-to-live (TTL) to ensure data freshness.

Example:
    >>> from src.cache import CacheManager
    >>> cache = CacheManager(cache_dir="cache", ttl_days=7)
    >>> cache.save_markdown("http://example.com", "Shibuya", "<h1>Hello</h1>")
    >>> if cache.is_cache_valid("http://example.com", "Shibuya"):
    ...     content = cache.load_markdown("http://example.com", "Shibuya")
    ...     print(content)
    # Hello
"""

import hashlib
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.utils import create_directory

# ==============================================================================
# CLASSES
# ==============================================================================

class CacheManager:
    """Manages file-based caching with a time-to-live (TTL)."""

    def __init__(self, cache_dir: str, ttl_days: int):
        """
        Initialize the CacheManager.

        Args:
            cache_dir: The directory where cache files will be stored.
            ttl_days: The number of days until a cache entry becomes stale.
        """
        self.cache_dir = Path(cache_dir)
        self.ttl_seconds = ttl_days * 24 * 60 * 60
        create_directory(self.cache_dir)

    def _get_cache_path(self, url: str, location: str, extension: str) -> Path:
        """Generate a consistent cache file path."""
        unique_string = f"{url}-{location}"
        hashed_name = hashlib.md5(unique_string.encode()).hexdigest()
        return self.cache_dir / f"{hashed_name}.{extension}"

    def save_markdown(self, url: str, location: str, markdown_content: str) -> Path:
        """
        Save scraped and converted Markdown content to the cache.

        Args:
            url: The original URL of the scraped page.
            location: The location associated with the scrape.
            markdown_content: The content to save.

        Returns:
            The path to the saved cache file.
        """
        cache_file = self._get_cache_path(url, location, "md")
        with open(cache_file, "w", encoding="utf-8") as f:
            f.write(markdown_content)
        return cache_file

    def save_json(self, url: str, location: str, data: List[Dict[str, Any]]) -> Path:
        """
        Save extracted JSON data to the cache.

        Args:
            url: The original URL of the scraped page.
            location: The location associated with the scrape.
            data: The JSON-serializable data to save.

        Returns:
            The path to the saved cache file.
        """
        cache_file = self._get_cache_path(url, location, "json")
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return cache_file

    def load_markdown(self, url: str, location: str) -> Optional[str]:
        """
        Load Markdown content from the cache if it is valid.

        Args:
            url: The original URL of the scraped page.
            location: The location associated with the scrape.

        Returns:
            The cached content, or None if not found or stale.
        """
        cache_file = self._get_cache_path(url, location, "md")
        if self.is_cache_valid(cache_file):
            with open(cache_file, "r", encoding="utf-8") as f:
                return f.read()
        return None

    def load_json(self, url: str, location: str) -> Optional[List[Dict[str, Any]]]:
        """
        Load JSON data from the cache if it is valid.

        Args:
            url: The original URL of the scraped page.
            location: The location associated with the scrape.

        Returns:
            The cached data, or None if not found or stale.
        """
        cache_file = self._get_cache_path(url, location, "json")
        if self.is_cache_valid(cache_file):
            with open(cache_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return None

    def is_cache_valid(self, cache_file: Path) -> bool:
        """
        Check if a cache file exists and is within its TTL.

        Args:
            cache_file: The path to the cache file.

        Returns:
            True if the cache is valid, False otherwise.
        """
        if not cache_file.exists():
            return False
        
        file_mod_time = cache_file.stat().st_mtime
        if (time.time() - file_mod_time) > self.ttl_seconds:
            return False
            
        return True

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the cache directory.

        Returns:
            A dictionary with cache statistics.
        """
        total_files = 0
        total_size_bytes = 0
        stale_files = 0

        for file in self.cache_dir.iterdir():
            if file.is_file():
                total_files += 1
                total_size_bytes += file.stat().st_size
                if not self.is_cache_valid(file):
                    stale_files += 1
        
        return {
            "total_files": total_files,
            "total_size_mb": round(total_size_bytes / (1024 * 1024), 2),
            "stale_files": stale_files,
            "cache_directory": str(self.cache_dir),
        }
