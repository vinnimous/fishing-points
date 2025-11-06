#!/usr/bin/env python3
"""
North Carolina Fishing Points Scraper

This script fetches fishing location data from TidesPro.com for North Carolina
locations and generates GPX files with waypoints for fishing spots.
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


# Configuration - URLs to scrape for fishing location data
FISHING_URLS = [
    "https://www.tidespro.com/fishing/us/north-carolina/estuarine",
    "https://www.tidespro.com/fishing/us/north-carolina/long-bay",
    "https://www.tidespro.com/fishing/us/north-carolina/onslow-bay",
    "https://www.tidespro.com/fishing/us/north-carolina/outer-banks",
    "https://www.tidespro.com/fishing/us/north-carolina/raleigh-bay"
]

# Scraper settings
SCRAPER_CONFIG = {
    'delay_between_requests': 1.0,
    'request_timeout': 30,
    'max_retries': 3,
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}


class FishingPointScraper:
    """Scraper for TidesPro fishing location data."""
    
    def __init__(self):
        self.session = requests.Session()
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
        Fetch a web page and return BeautifulSoup object.
        
        Args:
            url: URL to fetch
            delay: Delay between requests in seconds (uses config default if None)
            
        Returns:
            BeautifulSoup object or None if failed
        """
        if delay is None:
            delay = SCRAPER_CONFIG['delay_between_requests']
            
        try:
            print(f"Fetching: {url}")
            time.sleep(delay)  # Be respectful to the server
            
            response = self.session.get(url, timeout=SCRAPER_CONFIG['request_timeout'])
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')
            print(f"✓ Successfully fetched {url}")
            return soup
            
        except requests.RequestException as e:
            print(f"✗ Error fetching {url}: {e}")
            return None
        except Exception as e:
            print(f"✗ Unexpected error parsing {url}: {e}")
            return None
    
    def extract_coordinates(self, text: str) -> Optional[Tuple[float, float]]:
        """
        Extract latitude and longitude from text (decimal degrees only).
        
        Args:
            text: Text containing coordinates in decimal degrees format
            
        Returns:
            Tuple of (latitude, longitude) or None
        """
        # Only extract decimal degrees: 35.123456, -75.654321
        pattern = r'(-?\d+\.?\d*),\s*(-?\d+\.?\d*)'
        
        matches = re.findall(pattern, text)
        if matches:
            match = matches[0]
            try:
                lat, lon = float(match[0]), float(match[1])
                
                # Validate coordinate ranges
                if -90 <= lat <= 90 and -180 <= lon <= 180:
                    return (lat, lon)
                    
            except (ValueError, IndexError):
                pass
                    
        return None
    
    def parse_fishing_locations(self, soup, base_url: str) -> List[Dict]:
        """
        Parse fishing locations from a TidesPro page.
        
        Args:
            soup: BeautifulSoup object of the page
            base_url: Base URL for resolving relative links
            
        Returns:
            List of fishing location dictionaries
        """
        locations = []
        
        # Look for the main data table
        table = soup.find('table', class_=['table', 'table-hover', 'table-sm', 'table-bordered'])
        if not table:
            # Fallback: find any table
            table = soup.find('table')
            
        if table:
            print("Found fishing locations table")
            tbody = table.find('tbody')
            if tbody:
                rows = tbody.find_all('tr')
                print(f"Found {len(rows)} data rows in table")
                
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 4:  # At least Name, Description, and 2 coordinate columns
                        location_data = self.extract_location_from_table_row(cells)
                        if location_data:
                            locations.append(location_data)
            else:
                print("No tbody found, checking all rows")
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 4:  # At least Name, Description, and 2 coordinate columns
                        location_data = self.extract_location_from_table_row(cells)
                        if location_data:
                            locations.append(location_data)
        else:
            print("No fishing locations table found, trying fallback methods")
            # Fallback methods for other page structures
            locations.extend(self.extract_from_scripts(soup, base_url))
        
        print(f"Found {len(locations)} fishing locations")
        return locations
    
    def extract_location_from_table_row(self, cells) -> Optional[Dict]:
        """Extract location data from table row cells."""
        if len(cells) < 4:
            return None
            
        try:
            # Extract name from first cell
            name_cell = cells[0]
            name = name_cell.get_text(strip=True)
            # Remove the map button text and clean up
            name = re.sub(r'\s*$', '', name)  # Remove trailing whitespace
            if not name:
                return None
            
            # Extract description from second cell
            desc_cell = cells[1]
            description = desc_cell.get_text(strip=True)
            # Clean up description - extract only the first part before unwanted text
            description = re.sub(r'Average Depth:.*$', '', description, flags=re.DOTALL)
            description = re.sub(r'Deployed:.*$', '', description, flags=re.DOTALL)
            description = re.sub(r'Depth:.*$', '', description, flags=re.DOTALL)
            description = re.sub(r'Tides & Solunars.*$', '', description, flags=re.DOTALL)
            description = re.sub(r'\[1\].*$', '', description)
            description = description.strip()
            
            # Dynamically find coordinate columns by looking for DD spans and depth column
            lat_cell = None
            lon_cell = None
            depth = None
            
            # Check each cell for coordinate data (DD spans) and depth
            for i, cell in enumerate(cells):
                # Check for coordinate data
                dd_span = cell.find('span', class_='dd')
                if dd_span:
                    coord_value = dd_span.get_text(strip=True)
                    try:
                        coord_float = float(coord_value)
                        # Latitude is typically positive for North (25-50 range for NC)
                        # Longitude is typically negative for West (-85 to -75 range for NC)
                        if 25 <= coord_float <= 50:  # Likely latitude
                            lat_cell = cell
                        elif -85 <= coord_float <= -75:  # Likely longitude  
                            lon_cell = cell
                    except ValueError:
                        continue
                
                # Check for depth data (skip first two cells which are name and description)
                elif i >= 2:
                    cell_text = cell.get_text(strip=True)
                    # Look for depth patterns like "84 ft", "25 feet", "30m", etc.
                    depth_match = re.search(r'(\d+(?:\.\d+)?)\s*(ft|feet|fathoms|fath|f|m|meters?)\b', cell_text, re.IGNORECASE)
                    if depth_match and not depth:  # Only capture first depth found
                        depth_value = float(depth_match.group(1))
                        depth_unit = depth_match.group(2).lower()
                        
                        # Convert to feet for consistency
                        if depth_unit in ['m', 'meter', 'meters']:
                            depth_value = depth_value * 3.28084  # meters to feet
                        elif depth_unit in ['fathoms', 'fath', 'f']:
                            depth_value = depth_value * 6  # fathoms to feet
                            
                        depth = depth_value  # Store as numeric value in feet
            
            # Get decimal degrees (DD) values from found coordinate cells
            if lat_cell and lon_cell:
                lat_dd_span = lat_cell.find('span', class_='dd')
                lon_dd_span = lon_cell.find('span', class_='dd')
                
                if lat_dd_span and lon_dd_span:
                    try:
                        latitude = float(lat_dd_span.get_text(strip=True))
                        longitude = float(lon_dd_span.get_text(strip=True))
                        
                        location = {
                            'name': name,
                            'description': description,
                            'latitude': latitude,
                            'longitude': longitude
                        }
                        
                        # Add depth if available
                        if depth:
                            location['depth'] = depth
                        
                        # Set sym and type based on description content
                        description_lower = description.lower()
                        if 'wreck' in description_lower:
                            location['sym'] = 'Wreck'
                            location['type'] = 'Shipwreck'
                        elif 'concrete' in description_lower:
                            location['sym'] = 'Reef'
                            location['type'] = 'Concrete Reef'
                        else:
                            location['sym'] = 'Reef'
                            location['type'] = 'Artificial Reef'
                        
                        depth_info = f" (depth: {depth:.0f} ft)" if depth else ""
                        print(f"Extracted: {name} at {latitude}, {longitude}{depth_info}")
                        return location
                        
                    except (ValueError, AttributeError) as e:
                        print(f"Error parsing coordinates: {e}")
                        return None
            else:
                print(f"Could not find DD coordinates for {name}")
                return None
                
        except Exception as e:
            print(f"Error extracting location from row: {e}")
            return None

    def extract_from_scripts(self, soup, base_url: str = None) -> List[Dict]:
        """Extract location data from JavaScript/JSON in script tags."""
        locations = []
        
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string:
                location_data = self.extract_location_from_script(script.string, base_url)
                if location_data:
                    locations.extend(location_data)
        
        return locations


    
    def extract_location_from_script(self, script_content: str, base_url: str = None) -> List[Dict]:
        """Extract location data from JavaScript/JSON in script tags."""
        locations = []
        
        # Look for JSON-like coordinate data
        coord_patterns = [
            r'"lat":\s*(-?\d+\.?\d*),?\s*"lng?":\s*(-?\d+\.?\d*)',
            r'"latitude":\s*(-?\d+\.?\d*),?\s*"longitude":\s*(-?\d+\.?\d*)',
            r'lat:\s*(-?\d+\.?\d*),?\s*lng?:\s*(-?\d+\.?\d*)',
        ]
        
        for pattern in coord_patterns:
            matches = re.findall(pattern, script_content)
            for match in matches:
                try:
                    lat, lon = float(match[0]), float(match[1])
                    if -90 <= lat <= 90 and -180 <= lon <= 180:
                        locations.append({
                            'latitude': lat,
                            'longitude': lon,
                            'name': 'Fishing Location',
                            'source': base_url if base_url else 'script'
                        })
                except ValueError:
                    continue
        
        return locations
    
    def scrape_urls(self, urls: List[str]) -> List[Dict]:
        """
        Scrape multiple URLs for fishing location data.
        
        Args:
            urls: List of URLs to scrape
            
        Returns:
            Combined list of all fishing locations found
        """
        all_locations = []
        
        for url in urls:
            soup = self.fetch_page(url)
            if soup:
                locations = self.parse_fishing_locations(soup, url)
                
                # Add metadata to each location
                for location in locations:
                    location['source_url'] = url
                    location['scraped_at'] = datetime.now().isoformat()
                    
                    # Parse URL to extract location info
                    # Expected format: https://www.tidespro.com/fishing/us/{state}/{type}
                    parsed_url = urlparse(url)
                    path_parts = parsed_url.path.strip('/').split('/')
                    
                    if len(path_parts) >= 4 and path_parts[0] == 'fishing' and path_parts[1] == 'us':
                        # Extract state and convert to proper case
                        state_slug = path_parts[2]
                        state_name = ' '.join(word.capitalize() for word in state_slug.split('-'))
                        location['state'] = state_name
                        location['country'] = 'United States'
                        
                        # Extract type/region if available
                        if len(path_parts) >= 5:
                            type_slug = path_parts[3]
                            type_name = ' '.join(word.capitalize() for word in type_slug.split('-'))
                            location['type'] = type_name
                
                all_locations.extend(locations)
        
        return all_locations





def scraper():
    """Main function to run the scraper and generate GPX files."""
    
    print("=== North Carolina Fishing Points Scraper ===")
    print(f"Scraping {len(FISHING_URLS)} URLs...")
    
    # Initialize scraper
    scraper = FishingPointScraper()
    
    # Scrape all URLs
    all_locations = scraper.scrape_urls(FISHING_URLS)
    
    if not all_locations:
        print("⚠ No fishing locations found. The website structure may have changed.")
        print("Consider manually inspecting the URLs to update the parsing logic.")
        return
    
    print(f"\n✓ Total locations found: {len(all_locations)}")
    
    # Remove duplicates based on coordinates
    unique_locations = []
    seen_coords = set()
    
    for location in all_locations:
        if 'latitude' in location and 'longitude' in location:
            coord_key = (round(location['latitude'], 6), round(location['longitude'], 6))
            if coord_key not in seen_coords:
                seen_coords.add(coord_key)
                unique_locations.append(location)
    
    print(f"✓ Unique locations after deduplication: {len(unique_locations)}")
    
    # Create output directory in parent folder's point_files
    project_root = Path(__file__).parent.parent.parent  # Go up to project root
    output_dir = project_root / "point_files"
    output_dir.mkdir(exist_ok=True)
    
    # Generate GPX file
    gpx_generator = GPXGenerator()
    
    output_file = output_dir / f"nc_fishing_points_{datetime.now().strftime('%Y%m%d_%H%M%S')}.gpx"
    
    success = gpx_generator.create_gpx_file(unique_locations, str(output_file))
    
    if success:
        # Also save raw data as JSON for debugging/analysis
        json_file = output_dir / f"nc_fishing_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(unique_locations, f, indent=2, default=str)
        print(f"✓ Raw data saved: {json_file}")
        
        return unique_locations
    else:
        print("✗ Failed to create GPX file")
        return []


if __name__ == "__main__":
    locations = scraper()
    if locations:
        print(f"\n🎯 Successfully scraped {len(locations)} fishing locations!")
    else:
        print("\n❌ No locations were scraped.")
        exit(1)
