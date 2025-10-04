from abc import ABC, abstractmethod
from typing import List
from bs4 import BeautifulSoup
from src.models import ParkingLot

class BaseParser(ABC):
    """Abstract base class for website-specific parking lot parsers."""

    @abstractmethod
    def parse(self, soup: BeautifulSoup, url: str) -> List[ParkingLot]:
        """
        Parses the HTML content of a page to extract parking lot information.

        Args:
            soup: A BeautifulSoup object representing the cleaned HTML of the page.
            url: The URL of the page being parsed.

        Returns:
            A list of ParkingLot data models.
        """
        pass
