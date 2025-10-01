"""
Utility functions for the Tokyo Parking Crawler.

This module provides common helper functions for logging, banner display,
time formatting, text truncation, and directory creation.

Example:
    >>> from src.utils import setup_logging
    >>> logger = setup_logging("INFO", "crawler.log")
    >>> logger.info("This is a test log message.")
"""

import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict

# ==============================================================================
# CONSTANTS
# ==============================================================================

APP_NAME = "Tokyo Parking Crawler"
VERSION = "1.0.0"

DEFAULT_CONFIG: Dict[str, Any] = {
    "log_level": "INFO",
    "log_file": "logs/parking_crawler.log",
    "cache_dir": "webpages",
    "cache_ttl_days": 7,
    "output_file": "parking_results.md",
    "searxng_instance_url": "http://127.0.0.1:8888",
    "max_search_results": 10,
    "vehicle_spec": {
        "length_m": 4.8,
        "width_m": 1.9,
        "height_m": 2.1,
    },
    "scoring_weights": {
        "dimension": 0.4,
        "price": 0.3,
        "distance": 0.2,
        "amenity": 0.1,
    },
    "max_price": 100000,
    "max_distance_km": 5.0,
    "output_top_n": 5,
    "search_query_template": "site:*.jp 月極駐車場 {location} 屋外 平置き",
    "gemini_model": "gemini/gemini-2.0-flash",
    "gemini_api_key": "YOUR_API_KEY",
}


# ==============================================================================
# FUNCTIONS
# ==============================================================================

def setup_logging(log_level: str, log_file: str) -> logging.Logger:
    """
    Set up logging for the application.

    Args:
        log_level: The desired log level (e.g., "INFO", "DEBUG").
        log_file: The path to the log file.

    Returns:
        The configured logger instance.
    """
    logger = logging.getLogger(APP_NAME)
    level = getattr(logging, log_level.upper(), logging.INFO)
    logger.setLevel(level)

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Create file handler
    log_path = Path(log_file)
    create_directory(log_path.parent)
    file_handler = logging.FileHandler(log_path)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Create stream handler
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    return logger


def show_usage_instructions() -> None:
    """
    Display usage instructions for the CLI.
    """
    print(f"Usage: python tokyo_parking_crawler.py \"<location>\"")
    print(f"       python tokyo_parking_crawler.py \"<latitude>,<longitude>\"")
    print(f"Example: python tokyo_parking_crawler.py \"渋谷駅\"")


def show_banner() -> None:
    """
    Display the application banner.
    """
    print("=" * 60)
    print(f"{APP_NAME} - Version {VERSION}")
    print("=" * 60)
    print("Finding monthly parking lots in Tokyo for your camping car...")
    print("-" * 60)


def format_time_duration(seconds: float) -> str:
    """
    Format a time duration in seconds into a human-readable string.

    Args:
        seconds: The duration in seconds.

    Returns:
        A formatted string (e.g., "1m 23s", "45.6s").
    """
    if seconds >= 60:
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes}m {seconds}s"
    return f"{seconds:.1f}s"


def truncate_text(text: str, max_length: int) -> str:
    """
    Truncate a string to a maximum length, adding an ellipsis if truncated.

    Args:
        text: The string to truncate.
        max_length: The maximum desired length.

    Returns:
        The truncated string.
    """
    if len(text) > max_length:
        return text[: max_length - 3] + "..."
    return text


def create_directory(path: Path) -> None:
    """
    Create a directory if it does not already exist.

    Args:
        path: The directory path to create.
    """
    path.mkdir(parents=True, exist_ok=True)
