"""
Scoring and ranking logic for parking lots.

This module provides functions to calculate a suitability score for each
parking lot based on dimensions, price, distance, and amenities. It also
includes a function to rank the lots based on their final scores.

Example:
    >>> from src.models import ParkingLot
    >>> from src.scoring import rank_parking_lots
    >>> lots = [ParkingLot(url="a", name="A", score=80), ParkingLot(url="b", name="B", score=95)]
    >>> ranked = rank_parking_lots(lots)
    >>> print(ranked[0].name)
    B
"""

from typing import Any, Dict, List, Optional, Tuple

from src.models import ParkingLot, ParkingDimensions

# ==============================================================================
# SCORING FUNCTIONS
# ==============================================================================

def calculate_dimension_score(dimensions: ParkingDimensions, vehicle: Dict[str, float]) -> float:
    """Calculate a score based on how well the vehicle fits."""
    if not all([dimensions.length_m, dimensions.width_m, dimensions.height_m]):
        return 0.5  # Neutral score if dimensions are unknown

    if (
        dimensions.length_m >= vehicle["length_m"] and
        dimensions.width_m >= vehicle["width_m"] and
        dimensions.height_m >= vehicle["height_m"]
    ):
        return 1.0  # Perfect fit
    return 0.0  # Does not fit

def calculate_price_score(price: Optional[int], max_price: int) -> float:
    """Calculate a score based on the monthly price."""
    if price is None:
        return 0.5  # Neutral score if price is unknown

    if price > max_price:
        return 0.0
    
    # Inverse linear scale
    return 1.0 - (price / max_price)

def calculate_distance_score(distance: Optional[float], max_distance: float) -> float:
    """Calculate a score based on the distance from the target."""
    if distance is None:
        return 0.5  # Neutral score if distance is unknown

    if distance > max_distance:
        return 0.0
        
    # Inverse linear scale
    return 1.0 - (distance / max_distance)

def calculate_amenity_score(amenities: Dict[str, bool]) -> float:
    """Calculate a score based on available amenities."""
    score = 0.5  # Start with a neutral score
    if amenities.get("is_24_7"): score += 0.2
    if amenities.get("has_ev_charger"): score += 0.1 # Lower weight for EV
    if not amenities.get("is_covered"): score += 0.2 # Bonus for outdoor
    return min(1.0, score)

# ==============================================================================
# MAIN SCORING AND RANKING
# ==============================================================================

def calculate_parking_score(
    parking_lot: ParkingLot,
    vehicle_spec: Dict[str, float],
    target_coords: Optional[Tuple[float, float]],
    config: Dict[str, Any],
) -> ParkingLot:
    """
    Calculate the overall score for a single parking lot.

    Args:
        parking_lot: The ParkingLot object to score.
        vehicle_spec: The vehicle dimension specifications.
        target_coords: The target GPS coordinates.
        config: The application configuration dictionary.

    Returns:
        The same ParkingLot object, updated with the new score and breakdown.
    """
    weights = config["scoring_weights"]

    # Calculate individual scores
    dim_score = calculate_dimension_score(parking_lot.dimensions, vehicle_spec)
    price_score = calculate_price_score(parking_lot.pricing.monthly_fee, config["max_price"])
    dist_score = calculate_distance_score(parking_lot.distance_km, config["max_distance_km"])
    amenity_score = calculate_amenity_score(parking_lot.amenities.dict())

    # Apply weights
    total_score = (
        dim_score * weights["dimension"] +
        price_score * weights["price"] +
        dist_score * weights["distance"] +
        amenity_score * weights["amenity"]
    ) * 100

    # Update the parking lot object
    parking_lot.score = round(total_score, 2)
    parking_lot.score_breakdown.dimension_score = round(dim_score * 100, 1)
    parking_lot.score_breakdown.price_score = round(price_score * 100, 1)
    parking_lot.score_breakdown.distance_score = round(dist_score * 100, 1)
    parking_lot.score_breakdown.amenity_score = round(amenity_score * 100, 1)

    return parking_lot

def rank_parking_lots(lots: List[ParkingLot]) -> List[ParkingLot]:
    """
    Rank a list of parking lots by their score in descending order.

    Args:
        lots: A list of ParkingLot objects.

    Returns:
        A new list of ParkingLot objects sorted by score.
    """
    return sorted(lots, key=lambda lot: lot.score, reverse=True)
