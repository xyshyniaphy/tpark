"""
Geocoding and distance calculation utilities.

This module provides functions to convert place names to GPS coordinates (geocoding),
parse coordinate strings, and calculate the distance between two points.
It uses the geopy library.

Example:
    >>> from src.geocoding import geocode_location, calculate_distance
    >>> shibuya_station = geocode_location("Shibuya Station, Tokyo")
    >>> shinjuku_station = geocode_location("Shinjuku Station, Tokyo")
    >>> if shibuya_station and shinjuku_station:
    ...     distance = calculate_distance(shibuya_station, shinjuku_station)
    ...     print(f"Distance: {distance:.2f} km")
    Distance: 3.41 km
"""

import re
from typing import Optional, Tuple

from geopy.distance import geodesic
from geopy.geocoders import Nominatim

from src.utils import APP_NAME

# ==============================================================================
# FUNCTIONS
# ==============================================================================

def geocode_location(place_name: str) -> Optional[Tuple[float, float]]:
    """
    Convert a place name to latitude and longitude coordinates.

    Args:
        place_name: The name of the place to geocode (e.g., "Tokyo Tower").

    Returns:
        A tuple of (latitude, longitude), or None if not found.
    """
    try:
        geolocator = Nominatim(user_agent=APP_NAME)
        location = geolocator.geocode(place_name)
        if location:
            return (location.latitude, location.longitude)
    except Exception as e:
        print(f"Error during geocoding for '{place_name}': {e}")
    return None

def calculate_distance(coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
    """
    Calculate the distance in kilometers between two GPS coordinates.

    Args:
        coord1: The first coordinate (latitude, longitude).
        coord2: The second coordinate (latitude, longitude).

    Returns:
        The distance in kilometers.
    """
    return geodesic(coord1, coord2).kilometers

def parse_coordinates(input_str: str) -> Optional[Tuple[float, float]]:
    """
    Parse a string containing latitude and longitude.

    The string can be in various formats, e.g., "35.6628, 139.6983".

    Args:
        input_str: The string to parse.

    Returns:
        A tuple of (latitude, longitude), or None if parsing fails.
    """
    # Regex to find floating point numbers, allowing for negative values
    match = re.findall(r"[-+]?\d*\.\d+|[-+]?\d+", input_str)
    
    if len(match) == 2:
        try:
            lat = float(match[0])
            lon = float(match[1])
            # Basic validation for lat/lon ranges
            if -90 <= lat <= 90 and -180 <= lon <= 180:
                return (lat, lon)
        except ValueError:
            return None
    return None
