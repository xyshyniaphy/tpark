"""
LangGraph workflow orchestration for the Tokyo Parking Crawler.

This module defines the nodes and graph that constitute the main application
logic. It uses LangGraph to create a stateful workflow that proceeds from
configuration and geocoding through searching, scraping, data extraction,
scoring, and finally to output generation.

Example:
    >>> from src.workflow import execute_workflow
    >>> from src.config import load_yaml_env
    >>> config = load_yaml_env()
    >>> result = execute_workflow("Shibuya Station", config)
    >>> print(result['final_markdown'])
"""

import logging
import time
from typing import Any, Dict, List
from urllib.parse import urljoin

from langgraph.graph import StateGraph, END

from src.cache import CacheManager
from src.config import validate_config, load_system_prompt
from src.geocoding import geocode_location, parse_coordinates, calculate_distance
from src.gemini import GeminiExtractor
from src.models import WorkflowState, ParkingLot
from src.output import generate_markdown_output, save_output
from src.scoring import calculate_parking_score, rank_parking_lots
from src.scraper import WebScraper
from src.searxng import SearXNGClient
from src.utils import APP_NAME

# Get the logger for this module
logger = logging.getLogger(APP_NAME)

# ==============================================================================
# WORKFLOW NODES
# ==============================================================================

def node_validate_config(state: WorkflowState) -> WorkflowState:
    """Validate the application configuration."""
    logger.debug("--- Validating configuration ---")
    errors = validate_config(state["config"])
    if errors:
        logger.error(f"Configuration validation failed: {errors}")
        state["error"] = "\n".join(errors)
    else:
        logger.debug("Configuration is valid.")
    return state

def node_load_system_prompt(state: WorkflowState) -> WorkflowState:
    """Load the Gemini system prompt."""
    logger.debug("--- Loading system prompt ---")
    state["system_prompt"] = load_system_prompt("system.md")
    logger.debug(f"System prompt loaded successfully. Length: {len(state['system_prompt'])}")
    return state

def node_geocode_location(state: WorkflowState) -> WorkflowState:
    """Geocode the input place name to get coordinates."""
    place_name = state["place_name"]
    logger.debug(f"--- Geocoding location: {place_name} ---")
    
    coords = parse_coordinates(place_name)
    if coords:
        logger.debug(f"Parsed coordinates directly: {coords}")
    else:
        logger.debug("Could not parse coordinates, attempting to geocode...")
        coords = geocode_location(place_name)
    
    if not coords:
        logger.error(f"Failed to geocode location: {place_name}")
        state["error"] = f"Could not geocode location: {place_name}"
    else:
        logger.debug(f"Geocoded coordinates: {coords}")
        state["target_coordinates"] = coords
        
    return state

def node_searxng_search(state: WorkflowState) -> WorkflowState:
    """Perform a web search using SearXNG."""
    config = state["config"]
    place_name = state["place_name"]
    logger.debug(f"--- Performing SearXNG search for: {place_name} ---")
    
    client = SearXNGClient(config["searxng_instance_url"], config)
    query = client.build_query(place_name, config["search_query_template"])
    logger.debug(f"Constructed search query: {query}")
    
    results = client.search(query, config["max_search_results"])
    state["search_results"] = results
    logger.debug(f"Found {len(results)} search results.")
    return state

def node_scrape_and_cache(state: WorkflowState) -> WorkflowState:
    """Scrape web pages, clean HTML, and cache the cleaned content."""
    config = state["config"]
    place_name = state["place_name"]
    logger.debug(f"--- Scraping, cleaning, and caching HTML for: {place_name} ---")

    scraper = WebScraper(config)
    cache = CacheManager(config["cache_dir"], config["cache_ttl_days"])
    
    scraped_content = []
    processed_urls = set()

    for result in state.get("search_results", []) :
        url = result["url"]
        if url in processed_urls:
            continue

        processed_urls.add(url)
        logger.debug(f"Processing URL: {url}")

        # Check cache first
        cached_html = cache.load_html(url, place_name)
        if cached_html:
            logger.debug(f"Cache hit for {url}. Loading from cache.")
            scraped_content.append({"url": url, "html": cached_html})
            continue

        logger.debug(f"Cache miss for {url}. Fetching from web.")
        html = scraper.fetch(url)
        if not html:
            logger.warning(f"Failed to fetch HTML from {url}.")
            continue
        
        logger.debug(f"Cleaning HTML for {url}")
        cleaned_html = scraper.clean_html(html)

        cache.save_html(url, place_name, cleaned_html)
        scraped_content.append({"url": url, "html": cleaned_html})

    state["scraped_content"] = scraped_content
    logger.debug(f"Finished scraping and cleaning. Total pages processed: {len(scraped_content)}")
    
    # For debugging, save the cleaned HTML to a file
    if scraped_content:
        with open("cleaned_debug.html", "w", encoding="utf-8") as f:
            f.write(scraped_content[0]["html"])
        logger.info("Saved the first cleaned HTML to cleaned_debug.html for debugging.")

    return state

def node_extract_with_gemini(state: WorkflowState) -> WorkflowState:
    """Extract structured data from HTML using Gemini."""
    config = state["config"]
    system_prompt = state["system_prompt"]
    logger.debug("--- Extracting structured data with Gemini ---")
    
    extractor = GeminiExtractor(config, system_prompt)
    extracted_data = []
    
    scraped_content = state.get("scraped_content", [])
    logger.debug(f"Processing {len(scraped_content)} scraped documents with Gemini.")

    for i, content in enumerate(scraped_content):
        url = content["url"]
        html = content["html"]
        logger.debug(f"Extracting from document {i+1}/{len(scraped_content)} (URL: {url}, HTML length: {len(html)})")
        
        try:
            lots = extractor.extract_parking_data(html, url)
            if lots:
                logger.debug(f"Extracted {len(lots)} parking lots from {url}.")
                extracted_data.extend(lots)
            else:
                logger.warning(f"No parking lots extracted from {url}.")
        except Exception as e:
            logger.error(f"An error occurred during Gemini extraction for {url}: {e}", exc_info=True)

    state["extracted_data"] = extracted_data
    logger.debug(f"Finished Gemini extraction. Total lots extracted: {len(extracted_data)}")
    return state

def node_score_and_rank(state: WorkflowState) -> WorkflowState:
    """Score and rank the extracted parking lots."""
    logger.debug("--- Scoring and ranking parking lots ---")
    scored_lots = []
    
    extracted_data = state.get("extracted_data", [])
    target_coords = state.get("target_coordinates")
    vehicle_spec = state.get("config", {}).get("vehicle_spec")
    
    logger.debug(f"Scoring {len(extracted_data)} extracted lots.")

    for lot in extracted_data:
        if lot.coordinates and target_coords:
            lot.distance_km = calculate_distance(
                target_coords,
                parse_coordinates(lot.coordinates)
            )
            logger.debug(f"Calculated distance for lot {lot.name}: {lot.distance_km:.2f} km")
        
        scored_lot = calculate_parking_score(
            lot, 
            vehicle_spec, 
            target_coords, 
            state["config"]
        )
        scored_lots.append(scored_lot)
        logger.debug(f"Scored lot '{scored_lot.name}': {scored_lot.score:.2f}")

    ranked_lots = rank_parking_lots(scored_lots)
    state["ranked_lots"] = ranked_lots
    logger.debug(f"Ranked {len(ranked_lots)} lots.")
    return state

def node_generate_output(state: WorkflowState) -> WorkflowState:
    """Generate the final Markdown output."""
    logger.debug("--- Generating final Markdown output ---")
    
    ranked_lots = state.get("ranked_lots", [])
    config = state["config"]
    output_file = config.get("output_file")
    
    metadata = {
        "place_name": state.get("place_name"),
        "target_coordinates": state.get("target_coordinates"),
        "total_duration_s": time.time() - state.get("_start_time", time.time()),
        "total_lots_found": len(state.get("extracted_data", [])),
        "total_lots_ranked": len(ranked_lots),
    }
    
    logger.debug(f"Generating output with {metadata['total_lots_ranked']} ranked lots.")
    
    markdown = generate_markdown_output(
        ranked_lots, 
        state.get("place_name"), 
        config, 
        metadata
    )
    state["final_markdown"] = markdown
    
    if output_file:
        save_output(markdown, output_file)
        logger.info(f"Final report saved to {output_file}")
    else:
        logger.warning("No output file specified in config. Report not saved.")
        
    return state

# ==============================================================================
# WORKFLOW GRAPH CONSTRUCTION
# ==============================================================================

def build_workflow_graph() -> StateGraph:
    """Build and return the LangGraph StateGraph."""
    workflow = StateGraph(WorkflowState)

    # Add nodes
    workflow.add_node("validate_config", node_validate_config)
    workflow.add_node("load_system_prompt", node_load_system_prompt)
    workflow.add_node("geocode_location", node_geocode_location)
    workflow.add_node("searxng_search", node_searxng_search)
    workflow.add_node("scrape_and_cache", node_scrape_and_cache)
    workflow.add_node("extract_with_gemini", node_extract_with_gemini)
    workflow.add_node("score_and_rank", node_score_and_rank)
    workflow.add_node("generate_output", node_generate_output)

    # Define edges
    workflow.set_entry_point("validate_config")
    workflow.add_edge("validate_config", "load_system_prompt")
    workflow.add_edge("load_system_prompt", "geocode_location")
    workflow.add_edge("geocode_location", "searxng_search")
    workflow.add_edge("searxng_search", "scrape_and_cache")
    workflow.add_edge("scrape_and_cache", END)
    # workflow.add_edge("scrape_and_cache", "extract_with_gemini")
    # workflow.add_edge("extract_with_gemini", "score_and_rank")
    # workflow.add_edge("score_and_rank", "generate_output")
    # workflow.add_edge("generate_output", END)

    return workflow.compile()

def execute_workflow(place_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute the main application workflow.

    Args:
        place_name: The location to search for.
        config: The application configuration.

    Returns:
        The final state of the workflow.
    """
    graph = build_workflow_graph()
    initial_state = {
        "place_name": place_name,
        "config": config,
        "_start_time": time.time(),
    }
    logger.info(f"Starting workflow for location: '{place_name}'")
    final_state = graph.invoke(initial_state)
    logger.info("Workflow finished.")
    return final_state
