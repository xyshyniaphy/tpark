# test_parse.py
import json
import os
from bs4 import BeautifulSoup
from src.parsers import get_parser
from src.scraper import WebScraper

def main():
    """
    This script tests the implemented parsers against all HTML files
    in the 'webpages' directory. It processes each file, attempts to parse it
    using the appropriate parser based on the domain name in the filename,
    and writes the results to 'parse_test.md'.
    """
    webpages_dir = "webpages"
    output_file = "parse_test.md"

    try:
        html_files = [f for f in os.listdir(webpages_dir) if f.endswith(".html")]
    except FileNotFoundError:
        print(f"Error: The directory '{webpages_dir}' was not found.")
        return

    with open(output_file, 'w', encoding='utf-8') as md_file:
        md_file.write("# Parser Test Results\n\n")

        for html_file in html_files:
            file_path = os.path.join(webpages_dir, html_file)
            
            # Extract domain from filename
            try:
                domain = html_file.split('_')[0]
                # Construct a placeholder URL with the correct domain
                url = f"https://{domain}/placeholder"
            except IndexError:
                md_file.write(f"## Parsing: `{html_file}`\n\n")
                md_file.write(f"Could not extract domain from filename.\n\n")
                continue

            md_file.write(f"## Parsing: `{html_file}` (Domain: {domain})\n\n")

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    html_content = f.read()
            except IOError as e:
                md_file.write(f"Error reading file: {e}\n\n")
                continue

            scraper = WebScraper(config={})
            cleaned_html = scraper.clean_html(html_content)
            
            soup = BeautifulSoup(cleaned_html, 'lxml')

            Parser = get_parser(url)
            if not Parser:
                md_file.write(f"No parser found for domain: {domain}\n\n")
                continue

            parser = Parser()
            
            try:
                parking_lots = parser.parse(soup, url)
            except Exception as e:
                md_file.write(f"An error occurred during parsing: {e}\n\n")
                continue

            if parking_lots:
                for lot in parking_lots:
                    md_file.write("```json\n")
                    md_file.write(json.dumps(lot.model_dump(), indent=4, ensure_ascii=False))
                    md_file.write("\n```\n\n")
            else:
                md_file.write("No parking lots found.\n\n")

    print(f"Parsing complete. Results are in '{output_file}'.")

if __name__ == "__main__":
    main()
