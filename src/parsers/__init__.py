from urllib.parse import urlparse
from src.parsers.carparking_jp import CarParkingJpParser
from src.parsers.at_parking_jp import AtParkingJpParser
from src.parsers.athome_co_jp import AthomeCoJpParser
from src.parsers.park_direct_jp import ParkDirectJpParser
from src.parsers.tokyo_parking_jp import TokyoParkingJpParser

# A mapping from domain to parser class
PARSER_REGISTRY = {
    'www.carparking.jp': CarParkingJpParser,
    'carparking.jp': CarParkingJpParser,
    'www.at-parking.jp': AtParkingJpParser,
    'www.athome.co.jp': AthomeCoJpParser,
    'www.park-direct.jp': ParkDirectJpParser,
    'www.tokyo-parking.jp': TokyoParkingJpParser,
}

def get_parser(url: str):
    """
    Returns the appropriate parser for a given URL.
    """
    domain = urlparse(url).netloc
    return PARSER_REGISTRY.get(domain)