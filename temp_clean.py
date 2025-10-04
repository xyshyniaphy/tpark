from bs4 import BeautifulSoup
from src.scraper import WebScraper

def main():
    html_file = "webpages/www.at-parking.jp_710a143b1712aeeb5c8498d1456876ae.html"

    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()

    scraper = WebScraper(config={})
    cleaned_html = scraper.clean_html(html_content)
    
    print(cleaned_html)

if __name__ == "__main__":
    main()
