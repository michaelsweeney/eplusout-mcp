"""
Analyze cooling coil sizing for Water-to-Air Heat Pump coils in EnergyPlus model.
Extracts coil data from epJSON, traces zones served, and compiles HTML report data.
"""

import json
import pandas as pd
from pathlib import Path
from bs4 import BeautifulSoup
import re

# File paths
base_path = Path(r"C:\code\ai-mcp\mcp-eplus-outputs - filename-agnostic\eplus_files\diff_filenames")
model_name = "ASHRAE901_HotelLarge_STD2025_Buffalo_SkipEC_gshp.dd"

epjson_file = base_path / f"{model_name}.epJSON"
html_file = base_path / f"{model_name}.table.htm"
output_file = Path(r"C:\code\ai-mcp\mcp-eplus-outputs - filename-agnostic") / "wshp_cooling_coil_analysis.csv"

print("Loading epJSON file...")
with open(epjson_file, 'r') as f:
    epjson_data = json.load(f)

# Extract all cooling coils
coil_data = {}

# Get Coil:Cooling:WaterToAirHeatPump:EquationFit objects
if "Coil:Cooling:WaterToAirHeatPump:EquationFit" in epjson_data:
    for coil_name, coil_props in epjson_data["Coil:Cooling:WaterToAirHeatPump:EquationFit"].items():
        coil_data[coil_name] = {
            "coil_type": "Coil:Cooling:WaterToAirHeatPump:EquationFit",
            "air_inlet_node": coil_props.get("air_inlet_node_name", ""),
            "air_outlet_node": coil_props.get("air_outlet_node_name", ""),
            "water_inlet_node": coil_props.get("water_inlet_node_name", ""),
            "water_outlet_node": coil_props.get("water_outlet_node_name", ""),
            "rated_total_capacity": coil_props.get("gross_rated_total_cooling_capacity", "Autosize"),
            "rated_sensible_capacity": coil_props.get("gross_rated_sensible_cooling_capacity", "Autosize"),
            "rated_cop": coil_props.get("gross_rated_cooling_cop", ""),
            "rated_air_flow": coil_props.get("rated_air_flow_rate", "Autosize"),
            "rated_water_flow": coil_props.get("rated_water_flow_rate", "Autosize"),
        }

print(f"Found {len(coil_data)} Coil:Cooling:WaterToAirHeatPump:EquationFit coils")

# Get zone information and calculate floor areas from volume
zones = {}
if "Zone" in epjson_data:
    for zone_name, zone_props in epjson_data["Zone"].items():
        volume = zone_props.get("volume", 0)
        multiplier = zone_props.get("multiplier", 1)
        # Assume standard ceiling height of 3.05m (10 ft) if not specified
        # EnergyPlus typically uses this when ceiling_height is -9999
        ceiling_height = 3.05
        floor_area = volume / ceiling_height if volume > 0 else 0
        
        zones[zone_name] = {
            "volume": volume,
            "multiplier": multiplier,
            "floor_area": floor_area,
            "floor_area_autocalc": zone_props.get("floor_area", "Autocalculate")
        }

print(f"Found {len(zones)} zones")

# Get ZoneHVAC:WaterToAirHeatPump to map coils to zones
zone_equipment_map = {}
if "ZoneHVAC:WaterToAirHeatPump" in epjson_data:
    for equip_name, equip_props in epjson_data["ZoneHVAC:WaterToAirHeatPump"].items():
        cooling_coil = equip_props.get("cooling_coil_name", "")
        zone_name_raw = equip_props.get("air_inlet_node_name", "")
        # Extract zone name from node name (e.g., "Room_1_Flr_3 Return" -> "Room_1_Flr_3")
        zone_match = re.match(r"(.+?)\s+(Return|Inlet)", zone_name_raw)
        if zone_match:
            zone_name_candidate = zone_match.group(1)
        else:
            zone_name_candidate = zone_name_raw.replace(" Return", "").replace(" Inlet", "").strip()
        
        if cooling_coil in coil_data:
            coil_data[cooling_coil]["zone_equipment"] = equip_name
            coil_data[cooling_coil]["zone_name_candidate"] = zone_name_candidate
            zone_equipment_map[cooling_coil] = zone_name_candidate

print(f"Mapped {len(zone_equipment_map)} coils to zones via ZoneHVAC:WaterToAirHeatPump")

# Try to find zone areas from ZoneList or direct zone mapping
# First, get BuildingSurface:Detailed to calculate floor area for each zone
zone_floor_areas = {}
if "BuildingSurface:Detailed" in epjson_data:
    for surf_name, surf_props in epjson_data["BuildingSurface:Detailed"].items():
        if surf_props.get("surface_type", "") == "Floor":
            zone_name = surf_props.get("zone_name", "")
            vertices = []
            i = 1
            while f"vertex_{i}_x_coordinate" in surf_props:
                x = surf_props[f"vertex_{i}_x_coordinate"]
                y = surf_props[f"vertex_{i}_y_coordinate"]
                vertices.append((x, y))
                i += 1
            
            # Calculate area using shoelace formula
            if len(vertices) >= 3:
                area = 0
                for j in range(len(vertices)):
                    x1, y1 = vertices[j]
                    x2, y2 = vertices[(j + 1) % len(vertices)]
                    area += x1 * y2 - x2 * y1
                area = abs(area) / 2
                
                if zone_name in zone_floor_areas:
                    zone_floor_areas[zone_name] += area
                else:
                    zone_floor_areas[zone_name] = area

print(f"Calculated floor areas from surfaces for {len(zone_floor_areas)} zones")

# Merge surface-calculated areas with volume-based estimates
for zone_name, zone_data in zones.items():
    if zone_name in zone_floor_areas:
        # Use the surface-calculated area (more accurate)
        zone_data["floor_area"] = zone_floor_areas[zone_name]
    # Otherwise, use the volume-based estimate already calculated

# Add zone area to coil data
for coil_name, data in coil_data.items():
    zone_candidate = data.get("zone_name_candidate", "")
    if zone_candidate in zones:
        zone_info = zones[zone_candidate]
        data["zone_floor_area_m2"] = zone_info["floor_area"]
        data["zone_multiplier"] = zone_info["multiplier"]
        data["total_floor_area_m2"] = zone_info["floor_area"] * zone_info["multiplier"]
    else:
        data["zone_floor_area_m2"] = None
        data["zone_multiplier"] = None
        data["total_floor_area_m2"] = None

# Parse HTML file for coil reports
print("\nParsing HTML file...")
with open(html_file, 'r', encoding='utf-8') as f:
    html_content = f.read()

soup = BeautifulSoup(html_content, 'html.parser')

# Find all tables
tables = soup.find_all('table')
print(f"Found {len(tables)} tables in HTML")

# Look for "Cooling Coils" report
cooling_coils_data = {}
for table in tables:
    # Check if this is the Cooling Coils table
    caption = table.find_previous(['b', 'p'])
    if caption and 'Cooling Coils' in caption.get_text():
        print(f"Found Cooling Coils table")
        # Parse the table
        rows = table.find_all('tr')
        headers = []
        for row in rows:
            cells = row.find_all(['th', 'td'])
            if not cells:
                continue
            
            cell_texts = [cell.get_text(strip=True) for cell in cells]
            
            if not headers and any('Type' in text for text in cell_texts):
                headers = cell_texts
                continue
            
            if headers and cell_texts and len(cell_texts) > 1:
                # First cell is usually the coil name
                coil_name = cell_texts[0]
                if coil_name and 'COOLING COIL' in coil_name.upper():
                    row_data = dict(zip(headers, cell_texts))
                    cooling_coils_data[coil_name] = row_data

print(f"Found data for {len(cooling_coils_data)} coils in Cooling Coils report")

# Look for "Coil Sizing Summary" report
coil_sizing_data = {}
for table in tables:
    caption = table.find_previous(['b', 'p'])
    if caption and 'Coil Sizing Summary' in caption.get_text():
        print(f"Found Coil Sizing Summary table")
        rows = table.find_all('tr')
        headers = []
        for row in rows:
            cells = row.find_all(['th', 'td'])
            if not cells:
                continue
            
            cell_texts = [cell.get_text(strip=True) for cell in cells]
            
            if not headers and any('Coil' in text for text in cell_texts):
                headers = cell_texts
                continue
            
            if headers and cell_texts and len(cell_texts) > 1:
                # First cell is usually the coil name
                coil_name = cell_texts[0]
                if coil_name and 'COOLING COIL' in coil_name.upper():
                    row_data = dict(zip(headers, cell_texts))
                    coil_sizing_data[coil_name] = row_data

print(f"Found data for {len(coil_sizing_data)} coils in Coil Sizing Summary report")

# Merge all data
final_data = []

# Create a mapping of uppercase coil names for matching HTML data
html_cooling_map = {k.upper(): v for k, v in cooling_coils_data.items()}
html_sizing_map = {k.upper(): v for k, v in coil_sizing_data.items()}

for coil_name, data in coil_data.items():
    row = {
        "Coil Name": coil_name,
        "Coil Type": data["coil_type"],
        "Air Inlet Node": data["air_inlet_node"],
        "Air Outlet Node": data["air_outlet_node"],
        "Water Inlet Node": data["water_inlet_node"],
        "Water Outlet Node": data["water_outlet_node"],
        "Zone Equipment": data.get("zone_equipment", ""),
        "Zone Name": data.get("zone_name_candidate", ""),
        "Zone Floor Area (m²)": data.get("zone_floor_area_m2", ""),
        "Zone Multiplier": data.get("zone_multiplier", ""),
        "Total Floor Area (m²)": data.get("total_floor_area_m2", ""),
        "Rated Total Capacity": data["rated_total_capacity"],
        "Rated Sensible Capacity": data["rated_sensible_capacity"],
        "Rated COP": data["rated_cop"],
        "Rated Air Flow": data["rated_air_flow"],
        "Rated Water Flow": data["rated_water_flow"],
    }
    
    # Add data from HTML Cooling Coils report (case-insensitive)
    coil_name_upper = coil_name.upper()
    if coil_name_upper in html_cooling_map:
        for key, value in html_cooling_map[coil_name_upper].items():
            if key not in row:
                row[f"HTML_CoolingCoils_{key}"] = value
    
    # Add data from HTML Coil Sizing Summary report (case-insensitive)
    if coil_name_upper in html_sizing_map:
        for key, value in html_sizing_map[coil_name_upper].items():
            if key not in row:
                row[f"HTML_SizingSummary_{key}"] = value
    
    final_data.append(row)

# Create DataFrame and export to CSV
df = pd.DataFrame(final_data)
df.to_csv(output_file, index=False)

print(f"\n✓ Analysis complete!")
print(f"✓ Output saved to: {output_file}")
print(f"✓ Total coils analyzed: {len(df)}")
print(f"\nSummary:")
print(f"  - Coils with zone data: {df['Zone Name'].notna().sum()}")
print(f"  - Coils with floor area: {df['Zone Floor Area (m²)'].notna().sum()}")
