from typing import List
from bs4 import BeautifulSoup
from src.models import ParkingLot
from src.parsers.base_parser import BaseParser

class ParkDirectJpParser(BaseParser):
    """Parser for park-direct.jp pages."""

    def parse(self, soup: BeautifulSoup, url: str) -> List[ParkingLot]:
        """
        Parses the HTML content of a park-direct.jp page.
        """
        # TODO: Implement parser logic
        return []
