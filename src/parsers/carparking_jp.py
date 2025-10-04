import re
from typing import List
from bs4 import BeautifulSoup
from src.models import ParkingLot, ParkingDimensions, ParkingPricing, ParkingAmenities
from src.parsers.base_parser import BaseParser

class CarParkingJpParser(BaseParser):
    """Parser for carparking.jp pages."""

    def parse(self, soup: BeautifulSoup, url: str) -> List[ParkingLot]:
        """
        Parses the HTML content of a carparking.jp page.
        """
        lots = []

        name_tag = soup.find('h2')
        name = name_tag.get_text(strip=True) if name_tag else 'No name found'
        
        address = None
        amenities = ParkingAmenities()
        pricing = ParkingPricing()
        dimensions = ParkingDimensions()

        details_section = soup.find('h3', string='詳細情報')
        if not details_section:
            return []
            
        details_table = details_section.find_next('table')
        if not details_table:
            return []

        rows = details_table.select('tbody > tr')
        for row in rows:
            th = row.find('th')
            td = row.find('td')
            if th and td:
                header = th.get_text(strip=True)
                value = td.get_text(strip=True)
                
                if '所在地' in header:
                    address = value
                elif '賃料' in header:
                    price_match = re.search(r'([\d,]+)円', value)
                    if price_match:
                        pricing.monthly_fee = int(price_match.group(1).replace(',', ''))
                elif '利用可能時間' in header and '24時間' in value:
                    amenities.is_24_7 = True
                elif '屋内外' in header and '屋外' in value:
                    amenities.is_covered = False
                elif '保証金' in header and 'ヶ月分' in value:
                    deposit_match = re.search(r'([\d\.]+)', value)
                    if deposit_match:
                        pricing.deposit_months = float(deposit_match.group(1))
                elif '礼金' in header and 'ヶ月分' in value:
                    key_money_match = re.search(r'([\d\.]+)', value)
                    if key_money_match:
                        pricing.key_money_months = float(key_money_match.group(1))

        car_space_table = details_table.find_next('table')
        if car_space_table:
            rows = car_space_table.select('tbody > tr')
            for row in rows:
                th = row.find('th')
                td = row.find('td')
                if th and td:
                    header = th.get_text(strip=True)
                    if '車室サイズ' in header:
                        size_text = td.get_text(separator=' ', strip=True)
                        length_match = re.search(r'全長：([\d\.-]+)', size_text)
                        if length_match and length_match.group(1) != '-':
                            dimensions.length_m = float(length_match.group(1))
                        width_match = re.search(r'全幅：([\d\.-]+)', size_text)
                        if width_match and width_match.group(1) != '-':
                            dimensions.width_m = float(width_match.group(1))
                        height_match = re.search(r'全高：([\d\.-]+)', size_text)
                        if height_match and height_match.group(1) != '-':
                            dimensions.height_m = float(height_match.group(1))

        if address and pricing.monthly_fee:
            lots.append(ParkingLot(
                url=url, name=name, address=address, pricing=pricing,
                dimensions=dimensions, amenities=amenities
            ))

        return lots
