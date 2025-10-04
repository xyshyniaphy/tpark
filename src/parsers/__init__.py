from urllib.parse import urlparse
from src.parsers.carparking_jp import CarParkingJpParser

# A mapping from domain to parser class
PARSER_REGISTRY = {
    'www.carparking.jp': CarParkingJpParser,
    'carparking.jp': CarParkingJpParser,
}

def get_parser(url: str):
    """
    Returns the appropriate parser for a given URL.
    """
    domain = urlparse(url).netloc
    return PARSER_REGISTRY.get(domain)
