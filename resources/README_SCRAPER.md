# North Carolina Fishing Points Scraper

This script scrapes fishing location data from TidesPro.com for North Carolina locations and generates GPX files compatible with GPS devices and fishing apps.

## Features

- 🎣 Scrapes fishing locations from multiple NC regions on TidesPro.com
- 📍 Extracts coordinates, names, descriptions, and depth information
- 🗺️ Generates GPX files compatible with Garmin and other GPS devices
- 🏷️ Smart categorization with symbols (Wreck/Reef) and types (Shipwreck/Concrete Reef/Artificial Reef)
- 📊 Saves raw data in JSON format for analysis
- 🔄 Automatic deduplication of duplicate locations
- 🌊 Dynamic table structure handling for different page layouts
- 📏 Automatic depth unit conversion to feet
- 🤖 GitHub Actions automation for regular data updates

## Installation

1. Make sure Python 3.11+ is installed
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Quick Start

Run the scraper with the main application:
```bash
python main.py
```

This will:
- Set up the virtual environment automatically
- Install dependencies if needed
- Run the scraper
- Generate GPX and JSON files in the `point_files/` directory

### Direct Execution

Run the scraper module directly:
```bash
python resources/source/nc.py
```

## Output Files

The scraper generates files in the `point_files/` directory:

- **GPX Files** (`nc_fishing_points_YYYYMMDD_HHMMSS.gpx`)
  - Compatible with GPS devices and fishing apps
  - Contains waypoints with coordinates, names, descriptions, and depth
  - Includes Garmin extensions with proper categorization
  - Symbol field: "Wreck" or "Reef"
  - Type field: "Shipwreck", "Concrete Reef", or "Artificial Reef"

- **JSON Files** (`nc_fishing_data_YYYYMMDD_HHMMSS.json`)
  - Raw scraped data for analysis and debugging
  - Contains all extracted information including source URLs and metadata

## Automated Updates

The project includes GitHub Actions automation that:
- ⏰ Runs weekly on Sundays at 6:00 AM UTC
- 🚀 Triggers on pushes to master branch
- 🖱️ Can be manually triggered from GitHub Actions tab
- 📦 Creates releases with GPX/JSON files as downloadable assets
- 💾 Stores artifacts for 30 days

## Supported Data Sources

Currently scrapes all major NC fishing regions:
- **Estuarine**: https://www.tidespro.com/fishing/us/north-carolina/estuarine
- **Long Bay**: https://www.tidespro.com/fishing/us/north-carolina/long-bay
- **Onslow Bay**: https://www.tidespro.com/fishing/us/north-carolina/onslow-bay
- **Outer Banks**: https://www.tidespro.com/fishing/us/north-carolina/outer-banks
- **Raleigh Bay**: https://www.tidespro.com/fishing/us/north-carolina/raleigh-bay

## Smart Data Processing

### Coordinate Extraction
- Extracts decimal degrees (DD) from hidden spans in table cells
- Dynamically handles different table layouts (4-column vs 5-column with depth)
- Validates coordinate ranges for North Carolina region

### Description Cleaning
Automatically removes unwanted text from descriptions:
- "Average Depth:" sections
- "Deployed:" information  
- "Depth:" measurements
- "Tides & Solunars" references
- Reference markers like "[1]"

### Depth Processing
- Extracts depth from dedicated table columns when available
- Supports multiple units: feet, meters, fathoms
- Converts all measurements to feet for consistency
- Stores as numeric values (not strings) for GPS compatibility

### Smart Categorization
Based on description content:
- **Wrecks**: `sym: "Wreck"`, `type: "Shipwreck"`
- **Concrete structures**: `sym: "Reef"`, `type: "Concrete Reef"`  
- **Other artificial reefs**: `sym: "Reef"`, `type: "Artificial Reef"`

## Project Architecture

### File Structure
```
fishing-points/
├── main.py                          # Main application entry point with auto-setup
├── requirements.txt                 # Python dependencies
├── point_files/                     # Generated output files (gitignored)
│   ├── *.gpx                       # GPX waypoint files
│   └── *.json                      # Raw scraped data
├── resources/
│   ├── source/
│   │   └── nc.py                   # Main scraper implementation
│   ├── destination/
│   │   ├── gpx_generator.py        # Externalized GPX file creation
│   │   └── gpx.xsd                 # GPX schema definition
│   └── README_SCRAPER.md           # This documentation
├── .github/
│   └── workflows/
│       └── scrape-fishing-points.yml  # GitHub Actions automation
├── .gitignore                      # Clean Python-focused gitignore
└── venv/                           # Virtual environment (auto-created)
```

### Key Components

**Main Application** (`main.py`)
- Automatic virtual environment setup
- Dependency installation
- Cross-platform compatibility
- Environment validation

**Core Scraper** (`resources/source/nc.py`)
- Dynamic table parsing for different page layouts
- Robust coordinate extraction from hidden DD spans
- Smart description cleaning and categorization
- Flexible depth measurement handling

**GPX Generator** (`resources/destination/gpx_generator.py`)
- Externalized file creation logic
- GPX 1.1 standard compliance
- Garmin extension support
- Proper XML formatting with validation

**GitHub Actions** (`.github/workflows/scrape-fishing-points.yml`)
- Weekly automated runs
- Release creation with artifacts
- Manual trigger capability
- Cross-platform CI/CD

## Dependencies

Core Python packages:
- `requests>=2.31.0` - HTTP requests to web pages
- `beautifulsoup4>=4.12.0` - HTML parsing and data extraction  
- `lxml>=4.9.0` - XML processing (used by BeautifulSoup)
- `defusedxml>=0.7.1` - Secure XML parsing for GPX generation

## Error Handling & Robustness

The scraper includes comprehensive error handling:
- **Network resilience**: Timeouts, retries, respectful delays
- **Data validation**: Coordinate range checking, duplicate detection
- **Format flexibility**: Multiple table layouts, missing data graceful handling
- **Output validation**: GPX schema compliance, UTF-8 encoding
- **Logging**: Detailed progress reporting and error diagnostics

## Troubleshooting

### No locations found
- Check if TidesPro.com is accessible
- Verify website structure hasn't changed significantly
- Review parsing logic in `extract_location_from_table_row()`

### Import/Environment errors  
- Run `python main.py` for automatic environment setup
- Manually install: `pip install -r requirements.txt`
- Ensure Python 3.11+ is available

### GitHub Actions failing
- Check workflow logs in GitHub Actions tab
- Verify secrets are configured (GITHUB_TOKEN is automatic)
- Check for rate limiting or network issues

### Coordinate extraction issues
- Table structure may have changed - check DD span extraction logic
- Validate coordinate ranges are appropriate for NC region
- Review cell indexing in dynamic table parsing

## Usage in GPS Devices

### Garmin Devices
1. Download the GPX file from latest release
2. Copy to `/Garmin/GPX/` folder on device or SD card
3. Waypoints appear with proper symbols (Wreck/Reef icons)
4. Depth information available in waypoint details

### Other GPS/Navigation Apps
- Import GPX file directly
- Waypoints include name, description, coordinates, and depth
- Type field provides additional categorization

## Legal Notice

This tool is for educational and personal fishing use only. Please:
- Respect TidesPro.com's terms of service
- Use appropriate delays between requests (configured in scraper)
- Do not overload their servers
- Give credit to TidesPro.com as the data source

## Contributing

1. Fork the repository
2. Make improvements to parsing logic, add new regions, or enhance output
3. Test thoroughly with `python main.py`  
4. Update documentation if needed
5. Submit a pull request

## License

This project is open source. Please use responsibly and respect data sources.