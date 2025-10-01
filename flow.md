# LangGraph Workflow

This document outlines the LangGraph workflow for the Tokyo Parking Crawler.

## Workflow State

The workflow is managed by a state dictionary defined by `WorkflowState`:

```python
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
```

## Workflow Nodes

The workflow consists of the following nodes:

1.  **`node_validate_config`**: Validates the application configuration.
2.  **`node_load_system_prompt`**: Loads the Gemini system prompt.
3.  **`node_geocode_location`**: Geocodes the input place name to get coordinates.
4.  **`node_searxng_search`**: Performs a web search using SearXNG.
5.  **`node_scrape_and_cache`**: Scrapes web pages and caches their content as Markdown.
6.  **`node_extract_with_gemini`**: Extracts structured data from Markdown using Gemini.
7.  **`node_score_and_rank`**: Scores and ranks the extracted parking lots.
8.  **`node_generate_output`**: Generates the final Markdown output.

## Workflow Graph

The nodes are connected in a sequential graph:

```
[Start] -> validate_config -> load_system_prompt -> geocode_location -> searxng_search -> scrape_and_cache -> extract_with_gemini -> score_and_rank -> generate_output -> [End]
```

### Graph Construction

The graph is built using the `StateGraph` class from LangGraph:

```python
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
```
