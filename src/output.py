"""
Markdown output generation for the Tokyo Parking Crawler.

This module provides functions to generate a formatted Markdown report
from the list of ranked parking lots. The report includes a summary table,
detailed sections for the top lots, and metadata about the search.

Example:
    >>> from src.models import ParkingLot
    >>> from src.output import generate_markdown_output
    >>> from src.utils import DEFAULT_CONFIG
    >>> lots = [ParkingLot(url="a", name="A", score=95, address="Tokyo") ]
    >>> markdown = generate_markdown_output(lots, "Shibuya", DEFAULT_CONFIG, {})
    >>> "# Parking Results for Shibuya" in markdown
    True
"""

from typing import Any, Dict, List, Optional

from src.models import ParkingLot
from src.utils import format_time_duration, truncate_text

# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def _format_dimension(value: Optional[float]) -> str:
    return f"{value:.2f}m" if value is not None else "N/A"

def _format_price(value: Optional[int]) -> str:
    return f"{value:,} JPY" if value is not None else "N/A"

# ==============================================================================
# MARKDOWN GENERATION FUNCTIONS
# ==============================================================================

def generate_table(parking_lots: List[ParkingLot]) -> str:
    """Generate a Markdown table of the top parking lots."""
    if not parking_lots:
        return "No suitable parking lots found.\n"

    header = "| Rank | Score | Name | Address | Distance | Price (Monthly) |\n"
    separator = "|:----:|:-----:|:-----|:--------|:--------:|:---------------:|\n"
    body = ""

    for i, lot in enumerate(parking_lots):
        rank = i + 1
        name = truncate_text(lot.name, 40)
        address = truncate_text(lot.address or "N/A", 50)
        distance = f"{lot.distance_km:.2f} km" if lot.distance_km is not None else "N/A"
        price = _format_price(lot.pricing.monthly_fee)
        body += f"| {rank} | {lot.score:.1f} | [{name}]({lot.url}) | {address} | {distance} | {price} |\n"

    return header + separator + body

def format_parking_lot_detail(lot: ParkingLot, rank: int, config: Dict[str, Any]) -> str:
    """Format a detailed section for a single parking lot."""
    details = f"### {rank}. {lot.name}\n\n"
    details += f"- **Overall Score**: {lot.score:.1f}/100\n"
    details += f"- **URL**: [View Listing]({lot.url})\n\n"

    details += "**Location & Dimensions**\n"
    details += f"- Address: {lot.address or 'N/A'}\n"
    details += f"- Distance: {lot.distance_km:.2f} km\n" if lot.distance_km is not None else ""
    details += f"- Dimensions (L x W x H): {_format_dimension(lot.dimensions.length_m)} x {_format_dimension(lot.dimensions.width_m)} x {_format_dimension(lot.dimensions.height_m)}\n\n"

    details += "**Pricing**\n"
    details += f"- Monthly Fee: {_format_price(lot.pricing.monthly_fee)}\n"
    details += f"- Deposit: {lot.pricing.deposit_months} months\n" if lot.pricing.deposit_months is not None else ""
    details += f"- Key Money: {lot.pricing.key_money_months} months\n\n" if lot.pricing.key_money_months is not None else ""

    details += "**Score Breakdown**\n"
    breakdown = lot.score_breakdown
    details += f"- Dimension Fit: {breakdown.dimension_score:.1f}%\n"
    details += f"- Price: {breakdown.price_score:.1f}%\n"
    details += f"- Distance: {breakdown.distance_score:.1f}%\n"
    details += f"- Amenities: {breakdown.amenity_score:.1f}%\n\n"
    
    return details

def generate_detailed_section(parking_lots: List[ParkingLot], top_n: int, config: Dict[str, Any]) -> str:
    """Generate the detailed view for the top N parking lots."""
    if not parking_lots:
        return ""
    
    section = "---\n## 💎 Top Parking Lots: Detailed View\n\n"
    for i, lot in enumerate(parking_lots[:top_n]):
        section += format_parking_lot_detail(lot, i + 1, config)
        if i < top_n - 1:
            section += "---\n"
            
    return section

def generate_summary(parking_lots: List[ParkingLot], config: Dict[str, Any], metadata: Dict[str, Any]) -> str:
    """Generate a summary section with metadata about the run."""
    total_lots = len(parking_lots)
    duration = metadata.get("total_duration_s", 0)
    
    summary = "---\n## 📊 Summary & Metadata\n\n"
    summary += f"- **Total Suitable Lots Found**: {total_lots}\n"
    summary += f"- **Search Duration**: {format_time_duration(duration)}\n"
    summary += f"- **Searched Location**: {metadata.get('place_name', 'N/A')}\n"
    summary += f"- **Target Coordinates**: {metadata.get('target_coordinates', 'N/A')}\n"
    summary += f"- **Vehicle Spec (L x W x H)**: {config['vehicle_spec']['length_m']}m x {config['vehicle_spec']['width_m']}m x {config['vehicle_spec']['height_m']}m\n"
    
    return summary

# ==============================================================================
# MAIN OUTPUT FUNCTION
# ==============================================================================

def generate_markdown_output(
    parking_lots: List[ParkingLot],
    place_name: str,
    config: Dict[str, Any],
    metadata: Dict[str, Any],
) -> str:
    """
    Generate the full Markdown report.

    Args:
        parking_lots: The list of ranked ParkingLot objects.
        place_name: The name of the location searched.
        config: The application configuration dictionary.
        metadata: A dictionary of metadata about the run.

    Returns:
        The complete Markdown report as a string.
    """
    title = f"# 🚗 Parking Results for {place_name}\n\n"
    table_section = generate_table(parking_lots)
    detailed_section = generate_detailed_section(parking_lots, config["output_top_n"], config)
    summary_section = generate_summary(parking_lots, config, metadata)

    return title + table_section + detailed_section + summary_section

def save_output(markdown: str, output_file: str) -> None:
    """
    Save the Markdown content to a file.

    Args:
        markdown: The Markdown content to save.
        output_file: The path to the output file.
    """
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(markdown)
        print(f"Results saved to {output_file}")
    except IOError as e:
        print(f"Error saving output file: {e}")
