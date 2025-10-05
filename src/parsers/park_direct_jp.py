from typing import List
from bs4 import BeautifulSoup
from src.models import ParkingLot, ParkingPricing
from src.parsers.base_parser import BaseParser
import re

class ParkDirectJpParser(BaseParser):
    """Parser for park-direct.jp pages."""

    def parse(self, soup: BeautifulSoup, url: str) -> List[ParkingLot]:
        """
        Parses the HTML content of a park-direct.jp page.
        """
        return self._parse_nearby_lots(soup, url)

    def _parse_nearby_lots(self, soup: BeautifulSoup, url: str) -> List[ParkingLot]:
        parking_lots = []
        nearby_section = soup.find("h2", string="近くの月極駐車場")
        if not nearby_section:
            return []

        main_container = nearby_section.parent.find_next_sibling("div")
        if not main_container:
            return []

        for lot_container in main_container.find_all("div", recursive=False):
            name_tag = lot_container.find("h2")
            name = name_tag.text.strip() if name_tag else "N/A"

            address_tag = lot_container.find("img").find_next_sibling("div").find("div")
            address = address_tag.text.strip() if address_tag else "N/A"

            pricing = None
            price_tag = lot_container.find("div", string=re.compile(r"月額"))
            if price_tag:
                price_text = price_tag.text.strip()
                match = re.search(r"月額([\d,]+)円", price_text)
                if match:
                    try:
                        price = int(match.group(1).replace(",", ""))
                        pricing = ParkingPricing(monthly_fee=price)
                    except (ValueError, IndexError):
                        pass
            
            lot_data = {
                "name": name,
                "address": address,
                "url": url,
            }
            if pricing:
                lot_data["pricing"] = pricing

            parking_lot = ParkingLot(**lot_data)
            parking_lots.append(parking_lot)
            
        return parking_lots