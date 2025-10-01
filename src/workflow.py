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

import time
from typing import Any, Dict, List

from langgraph.graph import StateGraph, END

from src.cache import CacheManager
from src.config import validate_config, load_system_prompt
from src.geocoding import geocode_location, parse_coordinates, calculate_distance
from src.gemini import GeminiExtractor
from src.models import WorkflowState, ParkingLot
from src.output import generate_markdown_output, save_output
from src.scoring import calculate_parking_score, rank_parking_lots
from src.scraper import WebScraper, html_to_markdown
from src.searxng import SearXNGClient

# ==============================================================================
# WORKFLOW NODES
# ==============================================================================

def node_validate_config(state: WorkflowState) -> WorkflowState:
    """Validate the application configuration."""
    errors = validate_config(state["config"])
    if errors:
        state["error"] = "\n".join(errors)
    return state

def node_load_system_prompt(state: WorkflowState) -> WorkflowState:
    """Load the Gemini system prompt."""
    state["system_prompt"] = load_system_prompt("system.md")
    return state

def node_geocode_location(state: WorkflowState) -> WorkflowState:
    """Geocode the input place name to get coordinates."""
    place_name = state["place_name"]
    coords = parse_coordinates(place_name)
    if not coords:
        coords = geocode_location(place_name)
    
    if not coords:
        state["error"] = f"Could not geocode location: {place_name}"
    state["target_coordinates"] = coords
    return state

def node_searxng_search(state: WorkflowState) -> WorkflowState:
    """Perform a web search using SearXNG."""
    config = state["config"]
    client = SearXNGClient(config["searxng_instance_url"], config)
    query = client.build_query(state["place_name"], config["search_query_template"])
    state["search_results"] = client.search(query, config["max_search_results"])
    return state

def node_scrape_and_cache(state: WorkflowState) -> WorkflowState:
    """Scrape web pages and cache their content as Markdown."""
    config = state["config"]
    scraper = WebScraper(config)
    cache = CacheManager(config["cache_dir"], config["cache_ttl_days"])
    scraped_content = []

    for result in state["search_results"]:
        url = result["url"]
        cached_md = cache.load_markdown(url, state["place_name"])
        if cached_md:
            scraped_content.append({"url": url, "markdown": cached_md})
            continue

        html = scraper.fetch(url)
        if html:
            markdown = html_to_markdown(html)
            cache.save_markdown(url, state["place_name"], markdown)
            scraped_content.append({"url": url, "markdown": markdown})
    
    state["scraped_content"] = scraped_content
    return state

def node_extract_with_gemini(state: WorkflowState) -> WorkflowState:
    """Extract structured data from Markdown using Gemini."""
    config = state["config"]
    extractor = GeminiExtractor(config, state["system_prompt"])
    extracted_data = []

    for content in state["scraped_content"]:
        lots = extractor.extract_parking_data(content["markdown"], content["url"])
        extracted_data.extend(lots)

    state["extracted_data"] = extracted_data
    return state

def node_score_and_rank(state: WorkflowState) -> WorkflowState:
    """Score and rank the extracted parking lots."""
    scored_lots = []
    for lot in state["extracted_data"]:
        if lot.coordinates:
            lot.distance_km = calculate_distance(
                state["target_coordinates"],
                parse_coordinates(lot.coordinates)
            )
        
        scored_lot = calculate_parking_score(
            lot, 
            state["config"]["vehicle_spec"], 
            state["target_coordinates"], 
            state["config"]
        )
        scored_lots.append(scored_lot)

    state["ranked_lots"] = rank_parking_lots(scored_lots)
    return state

def node_generate_output(state: WorkflowState) -> WorkflowState:
    """Generate the final Markdown output."""
    metadata = {
        "place_name": state["place_name"],
        "target_coordinates": state["target_coordinates"],
        "total_duration_s": time.time() - state.get("_start_time", time.time()),
    }
    markdown = generate_markdown_output(
        state["ranked_lots"], 
        state["place_name"], 
        state["config"], 
        metadata
    )
    state["final_markdown"] = markdown
    save_output(markdown, state["config"]["output_file"])
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
    workflow.add_edge("scrape_and_cache", "extract_with_gemini")
    workflow.add_edge("extract_with_gemini", "score_and_rank")
    workflow.add_edge("score_and_rank", "generate_output")
    workflow.add_edge("generate_output", END)

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
    final_state = graph.invoke(initial_state)
    return final_state
