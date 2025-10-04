
import json
from bs4 import BeautifulSoup
import re

def parse_carparking_jp(html_content):
    """
    Parses parking lot information from carparking.jp HTML content.
    It specifically looks for the application/ld+json script tag.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    script_tag = soup.find('script', {'type': 'application/ld+json'})
    if not script_tag:
        return None

    try:
        data = json.loads(script_tag.string)
        return data
    except (json.JSONDecodeError, TypeError):
        return None

def parse_at_parking_jp(html_content):
    """
    Parses parking lot information from at-parking.jp HTML content.
    It specifically looks for the latlngList javascript variable.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    scripts = soup.find_all('script')
    all_data = []
    for script in scripts:
        if script.string and 'latlngList' in script.string:
            matches = re.findall(r"latlngList\[\d+\] = ({.*?});", script.string, re.DOTALL)
            for match in matches:
                json_like_string = match
                json_string = json_like_string.replace("'", '"')
                json_string = re.sub(r'([{,]\s*)(\w+)(\s*:)', r'\1"\2"\3', json_string)

                try:
                    data = json.loads(json_string)
                    all_data.append(data)
                except json.JSONDecodeError as e:
                    print(f"Failed to decode at-parking.jp JSON: {e}")
                    print(f"Original string: {json_like_string}")
                    print(f"Processed string: {json_string}")

    return all_data if all_data else None

def parse_athome_co_jp(html_content):
    """
    Parses parking lot information from athome.co.jp HTML content.
    It specifically looks for the script tag with id "serverApp-state".
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    script_tag = soup.find('script', {'id': 'serverApp-state'})
    if not script_tag:
        return None
    try:
        data = json.loads(script_tag.string)
        for key in data:
            if "bukken/list/first-view" in key:
                body = json.loads(data[key]["body"])
                if "data" in body and "bukkenData" in body["data"] and "bukkenList" in body["data"]["bukkenData"]:
                    return body["data"]["bukkenData"]["bukkenList"]
    except (json.JSONDecodeError, TypeError):
        return None
    return None

def parse_park_direct_jp(html_content):
    """
    Parses parking lot information from park-direct.jp HTML content.
    It specifically looks for the script tag with id "__NEXT_DATA__".
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    script_tag = soup.find('script', {'id': '__NEXT_DATA__'})
    if not script_tag:
        return None
    try:
        data = json.loads(script_tag.string)
        if "props" in data and "pageProps" in data["props"] and "parkingLot" in data["props"]["pageProps"]:
            return data["props"]["pageProps"]["parkingLot"]
    except (json.JSONDecodeError, TypeError):
        return None
    return None

def parse_html(file_path):
    """
    Parses a single HTML file and returns the parking lot information.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    if 'carparking.jp' in html_content:
        return parse_carparking_jp(html_content)
    if 'at-parking.jp' in html_content:
        return parse_at_parking_jp(html_content)
    if 'athome.co.jp' in html_content:
        return parse_athome_co_jp(html_content)
    if 'park-direct.jp' in html_content or 'parkdirect.jp' in html_content:
        return parse_park_direct_jp(html_content)
    
    # Fallback if no site is detected
    print(f"--- No specific site detected for {file_path}, trying all parsers ---")
    data = parse_carparking_jp(html_content)
    if data:
        return data
    data = parse_at_parking_jp(html_content)
    if data:
        return data
    data = parse_athome_co_jp(html_content)
    if data:
        return data
    data = parse_park_direct_jp(html_content)
    if data:
        return data
        
    print(f"--- No parser for {file_path} ---")
    return None

if __name__ == '__main__':
    import glob
    import json
    import os

    # Change to the script's directory to resolve relative paths correctly
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    files = glob.glob('../webpages/*.html')
    all_data = []
    for file in files:
        print(f"--- Parsing {file} ---")
        data = parse_html(file)
        if data:
            print(f"--- Found data in {file} ---")
            if isinstance(data, list):
                all_data.extend(data)
            else:
                all_data.append(data)

    print(json.dumps(all_data, indent=4, ensure_ascii=False))
