"""
Gemini LLM integration for extracting parking data from Markdown.

This module provides a GeminiExtractor class that uses the Gemini API
to parse Markdown content and extract structured parking lot information
according to the Pydantic models.

Example:
    >>> from src.gemini import GeminiExtractor
    >>> from src.utils import DEFAULT_CONFIG
    >>> system_prompt = "Extract parking data."
    >>> extractor = GeminiExtractor(config=DEFAULT_CONFIG, system_prompt=system_prompt)
    >>> markdown = "Parking available for 50000 JPY per month."
    >>> data = extractor.extract_parking_data(markdown, "http://example.com")
    >>> if data:
    ...     print(data[0].pricing.monthly_fee)
    50000
"""

import json
from typing import Any, Dict, List

import google.generativeai as genai
from google.generativeai.types import GenerationConfig

from src.models import ParkingLot

# ==============================================================================
# CLASSES
# ==============================================================================

class GeminiExtractor:
    """Extracts structured data from Markdown using the Gemini LLM."""

    def __init__(self, config: Dict[str, Any], system_prompt: str):
        """
        Initialize the GeminiExtractor.

        Args:
            config: The application configuration dictionary.
            system_prompt: The system prompt to guide the LLM.
        """
        self.config = config
        self.system_prompt = system_prompt
        self.model = self._configure_model()

    def _configure_model(self):
        """Configure and return the Gemini generative model."""
        genai.configure(api_key=self.config["gemini_api_key"])
        return genai.GenerativeModel(
            model_name=self.config["gemini_model"],
            system_instruction=self.system_prompt,
        )

    def extract_parking_data(self, markdown: str, url: str) -> List[ParkingLot]:
        """
        Extract parking data from Markdown content using the Gemini API.

        Args:
            markdown: The Markdown content to process.
            url: The source URL of the content.

        Returns:
            A list of ParkingLot Pydantic models.
        """
        generation_config = GenerationConfig(
            response_mime_type="application/json",
            temperature=0.1,
        )
        prompt = f"Extract parking information from the following text from {url}:\n\n{markdown}"

        try:
            response = self.model.generate_content(
                prompt, generation_config=generation_config
            )
            parsed_data = self.parse_gemini_response(response.text)
            
            # Validate and create ParkingLot models
            valid_lots = []
            for item in parsed_data:
                if self.validate_parking_data(item):
                    item["url"] = url # Ensure URL is set
                    valid_lots.append(ParkingLot(**item))
            return valid_lots

        except Exception as e:
            print(f"Error during Gemini API call for {url}: {e}")
            return []

    def parse_gemini_response(self, response_text: str) -> List[Dict[str, Any]]:
        """
        Parse the JSON response from the Gemini API.

        Args:
            response_text: The raw text response from the API.

        Returns:
            A list of dictionaries containing the extracted data.
        """
        try:
            # The response is expected to be a JSON array of objects
            return json.loads(response_text)
        except json.JSONDecodeError:
            print(f"Failed to decode Gemini JSON response: {response_text}")
            return []

    def validate_parking_data(self, data: Dict[str, Any]) -> bool:
        """
        Perform basic validation on the extracted data dictionary.

        Args:
            data: A dictionary representing a single parking lot.

        Returns:
            True if the data is valid, False otherwise.
        """
        # A name is required for a valid parking lot entry
        return "name" in data and isinstance(data["name"], str)
