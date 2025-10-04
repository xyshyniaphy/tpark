import json
from bs4 import BeautifulSoup
from src.parsers import get_parser
from src.scraper import WebScraper

def main():
    html_file = "webpages/0ff49d52746a57e31885aa1f44abeead.html"
    url = "https://www.carparking.jp/parking/3645"

    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()

    scraper = WebScraper(config={})
    cleaned_html = scraper.clean_html(html_content)
    
    soup = BeautifulSoup(cleaned_html, 'lxml')

    Parser = get_parser(url)
    if not Parser:
        print(f"No parser found for URL: {url}")
        return

    parser = Parser()
    parking_lots = parser.parse(soup, url)

    if parking_lots:
        for lot in parking_lots:
            print(json.dumps(lot.model_dump(), indent=4, ensure_ascii=False))
    else:
        print("No parking lots found.")

if __name__ == "__main__":
    main()
