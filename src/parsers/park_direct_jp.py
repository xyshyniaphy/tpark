# 必要なライブラリのインストールコマンド
# pip install beautifulsoup4

import re
from typing import List, Optional
from bs4 import BeautifulSoup

# 注意: 以下のモデルとベースクラスは、ユーザーの既存のプロジェクト構造に
# 基づいていると仮定します。必要に応じてパスを調整してください。
from src.models import ParkingLot, ParkingPricing
from src.parsers.base_parser import BaseParser


class ParkDirectJpParser(BaseParser):
    """
    park-direct.jpのページを解析するためのパーサークラス。

    このパーサーは、駐車場の「詳細ページ」と「一覧ページ」の両方を処理できます。
    parseメソッドは、与えられたページのHTML構造を分析し、適切な内部メソッドを呼び出して
    駐車場情報を抽出します。
    """

    def parse(self, soup: BeautifulSoup, url: str) -> List[ParkingLot]:
        """
        park-direct.jpのHTMLコンテンツを解析し、駐車場情報のリストを返します。

        ページのタイプ（詳細ページか一覧ページか）を自動的に判別し、
        最適な解析ロジックを適用します。

        Args:
            soup (BeautifulSoup): 解析対象のBeautifulSoupオブジェクト。
            url (str): 解析対象のページのURL。

        Returns:
            List[ParkingLot]: 抽出された駐車場情報のリスト。
        """
        parking_lots: List[ParkingLot] = []

        # ページタイプを判定し、適切なパーサーメソッドを呼び出す
        if self._is_detail_page(soup):
            # 詳細ページの場合、メインの駐車場情報をまず取得する
            main_lot = self._parse_detail_page(soup, url)
            if main_lot:
                parking_lots.append(main_lot)
            # 詳細ページ下部にある「近くの駐車場」リストも追加で取得する
            parking_lots.extend(self._parse_nearby_lots(soup, url))
        elif self._is_list_page(soup):
            # 一覧ページの場合、リストからすべての駐車場情報を取得する
            parking_lots.extend(self._parse_list_page(soup, url))
        else:
            # どちらのタイプとも判定できなかった場合、フォールバックとして
            # 「近くの駐車場」セクションが存在するか試みる
            parking_lots.extend(self._parse_nearby_lots(soup, url))

        return parking_lots

    def _is_detail_page(self, soup: BeautifulSoup) -> bool:
        """
        与えられたsoupオブジェクトが駐車場の「詳細ページ」であるかを判定します。

        判定ロジック:
        ページ内に「区画一覧」という見出し(h2)が存在するかどうかで判断します。
        これは詳細ページに特有の要素です。

        Args:
            soup (BeautifulSoup): 判定対象のBeautifulSoupオブジェクト。

        Returns:
            bool: 詳細ページである場合はTrue、そうでない場合はFalse。
        """
        return soup.find("h2", string="区画一覧") is not None

    def _is_list_page(self, soup: BeautifulSoup) -> bool:
        """
        与えられたsoupオブジェクトが駐車場の「一覧ページ」であるかを判定します。

        判定ロジック:
        ページのメイン見出し(h1)に「を検索」という文字列が含まれるかで判断します。
        これは市区町村などの単位で検索した結果ページの特徴です。

        Args:
            soup (BeautifulSoup): 判定対象のBeautifulSoupオブジェクト。

        Returns:
            bool: 一覧ページである場合はTrue、そうでない場合はFalse。
        """
        h1 = soup.find("h1")
        return h1 is not None and "を検索" in h1.get_text()

    def _extract_price(self, text: str) -> Optional[int]:
        """
        価格情報を含む文字列から数値の月額料金を抽出するヘルパー関数。

        例: "月額59,400円(税込)" -> 59400
        価格が "---" の場合はNoneを返します。

        Args:
            text (str): 解析対象の価格文字列。

        Returns:
            Optional[int]: 抽出された価格の整数値。抽出できない場合はNone。
        """
        if "---" in text:
            return None
        
        # 正規表現で "〇〇円" の形式から数値部分を抽出
        match = re.search(r"([\d,]+)円", text)
        if match:
            try:
                # 抽出した文字列からカンマを除去し、整数に変換
                return int(match.group(1).replace(",", ""))
            except (ValueError, IndexError):
                # 変換に失敗した場合はNoneを返す
                return None
        return None

    def _parse_detail_page(self, soup: BeautifulSoup, url: str) -> Optional[ParkingLot]:
        """
        駐車場の「詳細ページ」からメインの駐車場情報を抽出します。

        Args:
            soup (BeautifulSoup): 詳細ページのBeautifulSoupオブジェクト。
            url (str): 詳細ページのURL。

        Returns:
            Optional[ParkingLot]: 抽出された駐車場情報。失敗した場合はNone。
        """
        try:
            name_tag = soup.find("h1")
            name = name_tag.get_text(strip=True) if name_tag else "N/A"

            address_tag = soup.find("address")
            address = address_tag.get_text(strip=True) if address_tag else "N/A"

            pricing = None
            # 「区画一覧」セクションから価格情報を探す
            lots_section = soup.find("h2", string="区画一覧")
            if lots_section:
                # 「月額使用料」というヘッダーテキストを持つdivを探す
                monthly_fee_header = lots_section.find_next("div", text="月額使用料")
                if monthly_fee_header:
                    # ヘッダーの兄弟要素に価格情報が含まれる構造を想定
                    price_container = monthly_fee_header.find_next_sibling("div")
                    if price_container:
                        # 最初の<p>タグに価格が入っていると仮定
                        price_p_tag = price_container.find("p")
                        if price_p_tag:
                            price_text = price_p_tag.get_text(strip=True)
                            # "円"を補完してヘルパー関数に渡し、価格を抽出
                            price_value = self._extract_price(price_text + "円")
                            if price_value is not None:
                                pricing = ParkingPricing(monthly_fee=price_value)

            lot_data = {"name": name, "address": address, "url": url}
            if pricing:
                lot_data["pricing"] = pricing

            return ParkingLot(**lot_data)
        except Exception:
            # パース中に何らかのエラーが発生した場合でも、プログラムを停止させずにNoneを返す
            return None

    def _parse_list_page(self, soup: BeautifulSoup, url: str) -> List[ParkingLot]:
        """
        駐車場の「一覧ページ」からすべての駐車場情報を抽出します。

        Args:
            soup (BeautifulSoup): 一覧ページのBeautifulSoupオブジェクト。
            url (str): 一覧ページのURL。

        Returns:
            List[ParkingLot]: 抽出された駐車場情報のリスト。
        """
        parking_lots = []
        # 駐車場リストの各項目へのリンク(<a>)をCSSセレクタで取得する。
        # これにより、ページ内の無関係な<h3>タグを無視できる。
        lot_links = soup.select("div > h3 > a")
        
        for link_tag in lot_links:
            try:
                # <a>タグの親である<h3>タグを取得
                header = link_tag.parent
                # さらに親を辿り、駐車場情報全体を囲むコンテナ要素を取得
                lot_container = header.find_parent("div").find_parent("div")
                if not lot_container:
                    continue

                name = link_tag.get_text(strip=True)

                address_tag = header.find_next_sibling("div")
                address = address_tag.get_text(strip=True) if address_tag else "N/A"

                pricing = None
                # コンテナ内から最初の有効な価格情報を探す
                price_element = lot_container.find("div", text=re.compile(r"月額"))
                if price_element:
                    price_text = price_element.get_text(strip=True)
                    price_value = self._extract_price(price_text)
                    if price_value is not None:
                        pricing = ParkingPricing(monthly_fee=price_value)

                lot_data = {"name": name, "address": address, "url": url}
                if pricing:
                    lot_data["pricing"] = pricing

                parking_lots.append(ParkingLot(**lot_data))
            except Exception:
                # 特定の項目でパースエラーが起きても、次の項目の処理を続ける
                continue
            
        return parking_lots

    def _parse_nearby_lots(self, soup: BeautifulSoup, url: str) -> List[ParkingLot]:
        """
        詳細ページ下部の「近くの月極駐車場」セクションから駐車場情報を抽出します。
        元のコードを改善し、より堅牢な要素特定方法を使用しています。

        Args:
            soup (BeautifulSoup): 解析対象のBeautifulSoupオブジェクト。
            url (str): 解析対象のページのURL。

        Returns:
            List[ParkingLot]: 抽出された駐車場情報のリスト。
        """
        parking_lots = []
        nearby_section = soup.find("h2", string="近くの月極駐車場")
        if not nearby_section:
            return []

        # <h2>の次の<div>がリスト全体のコンテナ
        main_container = nearby_section.find_next_sibling("div")
        if not main_container:
            return []

        # コンテナ直下の子要素<div>が各駐車場の情報ブロック
        for lot_container in main_container.find_all("div", recursive=False):
            name_tag = lot_container.find("h2")
            if not name_tag:
                continue
            
            name = name_tag.get_text(strip=True)

            # 住所は<h2>タグの直前の兄弟<div>タグにある
            address_tag = name_tag.find_previous_sibling("div")
            address = address_tag.get_text(strip=True) if address_tag else "N/A"

            pricing = None
            # 価格情報を含む要素をテキスト内容で柔軟に検索
            price_element = lot_container.find("div", text=re.compile(r"月額"))
            if price_element:
                price_text = price_element.get_text(strip=True)
                price_value = self._extract_price(price_text)
                if price_value is not None:
                    pricing = ParkingPricing(monthly_fee=price_value)
            
            lot_data = {"name": name, "address": address, "url": url}
            if pricing:
                lot_data["pricing"] = pricing

            parking_lots.append(ParkingLot(**lot_data))
            
        return parking_lots