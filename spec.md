# Tokyo Monthly Parking Crawler - Complete Specification (FINAL - MODULAR)

## 📌 Project Overview

**Project Name:** Tokyo Parking Crawler for Camping Car  
**Version:** 1.0.0  
**Purpose:** Automated web scraper using SearXNG to find outdoor/flat monthly parking lots in Tokyo suitable for camping cars with rooftop solar panels  
**Platform:** Ubuntu Linux with Python 3.10+  
**Architecture:** Modular Python package with multiple files

---

## 📁 Project Structure

```
tokyo_parking_crawler/
│
├── tokyo_parking_crawler.py       # Main entry point (CLI)
├── test_parse.py                  # Test script for individual parsers
├── system.md                       # Gemini system prompt
├── .env                            # User configuration (gitignored)
├── .env.sample                     # Sample configuration
├── requirements.txt                # Python dependencies
├── README.md                       # Documentation
├── .gitignore                      # Git ignore rules
│
├── src/                            # Source code modules
│   ├── __init__.py                 # Package initializer
│   ├── parsers/                    # Site-specific parsers
│   │   ├── __init__.py             # Parser registry
│   │   ├── base_parser.py          # Base class for parsers
│   │   └── carparking_jp.py        # Parser for carparking.jp
│   ├── config.py                   # Configuration management
│   ├── models.py                   # Data models (Pydantic)
│   ├── cache.py                    # Cache management
│   ├── geocoding.py                # Location geocoding
│   ├── searxng.py                  # SearXNG client
│   ├── scraper.py                  # Web scraping
│   ├── gemini.py                   # Gemini LLM integration
│   ├── scoring.py                  # Scoring and ranking
│   ├── output.py                   # Markdown output generation
│   ├── workflow.py                 # LangGraph workflow
│   └── utils.py                    # Utility functions
│
├── webpages/                       # Cache directory (auto-created)
│   ├── *.html                        # Cached html files
│   └── *.json                      # Cached JSON data
│
├── logs/                           # Log directory (auto-created)
│   └── parking_crawler.log         # Application logs
│
└── parking_results.md              # Output file
```

---

## 📄 File Responsibilities

### Main Entry Point

#### `tokyo_parking_crawler.py` (Main CLI)
- Parse command-line arguments
- Initialize logging
- Load configuration
- Execute workflow
- Handle top-level exceptions
- Display results

**Lines of code:** ~150-200

#### `test_parse.py` (Parser Test Script)
- A dedicated utility for testing individual parsers on local HTML files.
- Allows for rapid development and debugging of parsers.
- This file is intended for development and testing, and should be kept in the project.

---

### Core Modules (`src/`)

#### `src/__init__.py`
```python
"""Tokyo Parking Crawler package."""
__version__ = "1.0.0"
```

#### `src/config.py` - Configuration Management
**Purpose:** Load, validate, and manage configuration from .env file

**Functions:**
- `load_yaml_env(env_file: str) -> Dict[str, Any]`
- `validate_config(config: Dict) -> List[str]`
- `merge_with_defaults(config: Dict) -> Dict`
- `load_system_prompt(file: str) -> str`
- `create_sample_env() -> None`

**Lines of code:** ~150-200

---

#### `src/models.py` - Data Models
**Purpose:** Pydantic models for type safety and validation

**Classes:**
- `ParkingDimensions(BaseModel)`
- `ParkingAmenities(BaseModel)`
- `ParkingPricing(BaseModel)`
- `ParkingScoreBreakdown(BaseModel)`
- `ParkingLot(BaseModel)`
- `WorkflowState(TypedDict)` - LangGraph state

**Lines of code:** ~200-250

---

#### `src/cache.py` - Cache Management
**Purpose:** Manage file-based caching with TTL

**Classes:**
- `CacheManager`
  - `__init__(cache_dir, ttl_days)`
  - `save_html(url, location, html) -> Path`
  - `save_json(url, location, data) -> Path`
  - `load_html(url, location) -> Optional[str]`
  - `load_json(url, location) -> Optional[List[Dict]]`
  - `is_cache_valid(cache_file) -> bool`
  - `get_cache_stats() -> Dict`

**Lines of code:** ~200-250

---

#### `src/geocoding.py` - Geocoding
**Purpose:** Convert place names to coordinates and distance calculations

**Functions:**
- `geocode_location(place_name: str) -> Optional[Tuple[float, float]]`
- `calculate_distance(coord1, coord2) -> float`
- `parse_coordinates(input: str) -> Optional[Tuple[float, float]]`

**Lines of code:** ~100-150

---

#### `src/searxng.py` - SearXNG Integration
**Purpose:** Search using SearXNG meta-search engine

**Classes:**
- `SearXNGClient`
  - `__init__(instance_url, config)`
  - `search(query, max_results) -> List[Dict]`
  - `filter_parking_results(results) -> List[str]`
  - `build_query(location, template) -> str`

**Lines of code:** ~150-200

---

#### `src/scraper.py` - Web Scraping
**Purpose:** Robust web scraping with anti-bot measures

**Classes:**
- `WebScraper`
  - `__init__(config)`
  - `fetch(url) -> Optional[str]`
  - `_get_headers() -> Dict`
  - `_retry_request(url, attempts) -> Optional[str]`

**Functions:**
- `clean_html(soup: BeautifulSoup) -> BeautifulSoup`

**Constants:**
- `USER_AGENTS: List[str]`

**Lines of code:** ~150-200

---

#### `src/parsers/` - Site-specific Parsers
**Purpose:** Contains parsers for specific websites to extract parking lot data from cleaned HTML.

**`src/parsers/__init__.py`**
- Registers available parsers and provides a function to get the correct parser for a given URL.

**`src/parsers/base_parser.py`**
- Defines the `BaseParser` abstract base class that all site-specific parsers must inherit from.

**`src/parsers/carparking_jp.py`**
- A concrete implementation of `BaseParser` for the `carparking.jp` website.

---

#### `src/gemini.py` - Gemini Integration
**Purpose:** LLM-powered data extraction using Gemini 2.0 Flash. Supports connecting to a custom Gemini endpoint.

**Classes:**
- `GeminiExtractor`
  - `__init__(config, system_prompt)`: Initializes the extractor, optionally configuring a custom Gemini endpoint.
  - `extract_parking_data(html, url) -> List[Dict]`
  - `parse_gemini_response(response_text) -> List[Dict]`
  - `validate_parking_data(data) -> bool`

**Lines of code:** ~150-200

---

#### `src/scoring.py` - Scoring and Ranking
**Purpose:** Calculate suitability scores for parking lots

**Functions:**
- `calculate_parking_score(parking_lot, vehicle_spec, target_coords, config) -> ParkingLot`
- `calculate_dimension_score(dimensions, vehicle) -> float`
- `calculate_price_score(price, max_price) -> float`
- `calculate_distance_score(distance, max_distance) -> float`
- `calculate_amenity_score(amenities) -> float`
- `rank_parking_lots(lots) -> List[ParkingLot]`

**Lines of code:** ~200-250

---

#### `src/output.py` - Output Generation
**Purpose:** Generate formatted markdown output

**Functions:**
- `generate_markdown_output(parking_lots, place_name, config, metadata) -> str`
- `generate_table(parking_lots) -> str`
- `generate_detailed_section(parking_lots, top_n) -> str`
- `generate_summary(parking_lots, config) -> str`
- `format_parking_lot_detail(lot, rank, config) -> str`
- `save_output(markdown, output_file) -> None`

**Lines of code:** ~250-300

---

#### `src/workflow.py` - LangGraph Workflow
**Purpose:** Orchestrate the entire workflow using LangGraph. Includes detailed DEBUG-level logging for each step to allow for thorough debugging.

**Functions (LangGraph Nodes):**
- `node_validate_config(state) -> WorkflowState`
- `node_load_system_prompt(state) -> WorkflowState`
- `node_geocode_location(state) -> WorkflowState`
- `node_searxng_search(state) -> WorkflowState`
- `node_scrape_and_cache(state) -> WorkflowState`
- `node_extract_data(state) -> WorkflowState`
- `node_score_and_rank(state) -> WorkflowState`
- `node_generate_output(state) -> WorkflowState`

**Functions (Workflow Construction):**
- `build_workflow_graph() -> StateGraph`
- `execute_workflow(place_name, config) -> Dict`

**Lines of code:** ~300-350

---

#### `src/utils.py` - Utility Functions
**Purpose:** Common utilities and helper functions

**Functions:**
- `setup_logging(log_level, log_file) -> logging.Logger`
- `show_usage_instructions() -> None`
- `show_banner() -> None`
- `format_time_duration(seconds) -> str`
- `truncate_text(text, max_length) -> str`
- `create_directory(path) -> None`

**Constants:**
- `APP_NAME: str`
- `VERSION: str`
- `DEFAULT_CONFIG: Dict`
  ```python
  {
      "log_level": "INFO",
      "log_file": "logs/parking_crawler.log",
      "cache_dir": "webpages",
      "cache_ttl_days": 7,
      "output_file": "parking_results.md",
      "searxng_instance_url": "http://127.0.0.1:8888",
      "max_search_results": 10,
      "vehicle_spec": {
          "length_m": 4.8,
          "width_m": 1.9,
          "height_m": 2.1,
      },
      "scoring_weights": {
          "dimension": 0.4,
          "price": 0.3,
          "distance": 0.2,
          "amenity": 0.1,
      },
      "max_price": 100000,
      "max_distance_km": 5.0,
      "output_top_n": 5,
      "search_query_template": "site:*.jp 月極駐車場 {location} 屋外 平置き",
      "gemini_model": "gemini/gemini-2.0-flash",
      "gemini_api_key": "YOUR_API_KEY",
      "gemini_api_endpoint": None,
      "max_crawl_pages": 10
  }
  ```

**Lines of code:** ~150-200

---

## 🔧 File Size Summary

| File | Purpose | Est. Lines |
|------|---------|-----------|
| `tokyo_parking_crawler.py` | Main CLI | 150-200 |
| `src/config.py` | Configuration | 150-200 |
| `src/models.py` | Data models | 200-250 |
| `src/cache.py` | Cache management | 200-250 |
| `src/geocoding.py` | Geocoding | 100-150 |
| `src/searxng.py` | SearXNG client | 150-200 |
| `src/scraper.py` | Web scraping | 150-200 |
| `src/gemini.py` | Gemini integration | 150-200 |
| `src/scoring.py` | Scoring logic | 200-250 |
| `src/output.py` | Markdown output | 250-300 |
| `src/workflow.py` | LangGraph workflow | 300-350 |
| `src/utils.py` | Utilities | 150-200 |
| **Total** | | **~2,000-2,700** |

Each file is **manageable size (100-350 lines)** with clear separation of concerns.

---

## 📦 Installation

### requirements.txt
```txt
# Core Dependencies
python-dotenv>=1.0.0
pyyaml>=6.0.1
pydantic>=2.5.0

# LangChain & LangGraph
langchain>=0.1.0
langchain-google-genai>=1.0.0
langgraph>=0.0.20

# Web Scraping & Parsing
requests>=2.31.0
beautifulsoup4>=4.12.0
lxml>=4.9.0
markdownify>=0.11.6

# Geolocation
geopy>=2.4.0

# Utilities
tqdm>=4.66.0
typing-extensions>=4.9.0
```

### Installation Command (Ubuntu)
```bash
# Single command using uv pip
curl -LsSf https://astral.sh/uv/install.sh | sh && \
  source $HOME/.cargo/env && \
  uv pip install -r requirements.txt
```

---

## 🎯 Usage

### Command Line
```bash
# Basic usage
python tokyo_parking_crawler.py "渋谷駅"

# With coordinates
python tokyo_parking_crawler.py "35.6628,139.6983"

# Help
python tokyo_parking_crawler.py --help

# Version
python tokyo_parking_crawler.py --version
```

### Import as Module
```python
from src.workflow import execute_workflow
from src.config import load_yaml_env

config = load_yaml_env()
result = execute_workflow("渋谷駅", config)
print(result["final_markdown"])
```

---

## 🔄 Workflow Diagram

```
tokyo_parking_crawler.py (MAIN)
    │
    ├─> src/utils.py (setup_logging, show_banner)
    │
    ├─> src/config.py (load_yaml_env, validate_config)
    │
    └─> src/workflow.py (execute_workflow)
            │
            ├─> node_validate_config
            │   └─> src/config.py
            │
            ├─> node_load_system_prompt
            │   └─> src/config.py
            │
            ├─> node_geocode_location
            │   └─> src/geocoding.py
            │
            ├─> node_searxng_search
            │   └─> src/searxng.py
            │
            ├─> node_scrape_and_cache
            │   ├─> src/scraper.py (WebScraper)
            │   ├─> src/cache.py (CacheManager)
            │   └─> Follows detail and pagination links to crawl multiple pages.
            │
            ├─> node_extract_data
            │   ├─> src/parsers/
            │   ├─> src/cache.py
            │   └─> src/models.py
            │
            ├─> node_score_and_rank
            │   ├─> src/scoring.py
            │   ├─> src/geocoding.py
            │   └─> src/models.py
            │
            └─> node_generate_output
                └─> src/output.py
```

---

## 📝 Module Dependencies

### Import Hierarchy (No Circular Dependencies)

**Level 1: No dependencies**
- `src/utils.py`
- `src/models.py`

**Level 2: Depends on Level 1**
- `src/config.py` → utils
- `src/geocoding.py` → utils
- `src/cache.py` → utils, models

**Level 3: Depends on Level 1-2**
- `src/searxng.py` → utils, models
- `src/scraper.py` → utils, cache
- `src/gemini.py` → utils, models, config

**Level 4: Depends on Level 1-3**
- `src/scoring.py` → utils, models, geocoding
- `src/output.py` → utils, models

**Level 5: Depends on Level 1-4**
- `src/workflow.py` → ALL modules

**Level 6: Entry point**
- `tokyo_parking_crawler.py` → utils, config, workflow

---

## ✅ Benefits of Modular Architecture

### 1. **Maintainability**
- Each file has single responsibility
- Easy to locate and fix bugs
- Clear module boundaries

### 2. **Testability**
- Can test each module independently
- Mock dependencies easily
- Unit tests per module

### 3. **Readability**
- Manageable file sizes (100-350 lines)
- Clear naming conventions
- Easy to understand flow

### 4. **Extensibility**
- Add new scrapers without touching existing code
- Swap out components (e.g., different LLM)
- Add new output formats

### 5. **Reusability**
- Use modules in other projects
- Import specific functionality
- Build on top of components

---

## 🧪 Testing Structure

```
tests/
├── __init__.py
├── test_config.py          # Test configuration loading
├── test_models.py          # Test Pydantic models
├── test_cache.py           # Test cache operations
├── test_geocoding.py       # Test geocoding
├── test_searxng.py         # Test SearXNG client
├── test_scraper.py         # Test web scraping
├── test_gemini.py          # Test Gemini extraction
├── test_scoring.py         # Test scoring logic
├── test_output.py          # Test output generation
├── test_workflow.py        # Test workflow execution
└── fixtures/               # Test data
    ├── sample_html.html
    ├── sample_markdown.md
    └── sample_config.yaml
```

---

## 📊 Code Quality Standards

### All Files Must Have:

1. **File Docstring**
```python
"""
Module description.

This module provides...

Example:
    >>> from src.module import function
    >>> result = function(param)
"""
```

2. **Type Hints**
```python
def function_name(param: str, count: int = 0) -> List[Dict[str, Any]]:
    """Function description."""
    pass
```

3. **Google-Style Docstrings**
```python
def complex_function(param1: str, param2: int) -> Dict:
    """
    Brief description.
    
    Detailed explanation of what the function does.
    
    Args:
        param1: Description of param1
        param2: Description of param2
    
    Returns:
        Dictionary containing result data
    
    Raises:
        ValueError: If param1 is empty
        ConnectionError: If network fails
    
    Example:
        >>> result = complex_function("test", 5)
        >>> print(result["key"])
        value
    """
    pass
```

4. **Section Comments**
```python
# ============================================================================
# SECTION NAME
# ============================================================================
```

5. **Inline Comments**
```python
# Explain complex logic
result = some_complex_calculation()  # Why this is needed
```

---

## 🚀 Implementation Order

### Phase 1: Foundation (Day 1)
1. `src/utils.py` - Utilities
2. `src/models.py` - Data models
3. `src/config.py` - Configuration

### Phase 2: Core Services (Day 2)
4. `src/cache.py` - Cache management
5. `src/geocoding.py` - Geocoding
6. `src/searxng.py` - SearXNG client

### Phase 3: Data Processing (Day 3)
7. `src/scraper.py` - Web scraping
8. `src/gemini.py` - Gemini integration
9. `src/scoring.py` - Scoring logic

### Phase 4: Output & Workflow (Day 4)
10. `src/output.py` - Output generation
11. `src/workflow.py` - LangGraph workflow
12. `tokyo_parking_crawler.py` - Main CLI

### Phase 5: Polish (Day 5)
13. Testing and bug fixes
14. Documentation
15. `.env.sample` and `system.md`

---

## ✅ Acceptance Criteria

### Code Organization
- [x] Modular architecture with separate files
- [x] Clear separation of concerns
- [x] No circular dependencies
- [x] Each file 100-350 lines
- [x] Logical directory structure

### Code Quality
- [x] Full type hints on all functions
- [x] Google-style docstrings
- [x] Comprehensive inline comments
- [x] Section headers in each file
- [x] PEP 8 compliant

### Functionality
- [x] All features from original spec
- [x] Single entry point CLI
- [x] Can import as module
- [x] LangGraph workflow
- [x] Gemini 2.0 Flash integration
- [x] SearXNG search
- [x] Cache management (1 week TTL)
- [x] Markdown output
- [x] .env configuration (YAML)

### Installation
- [x] requirements.txt
- [x] Single install command with uv pip
- [x] Ubuntu Linux compatible

---

## 📄 Status

**Status:** ✅ **SPECIFICATION COMPLETE - READY FOR IMPLEMENTATION**

**Next Step:** Implement modules in order (Phase 1 → Phase 5)

---
do not use gemini key from .bashrc or system env.