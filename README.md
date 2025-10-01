# 🚐 Tokyo Parking Crawler for Camping Cars

Find outdoor monthly parking lots in Tokyo suitable for camping cars with rooftop solar panels.

## 🎯 What It Does

Searches for and compares **outdoor/flat monthly parking spaces** (月極駐車場) in Tokyo that can accommodate camping cars with solar panels. Uses SearXNG for privacy-respecting search and Gemini 2.0 Flash for intelligent Japanese text parsing.

**Perfect for:**
- Camping car owners needing long-term parking
- Solar panel charging (requires no-roof parking)
- 24-hour access parking search
- Price comparison across multiple sources

## ✨ Features

- 🔍 **SearXNG Integration** - Meta-search across multiple engines
- 🤖 **Gemini 2.0 Flash** - Intelligent Japanese text parsing
- 📊 **Smart Scoring** - Ranks by price, distance, size compatibility
- 💾 **Intelligent Caching** - 1-week TTL, avoids re-scraping
- 📝 **Markdown Output** - Clean, sortable table format
- 🎯 **Outdoor Detection** - Critical filtering for solar charging
- 🗺️ **Google Maps Links** - Direct navigation to locations

## 📋 Requirements

- **OS:** Ubuntu Linux (or similar)
- **Python:** 3.10 or higher
- **API Key:** Google Gemini API key ([Get one here](https://makersuite.google.com/app/apikey))
- **SearXNG:** Access to a SearXNG instance ([Public instances](https://searx.space/))

## 🚀 Quick Start

### 1. Install

```bash
# Clone or download the project
cd tokyo_parking_crawler

# Install uv (fast package installer)
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.cargo/env

# Install dependencies
uv pip install -r requirements.txt
```

### 2. Configure

```bash
# Create configuration file
cp .env.sample .env

# Edit with your API key
nano .env
```

**Minimum required configuration:**
```yaml
gemini:
  api_key: "YOUR_GEMINI_API_KEY_HERE"
  api_endpoint: "https://generativelanguage.googleapis.com/v1beta"
  model: "gemini-2.0-flash-exp"

searxng:
  instance_url: "https://searx.be"  # or your own instance
  engines: "google,bing"
```

### 3. Run

```bash
# Search by place name
python tokyo_parking_crawler.py "渋谷駅"

# Search by coordinates
python tokyo_parking_crawler.py "35.6628,139.6983"

# View results
cat parking_results.md
```

## 📖 Usage Examples

```bash
# Japanese place name
python tokyo_parking_crawler.py "新宿駅"

# English place name
python tokyo_parking_crawler.py "Shibuya Station"

# Coordinates (lat,lng)
python tokyo_parking_crawler.py "35.6628,139.6983"

# Show help
python tokyo_parking_crawler.py --help

# Show version
python tokyo_parking_crawler.py --version
```

## 📊 Output Example

The script generates `parking_results.md`:

```markdown
# Tokyo Camping Car Parking Search Results

**Search Location:** 渋谷駅
**Vehicle Specs:** H:2.2m × W:1.8m × L:5.0m

## 🅿️ Parking Options (Sorted by Price)

| Rank | Score | Name | Distance | Monthly Price | Size (H×W×L) | 24h | Google Maps |
|:----:|:-----:|:-----|:--------:|:-------------:|:------------:|:---:|:-----------:|
| 1 | 🟢 87.5 | タイムズ渋谷第5 | 450m | ¥28,000 | Open×2.0×5.5 | ✓ | [📍 Map](https://...) |
| 2 | 🟢 82.3 | エスパーク代々木 | 680m | ¥32,000 | Open×1.9×5.2 | ✓ | [📍 Map](https://...) |
...
```

## 🏗️ Project Structure

```
tokyo_parking_crawler/
├── tokyo_parking_crawler.py    # Main CLI entry point
├── system.md                    # Gemini system prompt
├── .env                         # Your configuration (not in git)
├── .env.sample                  # Configuration template
├── requirements.txt             # Python dependencies
│
├── src/                         # Source code modules
│   ├── config.py               # Configuration management
│   ├── models.py               # Data models
│   ├── cache.py                # Cache system
│   ├── geocoding.py            # Location services
│   ├── searxng.py              # Search integration
│   ├── scraper.py              # Web scraping
│   ├── gemini.py               # LLM integration
│   ├── scoring.py              # Ranking algorithm
│   ├── output.py               # Markdown generation
│   ├── workflow.py             # LangGraph orchestration
│   └── utils.py                # Utilities
│
└── webpages/                    # Cached data (auto-created)
    ├── *.md                    # HTML→Markdown cache
    └── *.json                  # Parsed data cache
```

## ⚙️ Configuration

### Vehicle Specifications (in `.env`)

Default values for camping car:

```yaml
vehicle:
  height_m: 2.2    # Height with rooftop solar panel
  width_m: 1.8     # Width including mirrors
  length_m: 5.0    # Total length
```

### Search Parameters

```yaml
search:
  radius_km: 2.0                    # Search radius (fixed)
  max_monthly_price_jpy: 50000      # Maximum price filter
```

### Scoring Weights

```yaml
scoring:
  no_roof_multiplier: 10.0          # Critical: outdoor requirement
  dimension_score_weight: 0.4       # Size compatibility (highest)
  price_score_weight: 0.25          # Price competitiveness
  distance_score_weight: 0.2        # Proximity to target
  amenity_score_weight: 0.15        # Features (24h, lighting, etc.)
```

## 🎯 Key Features Explained

### Outdoor Detection
- **Critical requirement:** No roof for solar panel charging
- Identifies: 平面駐車場, 屋根なし, 青空駐車場
- Filters out: 立体駐車場, 機械式, 屋根付き

### Smart Caching
- Caches HTML→Markdown conversions
- Caches Gemini parsing results
- 1-week TTL (configurable)
- Saves API calls and bandwidth

### Scoring System
- **Green (80-100):** Excellent match
- **Yellow (60-79):** Good option
- **Orange (40-59):** Marginal
- **Red (0-39):** Not suitable

## 🐛 Troubleshooting

### "Missing required configuration"
```bash
# Make sure .env exists and has required fields
cp .env.sample .env
nano .env  # Add your Gemini API key
```

### "Failed to geocode location"
```bash
# Try with coordinates instead
python tokyo_parking_crawler.py "35.6628,139.6983"
```

### "SearXNG search failed"
```bash
# Try different SearXNG instance in .env
searxng:
  instance_url: "https://search.sapti.me"
```

### Empty results
- Try different search location
- Check if place name is recognized (use major stations)
- Verify internet connection
- Check logs: `cat parking_crawler.log`

## 📝 Notes

### Legal & Ethical Use
- **Respects robots.txt** and rate limits
- **Caches aggressively** to minimize server load
- **Educational/Personal use** only
- Always verify information with official sources before signing contracts

### Data Accuracy
- Prices and availability may change
- Always contact parking operator to confirm
- Dimensions should be verified on-site
- Script provides estimates for comparison only

### API Costs
- Gemini 2.0 Flash: ~$0.05-0.20 per search
- Free tier: 15 requests/minute, 1500/day
- Caching reduces repeated API calls

## 🤝 Contributing

Found a bug? Have a suggestion?
- Check logs: `parking_crawler.log`
- Review cached data: `webpages/*.json`
- Test with different locations

## 📄 License

MIT License - Use at your own risk

## 🙏 Acknowledgments

- **SearXNG:** Privacy-respecting metasearch
- **Gemini 2.0 Flash:** Japanese text parsing
- **LangChain/LangGraph:** Workflow orchestration

---

**Made for camping car enthusiasts who need solar charging** ☀️🚐⚡

---

**Quick Links:**
- [Get Gemini API Key](https://makersuite.google.com/app/apikey)
- [SearXNG Public Instances](https://searx.space/)
- [Project Issues](#)