import re
from typing import List
from bs4 import BeautifulSoup
from src.models import ParkingLot, ParkingDimensions, ParkingPricing, ParkingAmenities
from src.parsers.base_parser import BaseParser

class AtParkingJpParser(BaseParser):
    """Parser for at-parking.jp pages."""

    def parse(self, soup: BeautifulSoup, url: str) -> List[ParkingLot]:
        """
        Parses the HTML content of a at-parking.jp page.
        It can handle both details and search result pages.
        """
        lots = self._parse_detail_page(soup, url)
        if lots:
            return lots
        return self._parse_search_page(soup, url)

    def _parse_detail_page(self, soup: BeautifulSoup, url: str) -> List[ParkingLot]:
        name_tag = soup.find('span', id='prptName')
        name = name_tag.text if name_tag else None

        if not name:
            return []

        address = self._find_table_value(soup, '駐車場所在地')

        monthly_fee_str = self._find_table_value(soup, '賃料／保証金', 2)
        monthly_fee = self._parse_fee(monthly_fee_str)

        deposit_str = self._find_table_value(soup, '敷金')
        deposit = self._parse_months(deposit_str)

        dimensions_str = self._find_table_value(soup, '駐車場スペック')
        dimensions = self._parse_dimensions(dimensions_str)

        availability_str = self._find_table_value(soup, '利用可能時間')
        is_24_7 = '24時間' in availability_str if availability_str else False

        covered_str = self._find_table_value(soup, '屋内外')
        is_covered = '屋内' in covered_str if covered_str else False

        parking_lot = ParkingLot(
            url=url,
            name=name,
            address=address,
            dimensions=dimensions,
            amenities=ParkingAmenities(is_24_7=is_24_7, is_covered=is_covered),
            pricing=ParkingPricing(monthly_fee=monthly_fee, deposit_months=deposit),
        )

        return [parking_lot]

    def _parse_search_page(self, soup: BeautifulSoup, url: str) -> List[ParkingLot]:
        lots = []
        results_container = soup.find('div', id='srcResult')
        if not results_container:
            return []

        for li in results_container.find_all('li'):
            if not li.find('a') or not li.find('span'):
                continue

            name_tag = li.find('a')
            name = name_tag.text.strip()

            span_tag = li.find('span')
            full_text = span_tag.text.strip()

            if '件' in full_text:
                continue

            parts = full_text.split('/')
            address = parts[0].strip()
            price_str = parts[1].strip() if len(parts) > 1 else None
            monthly_fee = self._parse_fee(price_str)

            lot_url_tag = li.find('a')
            lot_url = lot_url_tag['href'] if lot_url_tag and lot_url_tag.has_attr('href') else url

            parking_lot = ParkingLot(
                url=lot_url,
                name=name,
                address=address,
                pricing=ParkingPricing(monthly_fee=monthly_fee),
            )
            lots.append(parking_lot)
        
        return lots

    def _find_table_value(self, soup: BeautifulSoup, label: str, sibling_index: int = 1) -> str | None:
        label_td = soup.find('td', string=re.compile(label))
        if not label_td:
            return None
        
        value_td = label_td
        for _ in range(sibling_index):
            value_td = value_td.find_next_sibling('td')
            if not value_td:
                return None

        return value_td.get_text(strip=True)

    def _parse_fee(self, fee_str: str | None) -> int | None:
        if not fee_str:
            return None
        # Handles ranges like '38,500 ～ 49,500円' by taking the first number
        fee_str = fee_str.split('～')[0]
        match = re.search(r'[\d,]+', fee_str)
        if match:
            return int(match.group().replace(',', ''))
        return None

    def _parse_months(self, months_str: str | None) -> float | None:
        if not months_str:
            return None
        match = re.search(r'[\d.]+', months_str)
        if match:
            return float(match.group())
        return None

    def _parse_dimensions(self, dim_str: str | None) -> ParkingDimensions:
        dimensions = ParkingDimensions()
        if not dim_str:
            return dimensions

        patterns = {
            'height_m': r'全高\s*([\d,.]+)mm',
            'length_m': r'全長\s*([\d,.]+)mm',
            'width_m': r'全幅\s*([\d,.]+)mm',
        }

        for key, pattern in patterns.items():
            match = re.search(pattern, dim_str)
            if match:
                try:
                    value_mm = float(match.group(1).replace(',', ''))
                    setattr(dimensions, key, value_mm / 1000.0)
                except (ValueError, IndexError):
                    pass
        return dimensions
