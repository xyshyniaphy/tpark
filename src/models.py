"""
Data models for the Tokyo Parking Crawler.

This module defines Pydantic models for representing parking lot data,
ensuring type safety and validation throughout the application.
It also defines the TypedDict for the LangGraph workflow state.

Example:
    >>> from src.models import ParkingLot, ParkingDimensions
    >>> dimensions = ParkingDimensions(length_m=5.0, width_m=2.0, height_m=2.2)
    >>> parking_lot = ParkingLot(url="http://example.com", name="My Parking", dimensions=dimensions)
    >>> print(parking_lot.dimensions.length_m)
    5.0
"""

from typing import Any, Dict, List, Optional, TypedDict

from pydantic import BaseModel, Field


# ==============================================================================
# PYDANTIC MODELS
# ==============================================================================


class ParkingDimensions(BaseModel):
    """Dimensions of a parking space."""

    length_m: Optional[float] = Field(None, description="Length of the parking space in meters.")
    width_m: Optional[float] = Field(None, description="Width of the parking space in meters.")
    height_m: Optional[float] = Field(None, description="Height of the parking space in meters.")


class ParkingAmenities(BaseModel):
    """Amenities available at the parking lot."""

    is_24_7: bool = Field(False, description="Whether the parking is accessible 24/7.")
    has_ev_charger: bool = Field(False, description="Whether the parking has an EV charger.")
    is_covered: bool = Field(False, description="Whether the parking is covered.")


class ParkingPricing(BaseModel):
    """Pricing information for the parking lot."""

    monthly_fee: Optional[int] = Field(None, description="Monthly fee in JPY.")
    deposit_months: Optional[float] = Field(None, description="Deposit in number of months' rent.")
    key_money_months: Optional[float] = Field(None, description="Key money in number of months' rent.")


class ParkingScoreBreakdown(BaseModel):
    """Breakdown of the calculated parking score."""

    dimension_score: float = 0.0
    price_score: float = 0.0
    distance_score: float = 0.0
    amenity_score: float = 0.0


class ParkingLot(BaseModel):
    """Represents a single parking lot listing."""

    url: str = Field(..., description="URL of the parking lot listing.")
    name: str = Field(..., description="Name of the parking lot.")
    address: Optional[str] = Field(None, description="Address of the parking lot.")
    coordinates: Optional[str] = Field(None, description="GPS coordinates (lat, lon).")
    distance_km: Optional[float] = Field(None, description="Distance from the target location in kilometers.")

    dimensions: ParkingDimensions = Field(default_factory=ParkingDimensions)
    amenities: ParkingAmenities = Field(default_factory=ParkingAmenities)
    pricing: ParkingPricing = Field(default_factory=ParkingPricing)

    score: float = 0.0
    score_breakdown: ParkingScoreBreakdown = Field(default_factory=ParkingScoreBreakdown)

    raw_text: Optional[str] = Field(None, description="Raw extracted text from the webpage.")


# ==============================================================================
# WORKFLOW STATE
# ==============================================================================


class WorkflowState(TypedDict):
    """State dictionary for the LangGraph workflow."""

    place_name: str
    config: Dict[str, Any]
    system_prompt: str
    target_coordinates: Optional[tuple[float, float]]
    search_results: List[Dict[str, Any]]
    scraped_content: List[Dict[str, Any]]
    extracted_data: List[ParkingLot]
    ranked_lots: List[ParkingLot]
    final_markdown: str
    error: Optional[str]
