#!/usr/bin/env python3
"""
North Carolina Fishing Points Scraper Module

This module scrapes fishing location data from TidesPro.com for all North Carolina
coastal regions and processes it into structured data for GPS applications.

The scraper handles:
- Dynamic table parsing across different TidesPro.com page layouts
- Coordinate extraction in decimal degrees format only
- Depth data processing and unit conversion to feet
- Structure type classification (wrecks, reefs, artificial reefs)
- Intelligent deduplication based on coordinate proximity
- Marine GPS optimization for symbol assignment

Supported NC Regions:
- Estuarine fishing locations
- Long Bay fishing locations  
- Onslow Bay fishing locations
- Outer Banks fishing locations
- Raleigh Bay fishing locations

Author: NC Fishing Points Scraper
Version: 2.0
Dependencies: requests, beautifulsoup4, lxml
"""

import requests
import json
import time
import re
from bs4 import BeautifulSoup
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from urllib.parse import urljoin, urlparse
from datetime import datetime
from ..destination.gpx_generator import GPXGenerator


# TidesPro.com fishing location URLs for North Carolina coastal regions
FISHING_URLS = [
    "https://www.tidespro.com/fishing/us/north-carolina/estuarine",    # Inshore/estuarine waters
    "https://www.tidespro.com/fishing/us/north-carolina/long-bay",     # Long Bay offshore area
    "https://www.tidespro.com/fishing/us/north-carolina/onslow-bay",   # Onslow Bay offshore area
    "https://www.tidespro.com/fishing/us/north-carolina/outer-banks",  # Outer Banks region
    "https://www.tidespro.com/fishing/us/north-carolina/raleigh-bay"   # Raleigh Bay offshore area
]

# Web scraping configuration for respectful and reliable data extraction
SCRAPER_CONFIG = {
    'delay_between_requests': 1.0,  # Respectful delay between requests (seconds)
    'request_timeout': 30,          # HTTP request timeout (seconds)
    'max_retries': 3,              # Maximum retry attempts for failed requests
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}


class FishingPointScraper:
    """
    Web scraper for TidesPro.com fishing location data with advanced parsing capabilities.
    
    This class implements robust scraping with:
    - Persistent HTTP sessions for connection reuse
    - Respectful request throttling with configurable delays
    - Dynamic table structure detection and parsing
    - Coordinate validation and format standardization
    - Depth data extraction with unit conversion
    - Structure type classification for marine GPS compatibility
    - Comprehensive error handling and retry logic
    
    Attributes:
        session (requests.Session): Persistent HTTP session with appropriate headers
    """
    
    def __init__(self):
        """Initialize scraper with persistent session and browser-like headers."""
        self.session = requests.Session()
        
        # Set headers to mimic a real browser for better site compatibility
        self.session.headers.update({
            'User-Agent': SCRAPER_CONFIG['user_agent'],
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
    def fetch_page(self, url: str, delay: float = None):
        """
        Fetch a web page with respectful throttling and error handling.
        
        Implements respectful web scraping practices including request delays,
        proper error handling, and timeout management. Uses persistent session
        for connection reuse and efficiency.
        
        Args:
            url (str): Target URL to fetch
            delay (float, optional): Delay between requests in seconds. 
                                   Uses SCRAPER_CONFIG default if None.
            
        Returns:
            BeautifulSoup: Parsed HTML document or None if request failed
            
        Raises:
            None: All exceptions are caught and logged, returns None on failure
        """
        if delay is None:
            delay = SCRAPER_CONFIG['delay_between_requests']
            
        try:
            print(f"Fetching: {url}")
            
            # Respectful delay to avoid overwhelming the server
            time.sleep(delay)
            
            # Fetch page with configured timeout
            response = self.session.get(url, timeout=SCRAPER_CONFIG['request_timeout'])
            response.raise_for_status()

            # Parse HTML with lxml parser for better performance
            soup = BeautifulSoup(response.content, 'html.parser')
            print(f"✓ Successfully fetched {url}")
            return soup
            
        except requests.RequestException as e:
            print(f"✗ HTTP error fetching {url}: {e}")
            return None
        except Exception as e:
            print(f"✗ Unexpected error parsing {url}: {e}")
            return None
    
    def extract_coordinates(self, text: str) -> Optional[Tuple[float, float]]:
        """
        Extract latitude and longitude coordinates from text in decimal degrees format.
        
        This method specifically extracts decimal degree coordinates (DD format) and
        validates them against realistic geographical bounds. Other coordinate formats
        (DMS, DDM) are intentionally not supported to maintain consistency.
        
        Args:
            text (str): Text potentially containing coordinates in decimal degrees format
                       Example: "35.123456, -75.654321"
            
        Returns:
            Optional[Tuple[float, float]]: Tuple of (latitude, longitude) if valid 
                                          coordinates found, None if not found or invalid
            
        Example:
            >>> scraper.extract_coordinates("Location at 34.5678, -77.1234")
            (34.5678, -77.1234)
        """
        # Regex pattern for decimal degrees: optional minus, digits, optional decimal point and digits
        pattern = r'(-?\d+\.?\d*),\s*(-?\d+\.?\d*)'
        
        matches = re.findall(pattern, text)
        if matches:
            match = matches[0]
            try:
                lat, lon = float(match[0]), float(match[1])
                
                # Validate coordinates are within valid geographical ranges
                if -90 <= lat <= 90 and -180 <= lon <= 180:
                    return (lat, lon)
                    
            except (ValueError, IndexError):
                pass
                    
        return None
    
    def parse_fishing_locations(self, soup, base_url: str) -> List[Dict]:
        """
        Parse fishing locations from TidesPro.com page with dynamic table detection.
        
        This method implements robust parsing that adapts to different table structures
        used across TidesPro.com pages. It prioritizes table-based data extraction
        but falls back to JavaScript/JSON parsing when needed.
        
        Args:
            soup (BeautifulSoup): Parsed HTML document from TidesPro.com
            base_url (str): Base URL for resolving relative links and metadata
            
        Returns:
            List[Dict]: List of fishing location dictionaries containing:
                - name: Location identifier and description
                - latitude/longitude: Decimal degree coordinates  
                - description: Cleaned location description
                - depth: Depth in feet (if available)
                - type/sym: Marine GPS classification data
        """
        locations = []
        
        # Primary method: Look for Bootstrap-styled data tables (most common)
        table = soup.find('table', class_=['table', 'table-hover', 'table-sm', 'table-bordered'])
        if not table:
            # Fallback: Find any table element
            table = soup.find('table')
            
        if table:
            print("✓ Found fishing locations table")
            
            # Try structured tbody approach first (proper HTML tables)
            tbody = table.find('tbody')
            if tbody:
                rows = tbody.find_all('tr')
                print(f"✓ Found {len(rows)} data rows in tbody")
                
                for row in rows:
                    cells = row.find_all('td')
                    # Minimum 4 columns: Name, Description, Latitude, Longitude
                    if len(cells) >= 4:
                        location_data = self.extract_location_from_table_row(cells)
                        if location_data:
                            locations.append(location_data)
            else:
                # Fallback: Parse all table rows (less structured tables)
                print("⚠ No tbody found, parsing all table rows")
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 4:
                        location_data = self.extract_location_from_table_row(cells)
                        if location_data:
                            locations.append(location_data)
        else:
            print("⚠ No fishing locations table found, trying JavaScript extraction")
            # Last resort: Extract from JavaScript/JSON embedded in page
            locations.extend(self.extract_from_scripts(soup, base_url))
        
        print(f"✓ Successfully extracted {len(locations)} fishing locations")
        return locations
    
    def extract_location_from_table_row(self, cells) -> Optional[Dict]:
        """
        Extract comprehensive fishing location data from table row cells.
        
        This method handles dynamic table structures by intelligently detecting:
        - Location names and cleaning unwanted UI elements
        - Descriptive text with automatic filtering of metadata
        - Decimal degree coordinates from DD-formatted spans
        - Depth measurements with unit conversion to feet
        - Structure type classification for marine GPS symbols
        
        Args:
            cells (List): BeautifulSoup table cell elements from a row
            
        Returns:
            Optional[Dict]: Location dictionary with standardized fields or None if invalid
        """
        # Validate minimum table structure (4 columns: name, description, lat, lon)
        if len(cells) < 4:
            return None
            
        try:
            # Extract and clean location name from first cell
            name_cell = cells[0]
            name = name_cell.get_text(strip=True)
            
            # Clean up name by removing UI elements and excess whitespace
            name = re.sub(r'\s+', ' ', name).strip()  # Normalize whitespace
            if not name:
                return None
            
            # Extract and clean description from second cell
            desc_cell = cells[1]
            description = desc_cell.get_text(strip=True)
            
            # Remove unwanted metadata from description using comprehensive regex patterns
            # These patterns filter out deployment dates, depth info, and reference links
            cleanup_patterns = [
                r'Average Depth:.*$',      # Remove depth metadata
                r'Deployed:.*$',           # Remove deployment dates
                r'Depth:.*$',              # Remove standalone depth info
                r'Tides & Solunars.*$',    # Remove navigation links
                r'\[1\].*$',               # Remove reference links
                r'Last Updated:.*$',       # Remove update timestamps
            ]
            
            for pattern in cleanup_patterns:
                description = re.sub(pattern, '', description, flags=re.DOTALL)
            
            description = description.strip()
            
            # Dynamic coordinate and depth detection across variable table structures
            lat_cell = None
            lon_cell = None  
            depth = None
            
            # Analyze each cell to identify coordinates and depth data
            for i, cell in enumerate(cells):
                # Primary method: Look for decimal degree (DD) spans in coordinate cells
                dd_span = cell.find('span', class_='dd')
                if dd_span:
                    coord_value = dd_span.get_text(strip=True)
                    try:
                        coord_float = float(coord_value)
                        
                        # Classify coordinates based on North Carolina geographical bounds
                        # NC latitude range: ~25°-50°N, longitude range: ~85°-75°W
                        if 25 <= coord_float <= 50:
                            lat_cell = cell  # Positive value indicates latitude (North)
                        elif -85 <= coord_float <= -75:
                            lon_cell = cell  # Negative value indicates longitude (West)
                            
                    except ValueError:
                        continue
                
                # Secondary method: Extract depth data from non-coordinate cells
                elif i >= 2:  # Skip name and description columns
                    cell_text = cell.get_text(strip=True)
                    
                    # Comprehensive depth pattern matching with unit conversion
                    depth_pattern = r'(\d+(?:\.\d+)?)\s*(ft|feet|fathoms|fath|f|m|meters?)\b'
                    depth_match = re.search(depth_pattern, cell_text, re.IGNORECASE)
                    
                    if depth_match and not depth:  # Use first depth value found
                        depth_value = float(depth_match.group(1))
                        depth_unit = depth_match.group(2).lower()
                        
                        # Standardize all depth measurements to feet for consistency
                        if depth_unit in ['m', 'meter', 'meters']:
                            depth_value = depth_value * 3.28084  # Convert meters to feet
                        elif depth_unit in ['fathoms', 'fath', 'f']:
                            depth_value = depth_value * 6        # Convert fathoms to feet
                        # 'ft', 'feet' require no conversion
                            
                        depth = depth_value
            
            # Extract final coordinate values and construct location dictionary
            if lat_cell and lon_cell:
                lat_dd_span = lat_cell.find('span', class_='dd')
                lon_dd_span = lon_cell.find('span', class_='dd')
                
                if lat_dd_span and lon_dd_span:
                    try:
                        latitude = float(lat_dd_span.get_text(strip=True))
                        longitude = float(lon_dd_span.get_text(strip=True))
                        
                        # Build standardized location dictionary
                        location = {
                            'name': name,
                            'description': description,
                            'latitude': latitude,
                            'longitude': longitude
                        }
                        
                        # Add depth data if extracted successfully
                        if depth:
                            location['depth'] = depth
                        
                        # Intelligent structure classification for marine GPS symbols
                        # Analyze combined name and description for structure type keywords
                        combined_text = f"{name} {description}".lower()
                        
                        if 'wreck' in combined_text:
                            location['sym'] = 'Wreck'
                            location['type'] = 'Shipwreck'
                        elif 'concrete' in combined_text:
                            location['sym'] = 'Reef'
                            location['type'] = 'Concrete Reef'
                        else:
                            # Default classification for artificial reefs and general structures
                            location['sym'] = 'Reef'
                            location['type'] = 'Artificial Reef'
                        
                        # Log successful extraction with optional depth information
                        depth_info = f" (depth: {depth:.0f} ft)" if depth else ""
                        print(f"✓ Extracted: {name} at {latitude}, {longitude}{depth_info}")
                        return location
                        
                    except (ValueError, AttributeError) as e:
                        print(f"✗ Error parsing coordinates for {name}: {e}")
                        return None
            else:
                print(f"⚠ Could not find DD coordinates for {name}")
                return None
                
        except Exception as e:
            print(f"✗ Unexpected error extracting location from row: {e}")
            return None

    def extract_from_scripts(self, soup, base_url: str = None) -> List[Dict]:
        """
        Fallback method: Extract location data from embedded JavaScript/JSON.
        
        This method serves as a backup when table-based parsing fails, searching
        for coordinate data embedded in JavaScript variables or JSON objects within
        script tags. Less reliable than table parsing but useful for dynamic sites.
        
        Args:
            soup (BeautifulSoup): Parsed HTML document
            base_url (str, optional): Base URL for metadata attribution
            
        Returns:
            List[Dict]: List of locations found in JavaScript/JSON, may be incomplete
        """
        locations = []
        
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string:
                location_data = self.extract_location_from_script(script.string, base_url)
                if location_data:
                    locations.extend(location_data)
        
        return locations

    def extract_location_from_script(self, script_content: str, base_url: str = None) -> List[Dict]:
        """
        Extract coordinate pairs from JavaScript code or JSON objects.
        
        Searches for common coordinate variable patterns used in mapping
        applications and geographic data visualization.
        
        Args:
            script_content (str): JavaScript source code content
            base_url (str, optional): Base URL for source attribution
            
        Returns:
            List[Dict]: Basic location dictionaries with coordinates only
        """
        locations = []
        
        # Regex patterns for common coordinate formats in JavaScript/JSON
        coord_patterns = [
            r'"lat":\s*(-?\d+\.?\d*),?\s*"lng?":\s*(-?\d+\.?\d*)',          # JSON lat/lng
            r'"latitude":\s*(-?\d+\.?\d*),?\s*"longitude":\s*(-?\d+\.?\d*)', # JSON latitude/longitude  
            r'lat:\s*(-?\d+\.?\d*),?\s*lng?:\s*(-?\d+\.?\d*)',              # JavaScript lat/lng
        ]
        
        for pattern in coord_patterns:
            matches = re.findall(pattern, script_content)
            for match in matches:
                try:
                    lat, lon = float(match[0]), float(match[1])
                    
                    # Validate coordinate ranges
                    if -90 <= lat <= 90 and -180 <= lon <= 180:
                        locations.append({
                            'latitude': lat,
                            'longitude': lon,
                            'name': 'Fishing Location',  # Generic name for script-extracted data
                            'source': base_url if base_url else 'script'
                        })
                except ValueError:
                    continue
        
        return locations
    
    def scrape_urls(self, urls: List[str]) -> List[Dict]:
        """
        Orchestrate scraping across multiple TidesPro.com URLs with metadata enrichment.
        
        This method processes each URL sequentially with respectful delays, extracts
        location data, and enriches each record with source metadata including
        state/region information parsed from URL structure.
        
        Args:
            urls (List[str]): List of TidesPro.com URLs to scrape
            
        Returns:
            List[Dict]: Combined list of all fishing locations with metadata:
                - source_url: Original page URL
                - scraped_at: ISO timestamp of extraction
                - state: Extracted state name from URL
                - country: Fixed as 'United States'
                - type: Region name if available in URL path
        """
        all_locations = []
        
        for url in urls:
            soup = self.fetch_page(url)
            if soup:
                locations = self.parse_fishing_locations(soup, url)
                
                # Enrich each location with comprehensive metadata
                for location in locations:
                    # Add scraping metadata
                    location['source_url'] = url
                    location['scraped_at'] = datetime.now().isoformat()
                    
                    # Parse URL structure to extract geographical information
                    # Expected TidesPro URL format: https://www.tidespro.com/fishing/us/{state}/{region}
                    parsed_url = urlparse(url)
                    path_parts = parsed_url.path.strip('/').split('/')
                    
                    if len(path_parts) >= 4 and path_parts[0] == 'fishing' and path_parts[1] == 'us':
                        # Extract and format state name from URL slug
                        state_slug = path_parts[2]
                        state_name = ' '.join(word.capitalize() for word in state_slug.split('-'))
                        location['state'] = state_name
                        location['country'] = 'United States'
                        
                        # Extract and format region/type information if available
                        if len(path_parts) >= 4:
                            region_slug = path_parts[3]
                            region_name = ' '.join(word.capitalize() for word in region_slug.split('-'))
                            # Only override type if not already set by structure classification
                            if 'type' not in location:
                                location['region'] = region_name
                
                all_locations.extend(locations)
        
        return all_locations





def scraper():
    """
    Main scraper orchestration function for North Carolina fishing points.
    
    This function coordinates the complete scraping workflow:
    1. Initializes the scraper with proper configuration
    2. Scrapes all configured TidesPro.com URLs for NC regions
    3. Deduplicates locations based on coordinate proximity
    4. Generates marine GPS-optimized GPX files
    5. Exports raw JSON data for analysis and debugging
    
    Returns:
        List[Dict]: List of unique fishing locations with full metadata,
                   empty list if scraping fails
    
    Output Files:
        - {timestamp}_nc_fishing_points.gpx: Marine GPS waypoint file
        - {timestamp}_nc_fishing_data.json: Raw scraped data with metadata
    """
    
    print("=== North Carolina Fishing Points Scraper ===")
    print(f"🎯 Target regions: {len(FISHING_URLS)} TidesPro.com pages")
    print("🌊 Extracting: Wrecks, Reefs, and Artificial Structures")
    
    # Initialize scraper with configured session and headers
    scraper_instance = FishingPointScraper()
    
    # Execute comprehensive scraping across all NC regions
    all_locations = scraper_instance.scrape_urls(FISHING_URLS)
    
    if not all_locations:
        print("⚠ No fishing locations found. Possible causes:")
        print("  • Website structure may have changed")
        print("  • Network connectivity issues")
        print("  • Site may be blocking requests")
        print("💡 Consider manually inspecting URLs to update parsing logic")
        return []
    
    print(f"\n✓ Total locations extracted: {len(all_locations)}")
    
    # Intelligent deduplication based on coordinate proximity
    # Uses 6 decimal places precision (~0.1 meter accuracy)
    unique_locations = []
    seen_coordinates = set()
    
    for location in all_locations:
        if 'latitude' in location and 'longitude' in location:
            # Create coordinate key with high precision for deduplication
            coord_key = (round(location['latitude'], 6), round(location['longitude'], 6))
            
            if coord_key not in seen_coordinates:
                seen_coordinates.add(coord_key)
                unique_locations.append(location)
    
    duplicates_removed = len(all_locations) - len(unique_locations)
    print(f"✓ Unique locations after deduplication: {len(unique_locations)}")
    if duplicates_removed > 0:
        print(f"  Removed {duplicates_removed} duplicate coordinates")
    
    # Setup output directory structure
    project_root = Path(__file__).parent.parent.parent  # Navigate to project root
    output_dir = project_root / "point_files"
    output_dir.mkdir(exist_ok=True)
    
    # Generate timestamp for consistent file naming
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Create marine GPS-optimized GPX file
    print(f"\n🗺️ Generating marine GPS files...")
    gpx_generator = GPXGenerator()
    gpx_file = output_dir / f"nc_fishing_points_{timestamp}.gpx"
    
    gpx_success = gpx_generator.create_gpx_file(unique_locations, str(gpx_file))
    
    if gpx_success:
        # Export raw JSON data for analysis, debugging, and API development
        json_file = output_dir / f"nc_fishing_data_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(unique_locations, f, indent=2, default=str, ensure_ascii=False)
        print(f"✓ Raw data exported: {json_file}")
        
        # Success summary
        print(f"\n🎉 Scraping completed successfully!")
        print(f"📁 Files saved to: {output_dir}")
        print(f"🎣 Ready for GPS import: {gpx_file.name}")
        
        return unique_locations
    else:
        print("✗ GPX file generation failed")
        return []


if __name__ == "__main__":
    """
    Direct execution entry point for standalone scraping.
    
    When run directly (not imported), executes the complete scraping workflow
    and provides appropriate exit codes for automation and error handling.
    """
    locations = scraper()
    
    if locations:
        print(f"\n🎯 Success! Scraped {len(locations)} unique fishing locations")
        print("💾 Files ready for GPS import and data analysis")
    else:
        print("\n❌ Scraping failed - no locations were extracted")
        print("🔍 Check network connectivity and site structure")
        exit(1)
