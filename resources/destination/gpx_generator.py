#!/usr/bin/env python3
"""
GPX Generator Module

This module creates GPX (GPS Exchange Format) files from fishing location data
scraped from TidesPro.com. The generated files are optimized for marine GPS
devices, particularly Garmin units with Active Captain integration.

Key Features:
- GPX 1.1 standard compliance
- Garmin GPX Extensions v3 support
- Optimized waypoint names for 10-character display limits
- Marine-specific symbols (Shipwreck, Fish)
- Depth and temperature data integration
- Automatic categorization based on structure types

Author: NC Fishing Points Scraper
Version: 2.0
"""

import xml.etree.ElementTree as ET
from xml.dom.minidom import parseString
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional


class GPXGenerator:
    """
    Generate GPX files optimized for marine GPS devices from fishing location data.
    
    This class creates GPX 1.1 compliant files with Garmin extensions, specifically
    optimized for devices like the Garmin ECHOMAP UHD 1243xsv and Active Captain
    mobile application.
    
    Attributes:
        gpx_namespace (str): GPX 1.1 XML namespace
        garmin_namespace (str): Garmin GPX Extensions v3 namespace
    """
    
    def __init__(self):
        """Initialize GPX generator with required XML namespaces."""
        self.gpx_namespace = "http://www.topografix.com/GPX/1/1"
        self.garmin_namespace = "http://www.garmin.com/xmlschemas/GpxExtensions/v3"
    
    def create_gpx_file(self, locations: List[Dict], output_path: str) -> bool:
        """
        Create a GPX file from fishing location data optimized for marine GPS devices.
        
        This method generates a GPX 1.1 file with the following optimizations:
        - Short waypoint names (first part before space) for display compatibility
        - Full descriptive names preserved in description field
        - Marine-specific symbols (Shipwreck for wrecks, Fish for reefs/structures)
        - Garmin extensions for depth, temperature, and categorization
        - Proper XML formatting with namespace declarations
        
        Args:
            locations (List[Dict]): List of location dictionaries containing:
                - name (str): Full location name (e.g., "AAR-465 Garry Ennis Reef - Site 1")
                - latitude (float): Decimal degrees latitude
                - longitude (float): Decimal degrees longitude  
                - description (str, optional): Additional site description
                - type (str, optional): Structure type classification
                - depth (float, optional): Depth in feet
                - temperature (float, optional): Water temperature
            output_path (str): Absolute path where GPX file will be saved
            
        Returns:
            bool: True if file creation successful, False if error occurred
            
        Example:
            >>> generator = GPXGenerator()
            >>> locations = [{'name': 'AAR-465 Liberty Wreck', 'latitude': 34.5, 'longitude': -77.2}]
            >>> generator.create_gpx_file(locations, '/path/to/output.gpx')
            True
        """
        try:
            # Create GPX root element with required namespaces and schema declarations
            gpx = ET.Element("gpx")
            gpx.set("version", "1.1")
            gpx.set("creator", "NC Fishing Points Scraper")
            gpx.set("xmlns", self.gpx_namespace)  # GPX 1.1 namespace
            gpx.set("xmlns:gpxx", self.garmin_namespace)  # Garmin extensions namespace
            gpx.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
            gpx.set("xsi:schemaLocation", 
                   f"{self.gpx_namespace} http://www.topografix.com/GPX/1/1/gpx.xsd "
                   f"{self.garmin_namespace} {self.garmin_namespace}")
            
            # Add GPX metadata for file identification and timestamp
            metadata = ET.SubElement(gpx, "metadata")
            name = ET.SubElement(metadata, "name")
            name.text = "North Carolina Fishing Points"
            
            desc = ET.SubElement(metadata, "desc")
            desc.text = f"Fishing locations scraped from TidesPro.com on {datetime.now().strftime('%Y-%m-%d')}"
            
            time_elem = ET.SubElement(metadata, "time")
            time_elem.text = datetime.now().isoformat()
            
            # Process each fishing location as a waypoint
            for i, location in enumerate(locations):
                # Skip locations without valid coordinates
                if 'latitude' not in location or 'longitude' not in location:
                    continue
                
                # Create waypoint element with coordinates
                wpt = ET.SubElement(gpx, "wpt")
                wpt.set("lat", str(location['latitude']))
                wpt.set("lon", str(location['longitude']))
                
                # Generate optimized waypoint name for marine GPS display
                name_elem = ET.SubElement(wpt, "name")
                full_name = location.get('name', f'Fishing Point {i+1}')
                
                # Extract short name (first part before space) for 10-character GPS display limit
                # Example: "AAR-465 Garry Ennis Reef - Site 1" becomes "AAR-465"
                short_name = full_name.split(' ')[0] if full_name else f'Fishing Point {i+1}'
                name_elem.text = short_name
                
                # Build comprehensive description with full location details
                desc_parts = []
                
                # Add descriptive portion (everything after first identifier) to description
                if full_name != short_name and ' ' in full_name:
                    long_name = ' '.join(full_name.split(' ')[1:])  # "Garry Ennis Reef - Site 1"
                    if long_name:
                        desc_parts.append(long_name)
                
                # Append original site description if available
                if location.get('description'):
                    desc_parts.append(location['description'])
                
                # Add description element if we have content
                if desc_parts:
                    desc_elem = ET.SubElement(wpt, "desc")
                    desc_elem.text = '\n'.join(desc_parts)
                
                # Add marine-optimized symbols for GPS device display
                sym_elem = ET.SubElement(wpt, "sym")
                
                # Intelligent symbol assignment based on structure type
                # Priority: wreck detection > structure type > default fishing
                if (full_name != short_name and ' ' in full_name and 
                    'wreck' in ' '.join(full_name.split(' ')[1:]).lower()):
                    # Shipwreck symbol for better Garmin/Active Captain compatibility
                    sym_elem.text = "Shipwreck"
                else:
                    # Fish symbol for all other structures (reefs, artificial reefs, etc.)
                    # More universally supported than "Reef" symbol
                    sym_elem.text = "Fish"
                
                # Add waypoint type for additional GPS categorization
                type_elem = ET.SubElement(wpt, "type")
                type_elem.text = location.get('type', 'Fishing')
                
                # Add Garmin GPX Extensions for enhanced marine GPS functionality
                if any(key in location for key in ['type', 'depth', 'temperature']):
                    extensions = ET.SubElement(wpt, "extensions")
                    wpt_ext = ET.SubElement(extensions, "gpxx:WaypointExtension")
                    
                    # Add structure type categories for GPS filtering/search
                    if location.get('type'):
                        categories = ET.SubElement(wpt_ext, "gpxx:Categories")
                        category = ET.SubElement(categories, "gpxx:Category")
                        category.text = location['type']
                    
                    # Add depth information in feet for fishing applications
                    if location.get('depth'):
                        depth = ET.SubElement(wpt_ext, "gpxx:Depth")
                        depth.text = str(location['depth'])
                    
                    # Add water temperature data if available
                    if location.get('temperature'):
                        temp = ET.SubElement(wpt_ext, "gpxx:Temperature")
                        temp.text = str(location['temperature'])
            
            # Generate formatted XML output
            rough_string = ET.tostring(gpx, encoding='unicode')
            reparsed = parseString(rough_string)
            pretty_xml = reparsed.toprettyxml(indent="  ")
            
            # Clean up XML formatting by removing empty lines
            pretty_lines = [line for line in pretty_xml.split('\n') if line.strip()]
            pretty_xml = '\n'.join(pretty_lines)
            
            # Write GPX file with UTF-8 encoding for international character support
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(pretty_xml)
            
            # Report successful creation with waypoint count
            valid_locations = len([l for l in locations if 'latitude' in l and 'longitude' in l])
            print(f"✓ GPX file created: {output_path}")
            print(f"✓ Added {valid_locations} waypoints with marine GPS optimization")
            return True
            
        except Exception as e:
            print(f"✗ Error creating GPX file: {e}")
            return False