from typing import List
from bs4 import BeautifulSoup
from src.models import ParkingLot, ParkingPricing
from src.parsers.base_parser import BaseParser
import re

class AthomeCoJpParser(BaseParser):
    """Parser for athome.co.jp pages."""

    def parse(self, soup: BeautifulSoup, url: str) -> List[ParkingLot]:
        """
        Parses the HTML content of a athome.co.jp page.
        """
        if soup.find("athome-csite-pc-part-rent-business-other-bukken-card"):
            return self._parse_search_page(soup, url)
        else:
            return self._parse_detail_page(soup, url)

    def _parse_detail_page(self, soup: BeautifulSoup, url: str) -> List[ParkingLot]:
        # Placeholder for detail page parsing
        return []

    def _parse_search_page(self, soup: BeautifulSoup, url: str) -> List[ParkingLot]:
        parking_lots = []
        for item in soup.find_all("athome-csite-pc-part-rent-business-other-bukken-card"):
            name_tag = item.find("h2").find("span")
            name = name_tag.text.strip() if name_tag else "N/A"

            address = "N/A"
            address_tag = item.find("td")
            if address_tag:
                spans = address_tag.find_all("span")
                if spans:
                    address = spans[-1].text.strip()

            pricing = None
            price_section = item.find("td")
            if price_section:
                price_section = price_section.find_next_sibling("td")
                if price_section:
                    price_text = price_section.text.strip()
                    match = re.search(r"([\d\.]+)万円", price_text)
                    if match:
                        try:
                            price = float(match.group(1)) * 10000
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