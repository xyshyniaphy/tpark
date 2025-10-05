# 必要なライブラリのインストールコマンド
# pip install beautifulsoup4 pydantic

import re
import copy
from typing import List
from urllib.parse import urljoin

from bs4 import BeautifulSoup

# 注意: 以下のモデルとベースクラスは、ユーザーの既存のプロジェクト構造に
# 基づいていると仮定します。
from src.models import (
    ParkingLot,
    ParkingPricing,
    ParkingDimensions,
    ParkingAmenities,
)
from src.parsers.base_parser import BaseParser


class CarParkingJpParser(BaseParser):
    """
    carparking.jp の駐車場リストページおよび詳細ページを解析するためのパーサー。

    このクラスは、与えられたHTMLコンテンツがリストページか詳細ページかを自動で判別し、
    適切な解析メソッドを呼び出します。抽出されたデータは、指定されたPydanticモデルに
    格納されます。
    """

    def parse(self, soup: BeautifulSoup, url: str) -> List[ParkingLot]:
        """
        HTMLコンテンツを解析し、ParkingLotオブジェクトのリストを返します。

        Args:
            soup (BeautifulSoup): 解析対象のBeautifulSoupオブジェクト。
            url (str): 解析対象ページのURL。相対URLを解決するために使用します。

        Returns:
            List[ParkingLot]: 抽出された駐車場情報のリスト。
        """
        # 詳細ページ特有の「詳細情報」という見出しがあるかチェック
        if self._is_detail_page(soup):
            return self._parse_detail_page(soup, url)

        # リストページは解析しない
        return []

    def _is_detail_page(self, soup: BeautifulSoup) -> bool:
        """
        ページが駐車場の詳細ページであるかを判定します。
        <section class="parking-detail"> の存在を基準とします。
        """
        return bool(soup.find("section", class_="parking-detail"))

    def _is_list_page(self, soup: BeautifulSoup) -> bool:
        """
        ページが駐車場のリストページであるかを判定します。
        <p class="count"> の存在を基準とします。
        """
        return bool(soup.find("p", class_="count"))

    def _parse_detail_page(self, soup: BeautifulSoup, url: str) -> List[ParkingLot]:
        """
        駐車場の詳細ページを解析します。
        ページには複数の車室情報が含まれる場合があり、その場合はそれぞれを
        個別のParkingLotオブジェクトとして返します。
        """
        lots: List[ParkingLot] = []
        try:
            parking_details_section = soup.find("section", class_="parking-detail")
            if not parking_details_section:
                return []

            name_tag = soup.find("h2")
            name = name_tag.get_text(strip=True) if name_tag else "名称不明"

            # 駐車場全体の共通情報を格納するベースオブジェクトを作成
            base_lot = ParkingLot(
                url=url,
                name=name,
                # addressは後で設定
                # pricing, dimensions, amenitiesはデフォルトファクトリで初期化
            )

            details_table = parking_details_section.find("table", class_="parking-table")
            if not details_table:
                return []

            # 共通情報テーブルからデータを抽出し、base_lotを更新
            rows = details_table.select("tbody > tr")
            for row in rows:
                th = row.find("th")
                td = row.find("td")
                if not (th and td):
                    continue

                header = th.get_text(strip=True)
                value = td.get_text(strip=True)

                if "所在地" in header:
                    base_lot.address = value
                elif "賃料" in header:
                    price_match = re.search(r"([\d,]+)円", value)
                    if price_match:
                        base_lot.pricing.monthly_fee = int(
                            price_match.group(1).replace(",", "")
                        )
                elif "利用可能時間" in header and "24時間" in value:
                    base_lot.amenities.is_24_7 = True
                elif "屋内外" in header:
                    if "屋内" in value:
                        base_lot.amenities.is_covered = True
                    elif "屋外" in value:
                        base_lot.amenities.is_covered = False
                elif "保証金" in header and "ヶ月分" in value:
                    deposit_match = re.search(r"([\d\.]+)", value)
                    if deposit_match:
                        base_lot.pricing.deposit_months = float(deposit_match.group(1))
                elif "礼金" in header and "ヶ月分" in value:
                    key_money_match = re.search(r"([\d\.]+)", value)
                    if key_money_match:
                        base_lot.pricing.key_money_months = float(
                            key_money_match.group(1)
                        )

            # 車室ごとの詳細情報を解析
            car_space_container = parking_details_section.find(
                "div", class_="parking-spacelist"
            )
            space_tables = (
                car_space_container.find_all("table")
                if car_space_container
                else []
            )

            if space_tables:
                for table in space_tables:
                    # 共通情報をディープコピーして、車室ごとのデータを作成
                    lot = copy.deepcopy(base_lot)

                    s_rows = table.select("tbody > tr")
                    for s_row in s_rows:
                        th = s_row.find("th")
                        td = s_row.find("td")
                        if not (th and td):
                            continue

                        header = th.get_text(strip=True)

                        if "賃料" in header:
                            value = td.get_text(strip=True)
                            price_match = re.search(r"([\d,]+)\s*円", value)
                            if price_match:
                                lot.pricing.monthly_fee = int(
                                    price_match.group(1).replace(",", "")
                                )
                        elif "車室サイズ" in header:
                            size_text = td.get_text(separator=" ", strip=True)
                            # 全長、全幅、全高を抽出し、mmからmに変換
                            length_match = re.search(r"全長：([\d\.-]+)mm", size_text)
                            if length_match and length_match.group(1) != "-":
                                lot.dimensions.length_m = (
                                    float(length_match.group(1)) / 1000.0
                                )
                            width_match = re.search(r"全幅：([\d\.-]+)mm", size_text)
                            if width_match and width_match.group(1) != "-":
                                lot.dimensions.width_m = (
                                    float(width_match.group(1)) / 1000.0
                                )
                            height_match = re.search(r"全高：([\d\.-]+)mm", size_text)
                            if height_match and height_match.group(1) != "-":
                                lot.dimensions.height_m = (
                                    float(height_match.group(1)) / 1000.0
                                )

                    # 必須情報（住所と賃料）が揃っている場合のみリストに追加
                    if lot.address and lot.pricing.monthly_fee is not None:
                        lots.append(lot)
                return lots

            # 車室ごとのテーブルが見つからなかった場合、基本情報から単一のLotを作成
            if base_lot.address and base_lot.pricing.monthly_fee is not None:
                lots.append(base_lot)

        except Exception as e:
            # 解析中に予期せぬエラーが発生した場合のフォールバック
            # 実際にはロギングライブラリを使用することが望ましい
            print(f"Error parsing detail page {url}: {e}")

        return lots
