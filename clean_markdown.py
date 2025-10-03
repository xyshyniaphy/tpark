import os
import re

def clean_markdown_files():
    """
    Analyzes markdown files in the webpages/ directory, cleans them to extract parking lot information,
    and consolidates the findings into a single markdown file.
    """
    webpages_dir = 'webpages'
    output_file = 'cleaned_parking_info.md'
    
    all_parking_data = []

    price_regex = re.compile(r'(賃料|月額|価格|料金)\s*[:：]?\s*([0-9,]+円)')
    roof_regex = re.compile(r'(屋内外|屋根)\s*[:：]?\s*(屋外|屋内)')

    if not os.path.exists(webpages_dir):
        print(f"Directory not found: {webpages_dir}")
        return

    with open(output_file, 'w', encoding='utf-8') as out_f:
        out_f.write("# Cleaned Parking Lot Information\n\n")

        for filename in os.listdir(webpages_dir):
            if filename.endswith('.md'):
                filepath = os.path.join(webpages_dir, filename)
                with open(filepath, 'r', encoding='utf-8') as md_file:
                    content = md_file.read()
                    
                    # Split content into sections based on horizontal rules
                    sections = content.split('---')
                    
                    for section in sections:
                        price_match = price_regex.search(section)
                        roof_match = roof_regex.search(section)
                        
                        if price_match and roof_match:
                            price = price_match.group(2)
                            roof = roof_match.group(2)
                            all_parking_data.append((filename, price, roof))

        # Write consolidated data
        for filename, price, roof in all_parking_data:
            out_f.write(f"## Source: {filename}\n")
            out_f.write(f"- **Price:** {price}\n")
            out_f.write(f"- **Roof:** {roof}\n\n")

    print(f"Markdown cleaning and consolidation complete. See {output_file}")

if __name__ == '__main__':
    clean_markdown_files()