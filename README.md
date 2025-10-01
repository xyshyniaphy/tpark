# Tokyo Monthly Parking Crawler

## 📌 Project Overview

**Project Name:** Tokyo Parking Crawler for Camping Car  
**Version:** 1.0.0  
**Purpose:** Automated web scraper using SearXNG to find outdoor/flat monthly parking lots in Tokyo suitable for camping cars with rooftop solar panels  
**Platform:** Ubuntu Linux with Python 3.10+  
**Architecture:** Modular Python package with multiple files

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
            │   ├─> src/scraper.py
            │   └─> src/cache.py
            │
            ├─> node_extract_with_gemini
            │   ├─> src/gemini.py
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
```