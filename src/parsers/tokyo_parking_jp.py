from typing import List
from bs4 import BeautifulSoup
from src.models import ParkingLot, ParkingPricing
from src.parsers.base_parser import BaseParser
import re

class TokyoParkingJpParser(BaseParser):
    """Parser for tokyo-parking.jp pages."""

    def parse(self, soup: BeautifulSoup, url: str) -> List[ParkingLot]:
        """
        Parses the HTML content of a tokyo-parking.jp page.
        """
        parking_lots = []
        main_container = soup.find("div", id="estates")
        if not main_container:
            return []

        for lot_container in main_container.find_all("a"):
            name_tag = lot_container.find("h2")
            name = name_tag.text.strip() if name_tag else "N/A"

            address_tag = lot_container.find("span", string=re.compile(r"〒"))
            address = address_tag.find_next_sibling("span").text.strip() if address_tag else "N/A"
            if address_tag:
                address = address_tag.text.strip() + address

            pricing = None
            divs = lot_container.find_all("div")
            for div in divs:
                if "円（税込）" in div.get_text():
                    price_span = div.find("span")
                    if price_span:
                        try:
                            price_text = price_span.text.strip()
                            price = int(price_text.replace(",", ""))
                            pricing = ParkingPricing(monthly_fee=price)
                            break
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