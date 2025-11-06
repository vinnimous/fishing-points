#!/usr/bin/env python3
"""
GPX Generator

This module handles the creation of GPX files from fishing location data.
"""

import xml.etree.ElementTree as ET
from xml.dom.minidom import parseString
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional


class GPXGenerator:
    """Generate GPX files from fishing location data."""
    
    def __init__(self):
        # Schema path is handled internally - look for gpx.xsd in the same directory
        self.schema_path = Path(__file__).parent / "gpx.xsd"
        self.gpx_namespace = "http://www.topografix.com/GPX/1/1"
        self.garmin_namespace = "http://www.garmin.com/xmlschemas/GpxExtensions/v3"
    
    def create_gpx_file(self, locations: List[Dict], output_path: str) -> bool:
        """
        Create a GPX file from fishing location data.
        
        Args:
            locations: List of location dictionaries
            output_path: Path to save the GPX file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create root element
            gpx = ET.Element("gpx")
            gpx.set("version", "1.1")
            gpx.set("creator", "NC Fishing Points Scraper")
            gpx.set("xmlns", self.gpx_namespace)
            gpx.set("xmlns:gpxx", self.garmin_namespace)
            gpx.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
            gpx.set("xsi:schemaLocation", 
                   f"{self.gpx_namespace} http://www.topografix.com/GPX/1/1/gpx.xsd "
                   f"{self.garmin_namespace} {self.garmin_namespace}")
            
            # Add metadata
            metadata = ET.SubElement(gpx, "metadata")
            name = ET.SubElement(metadata, "name")
            name.text = "North Carolina Fishing Points"
            
            desc = ET.SubElement(metadata, "desc")
            desc.text = f"Fishing locations scraped from TidesPro.com on {datetime.now().strftime('%Y-%m-%d')}"
            
            time_elem = ET.SubElement(metadata, "time")
            time_elem.text = datetime.now().isoformat()
            
            # Add waypoints
            for i, location in enumerate(locations):
                if 'latitude' not in location or 'longitude' not in location:
                    continue
                
                wpt = ET.SubElement(gpx, "wpt")
                wpt.set("lat", str(location['latitude']))
                wpt.set("lon", str(location['longitude']))
                
                # Basic waypoint information
                name_elem = ET.SubElement(wpt, "name")
                name_elem.text = location.get('name', f'Fishing Point {i+1}')
                
                if location.get('description'):
                    desc_elem = ET.SubElement(wpt, "desc")
                    desc_elem.text = location['description']
                
                # Add category for fishing
                type_elem = ET.SubElement(wpt, "type")
                type_elem.text = "Fishing"
                
                # Add Garmin extensions if we have additional data
                if any(key in location for key in ['type', 'depth', 'temperature']):
                    extensions = ET.SubElement(wpt, "extensions")
                    wpt_ext = ET.SubElement(extensions, "gpxx:WaypointExtension")
                    
                    # Add categories
                    if location.get('type'):
                        categories = ET.SubElement(wpt_ext, "gpxx:Categories")
                        category = ET.SubElement(categories, "gpxx:Category")
                        category.text = location['type']
                    
                    # Add depth if available
                    if location.get('depth'):
                        depth = ET.SubElement(wpt_ext, "gpxx:Depth")
                        depth.text = str(location['depth'])
                    
                    # Add temperature if available
                    if location.get('temperature'):
                        temp = ET.SubElement(wpt_ext, "gpxx:Temperature")
                        temp.text = str(location['temperature'])
            
            # Write to file with pretty formatting
            rough_string = ET.tostring(gpx, encoding='unicode')
            reparsed = parseString(rough_string)
            pretty_xml = reparsed.toprettyxml(indent="  ")
            
            # Remove empty lines
            pretty_lines = [line for line in pretty_xml.split('\n') if line.strip()]
            pretty_xml = '\n'.join(pretty_lines)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(pretty_xml)
            
            print(f"✓ GPX file created: {output_path}")
            print(f"✓ Added {len([l for l in locations if 'latitude' in l])} waypoints")
            return True
            
        except Exception as e:
            print(f"✗ Error creating GPX file: {e}")
            return False