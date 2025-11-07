# 🎣 North Carolina Fishing Points Scraper

A comprehensive Python application that scrapes fishing location data from TidesPro.com and generates marine GPS-optimized GPX files for North Carolina coastal waters.

## 🌊 Features

- **📍 Comprehensive Coverage**: Scrapes all NC coastal regions (Estuarine, Long Bay, Onslow Bay, Outer Banks, Raleigh Bay)
- **🗺️ Marine GPS Optimized**: Generates GPX files specifically optimized for Garmin marine devices and Active Captain
- **⚓ Smart Categorization**: Automatically classifies structures (Wrecks, Reefs, Artificial Reefs) with appropriate symbols
- **📏 Depth Processing**: Extracts and converts depth measurements to feet with unit standardization
- **🎯 Display Optimization**: Truncates waypoint names for 10-character GPS display limits while preserving full details
- **🔄 Automated Workflow**: GitHub Actions integration for weekly automatic updates
- **📊 Data Export**: Provides both GPX (for GPS) and JSON (for analysis) output formats

## 🚀 Quick Start

### Prerequisites
- Python 3.11 or higher
- Internet connection for scraping TidesPro.com

### Installation & Usage

1. **Clone the repository**:
   ```bash
   git clone https://github.com/vinnimous/fishing-points.git
   cd fishing-points
   ```

2. **Run the application**:
   ```bash
   python main.py
   ```

The application automatically handles:
- ✅ Virtual environment creation
- ✅ Dependency installation  
- ✅ Scraping all NC fishing regions
- ✅ GPX file generation
- ✅ Data validation and deduplication

### Output Files

Generated files are saved to `point_files/`:
- **`nc_fishing_points_YYYYMMDD_HHMMSS.gpx`** - Marine GPS waypoint file
- **`nc_fishing_data_YYYYMMDD_HHMMSS.json`** - Raw scraped data with metadata

## 🗺️ GPS Device Compatibility

### Optimized For:
- **Garmin ECHOMAP UHD Series** (1243xsv, etc.)
- **Garmin Active Captain** mobile app
- **Most marine GPS units** supporting GPX 1.1 standard

### Marine Symbols:
- 🚢 **Shipwreck** - For identified wreck sites
- 🐟 **Fish** - For reefs and artificial structures

### Display Optimization:
- **Short Names**: GPS display shows truncated identifiers (e.g., "AAR-465")
- **Full Details**: Complete descriptions preserved in waypoint details
- **Depth Data**: Included in Garmin extensions where available

## 🏗️ Project Structure

```
fishing-points/
├── main.py                           # Application entry point
├── resources/
│   ├── source/
│   │   └── nc.py                     # TidesPro.com scraper
│   └── destination/
│       └── gpx_generator.py          # Marine GPS file generator
├── point_files/                      # Generated output files
├── requirements.txt                  # Python dependencies
├── .github/workflows/                # Automation
│   └── scrape-fishing-points.yml     # Weekly scraping workflow
└── README.md                         # This file
```

## 🔧 Technical Details

### Scraping Targets
- **Estuarine Fishing**: `tidespro.com/fishing/us/north-carolina/estuarine`
- **Long Bay**: `tidespro.com/fishing/us/north-carolina/long-bay`
- **Onslow Bay**: `tidespro.com/fishing/us/north-carolina/onslow-bay`
- **Outer Banks**: `tidespro.com/fishing/us/north-carolina/outer-banks`
- **Raleigh Bay**: `tidespro.com/fishing/us/north-carolina/raleigh-bay`

### Data Processing
- **Dynamic Table Parsing**: Adapts to different TidesPro.com page layouts
- **Coordinate Validation**: Decimal degrees format with geographical bounds checking
- **Depth Conversion**: Supports feet, meters, and fathoms → standardized to feet
- **Deduplication**: Removes duplicate coordinates within 0.1-meter precision
- **Structure Classification**: Keyword-based categorization for marine symbols

### GPX Standards
- **GPX 1.1 Compliance**: Industry-standard GPS format
- **Garmin Extensions v3**: Enhanced depth, temperature, and category data
- **Marine Symbols**: Shipwreck and Fish symbols for optimal display
- **UTF-8 Encoding**: Full international character support

## 🤖 Automation

### GitHub Actions Workflow
- **Weekly Schedule**: Automatic scraping every Sunday at 6:00 AM UTC
- **Manual Trigger**: Run on-demand via GitHub Actions
- **Release Creation**: Automatic GitHub releases with GPX/JSON files
- **Artifact Storage**: 30-day retention for generated files

### CI/CD Features
- Cross-platform testing (Ubuntu)
- Automatic dependency management
- Error handling and notifications
- Release asset management

## 📊 Data Fields

Each fishing location includes:

| Field | Description | Example |
|-------|-------------|---------|
| `name` | Location identifier | "AAR-465 Liberty Ship Wreck - Site 1" |
| `latitude` | Decimal degrees | 34.12345 |
| `longitude` | Decimal degrees | -77.98765 |
| `description` | Site details | "Liberty ship sunk 1942, good fishing" |
| `depth` | Depth in feet | 84.0 |
| `type` | Structure classification | "Shipwreck", "Artificial Reef" |
| `source_url` | Original data source | TidesPro.com URL |
| `scraped_at` | Extraction timestamp | ISO 8601 format |

## 🔍 Troubleshooting

### Common Issues

**No locations found:**
- Check internet connectivity
- Verify TidesPro.com website accessibility
- Site structure may have changed (update parsing logic)

**Environment setup fails:**
- Ensure Python 3.11+ is installed
- Check file permissions for venv creation
- Try deleting `venv/` folder and running again

**GPS device not showing waypoints:**
- Verify GPX file import was successful
- Check device supports GPX 1.1 format
- Some devices may show generic symbols instead of marine symbols

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes with appropriate documentation
4. Test thoroughly with `python main.py`
5. Submit a pull request

### Development Guidelines
- Follow existing code documentation patterns
- Add comprehensive docstrings for new functions
- Test with different TidesPro.com page structures
- Ensure cross-platform compatibility

## 📄 License

This project is open source. Please respect TidesPro.com's terms of service and implement respectful scraping practices.

## 🙏 Acknowledgments

- **TidesPro.com** for providing comprehensive fishing location data
- **Garmin** for GPX extensions documentation
- **North Carolina Division of Marine Fisheries** for artificial reef programs

## 📞 Support

For issues, questions, or contributions:
- 🐛 **Bug Reports**: Open GitHub issues with detailed descriptions
- 💡 **Feature Requests**: Discuss in GitHub issues
- 📖 **Documentation**: Refer to inline code documentation

---

**Happy Fishing! 🎣🌊**