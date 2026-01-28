"""
Analyze cooling load sizing for EnergyPlus model.
Extracts cooling coils, traces served zone areas, and compiles sizing data.
"""

import json
import pandas as pd
from pathlib import Path
from bs4 import BeautifulSoup
import re

# File paths
base_path = Path(r"C:\code\ai-mcp\mcp-eplus-outputs - filename-agnostic\eplus_files\diff_filenames")
model_name = "ASHRAE901_HotelLarge_STD2025_Buffalo_SkipEC_gshp.dd"
epjson_path = base_path / f"{model_name}.epJSON"
html_path = base_path / f"{model_name}.table.htm"

# Parse HTML report first to get zone areas and coil data
print("Parsing HTML report...")
with open(html_path, 'r', encoding='utf-8') as f:
    soup = BeautifulSoup(f.read(), 'html.parser')

# Extract zone areas from "Zone Summary" report
zone_areas = {}
for table in soup.find_all('table'):
    # Find the HTML comment before the table
    prev_sibs = []
    for prev_elem in table.previous_siblings:
        if hasattr(prev_elem, 'string'):
            prev_sibs.append(str(prev_elem))
        if len(prev_sibs) > 5:
            break
    
    # Check if any previous element contains "Zone Summary"
    is_zone_summary = any('Zone Summary' in str(s) for s in prev_sibs)
    
    if is_zone_summary:
        print("Found Zone Summary table")
        rows = table.find_all('tr')
        if len(rows) > 1:
            # Get headers
            headers = [th.get_text().strip() for th in rows[0].find_all(['th', 'td'])]
            
            # Get data rows
            for row in rows[1:]:
                cells = [td.get_text().strip() for td in row.find_all('td')]
                if len(cells) > 1 and cells[0]:
                    zone_name = cells[0]
                    area_m2 = cells[1].strip() if len(cells) > 1 else 'Unknown'
                    try:
                        zone_areas[zone_name] = float(area_m2)
                    except:
                        zone_areas[zone_name] = area_m2
        break  # Only process first Zone Summary table

print(f"Found {len(zone_areas)} zones with areas")

# Extract cooling coil data from HTML reports
cooling_coil_html = {}
coil_sizing_html = {}

for table in soup.find_all('table'):
    # Find the bold tag before the table
    bold_tag = table.find_previous('b')
    if bold_tag:
        report_name = bold_tag.get_text().strip()
        
        if 'Cooling Coils' == report_name:
            print(f"\nExtracting data from: {report_name}")
            rows = table.find_all('tr')
            if len(rows) > 1:
                headers = [th.get_text().strip() for th in rows[0].find_all(['th', 'td'])]
                
                for row in rows[1:]:
                    cells = [td.get_text().strip() for td in row.find_all('td')]
                    if len(cells) > 0 and cells[0]:
                        coil_name = cells[0]
                        row_data = dict(zip(headers, cells))
                        cooling_coil_html[coil_name] = row_data
        
        elif 'Coil Sizing Summary' == report_name:
            print(f"Extracting data from: {report_name}")
            rows = table.find_all('tr')
            if len(rows) > 1:
                headers = [th.get_text().strip() for th in rows[0].find_all(['th', 'td'])]
                
                for row in rows[1:]:
                    cells = [td.get_text().strip() for td in row.find_all('td')]
                    if len(cells) > 0 and cells[0]:
                        coil_name = cells[0]
                        row_data = dict(zip(headers, cells))
                        coil_sizing_html[coil_name] = row_data

# Load epJSON
print("\nLoading epJSON file...")
with open(epjson_path, 'r') as f:
    epjson = json.load(f)


# Find all cooling coils - both VariableSpeed and EquationFit types
coil_types = [
    "Coil:Cooling:WaterToAirHeatPump:VariableSpeedEquationFit",
    "Coil:Cooling:WaterToAirHeatPump:EquationFit"
]

all_cooling_coils = {}
for coil_type in coil_types:
    coils = epjson.get(coil_type, {})
    if coils:
        print(f"\nFound {len(coils)} cooling coils of type: {coil_type}")
        all_cooling_coils.update(coils)

print(f"\nTotal cooling coils: {len(all_cooling_coils)}")

# Get zones
zones = epjson.get('Zone', {})

# Get ZoneHVAC equipment to map coils to zones
zone_hvac_wshp = epjson.get('ZoneHVAC:WaterToAirHeatPump', {})

# Map coils to zones via equipment names
coil_to_zone = {}
for unit_name, unit_obj in zone_hvac_wshp.items():
    cooling_coil_name = unit_obj.get('cooling_coil_name', '')
    if cooling_coil_name:
        # Extract zone from unit name or search zones
        for zone_name in zones.keys():
            zone_clean = zone_name.upper().replace('_', '').replace(' ', '')
            unit_clean = unit_name.upper().replace('_', '').replace(' ', '')
            if zone_clean in unit_clean:
                coil_to_zone[cooling_coil_name] = zone_name
                break

# Check for PSZ (packaged single zone) systems
air_loop_unitary = epjson.get('AirLoopHVAC:UnitarySystem', {})
for system_name, system_obj in air_loop_unitary.items():
    cooling_coil_name = system_obj.get('cooling_coil_name', '')
    if cooling_coil_name:
        # For PSZ systems, match system name to zone
        for zone_name in zones.keys():
            zone_clean = zone_name.upper().replace('_', '').replace(' ', '')
            system_clean = system_name.upper().replace('_', '').replace(' ', '').replace('PSZ', '')
            if zone_clean in system_clean or system_clean in zone_clean:
                coil_to_zone[cooling_coil_name] = zone_name
                break

print(f"\nMapped {len(coil_to_zone)} coils to zones")

# Create zone name lookup dict for case-insensitive matching
zone_lookup = {}
for zone_name in zone_areas.keys():
    zone_lookup[zone_name.upper().replace('_', '').replace(' ', '')] = zone_name

print(f"Zone lookup has {len(zone_lookup)} entries")

# Build comprehensive coil data
coil_data = {}
for coil_name in all_cooling_coils.keys():
    # Match to HTML data (case-insensitive search)
    coil_upper = coil_name.upper()
    
    # Find in HTML data
    html_cooling_data = None
    html_sizing_data = None
    
    for html_name, data in cooling_coil_html.items():
        if html_name.upper() == coil_upper:
            html_cooling_data = data
            break
    
    for html_name, data in coil_sizing_html.items():
        if html_name.upper() == coil_upper:
            html_sizing_data = data
            break
    
    # Get zone
    zone_name = coil_to_zone.get(coil_name, 'Unknown')
    
    # Try case-insensitive zone lookup
    zone_area_m2 = 'Unknown'
    if zone_name != 'Unknown':
        zone_clean = zone_name.upper().replace('_', '').replace(' ', '')
        if zone_clean in zone_lookup:
            html_zone_name = zone_lookup[zone_clean]
            zone_area_m2 = zone_areas.get(html_zone_name, 'Unknown')

    
    # Extract cooling capacity from HTML data
    nominal_capacity_w = None
    if html_cooling_data and 'Nominal Total Capacity [W]' in html_cooling_data:
        try:
            cap_str = html_cooling_data['Nominal Total Capacity [W]'].strip()
            nominal_capacity_w = float(cap_str)
        except:
            pass
    
    # Convert to tons and calculate SF per ton
    cooling_cap_tons = None
    zone_area_sf = None
    sf_per_ton = None
    
    if nominal_capacity_w:
        cooling_cap_tons = nominal_capacity_w / 3516.85  # Convert W to tons
        
        if zone_area_m2 and zone_area_m2 != 'Unknown':
            zone_area_sf = zone_area_m2 * 10.764  # m2 to SF
            sf_per_ton = zone_area_sf / cooling_cap_tons if cooling_cap_tons > 0 else None
    
    coil_data[coil_name] = {
        'zone': zone_name,
        'zone_area_m2': zone_area_m2,
        'zone_area_sf': zone_area_sf if zone_area_sf else 'Unknown',
        'cooling_capacity_w': nominal_capacity_w if nominal_capacity_w else 'Unknown',
        'cooling_capacity_tons': round(cooling_cap_tons, 2) if cooling_cap_tons else 'Unknown',
        'sf_per_ton': round(sf_per_ton, 1) if sf_per_ton else 'Unknown',
        'html_cooling_coils': html_cooling_data,
        'html_coil_sizing': html_sizing_data
    }

# Create summary table
summary_rows = []
for coil_name, data in sorted(coil_data.items()):
    row = {
        'Coil Name': coil_name,
        'Zone': data['zone'],
        'Zone Area (m²)': data['zone_area_m2'],
        'Zone Area (SF)': data['zone_area_sf'],
        'Cooling Capacity (W)': data['cooling_capacity_w'],
        'Cooling Capacity (Tons)': data['cooling_capacity_tons'],
        'SF per Ton': data['sf_per_ton'],
    }
    
    # Add key columns from HTML reports
    if data['html_cooling_coils']:
        row['Type'] = data['html_cooling_coils'].get('Type', '')
        row['Nominal Sensible Capacity [W]'] = data['html_cooling_coils'].get('Nominal Sensible Capacity [W]', '')
        row['Nominal Latent Capacity [W]'] = data['html_cooling_coils'].get('Nominal Latent Capacity [W]', '')
        row['Nominal SHR'] = data['html_cooling_coils'].get('Nominal Sensible Heat Ratio', '')
        row['Nominal Efficiency [W/W]'] = data['html_cooling_coils'].get('Nominal Efficiency [W/W]', '')
    
    if data['html_coil_sizing']:
        row['HVAC Type'] = data['html_coil_sizing'].get('HVAC Type', '')
        row['Coil Final Gross Sensible Capacity [W]'] = data['html_coil_sizing'].get('Coil Final Gross Sensible Capacity [W]', '')
        row['Coil Final Reference Air Volume Flow Rate [m3/s]'] = data['html_coil_sizing'].get('Coil Final Reference Air Volume Flow Rate [m3/s]', '')
    
    summary_rows.append(row)

# Create DataFrame
df = pd.DataFrame(summary_rows)

# Display results
print("\n" + "="*120)
print("COOLING LOAD SIZING ANALYSIS")
print("="*120)
print(df.to_string(index=False))

# Calculate summary statistics
valid_sf_per_ton = [row['SF per Ton'] for row in summary_rows if isinstance(row['SF per Ton'], (int, float))]
if valid_sf_per_ton:
    print(f"\n\nSF per Ton Statistics:")
    print(f"  Average: {sum(valid_sf_per_ton)/len(valid_sf_per_ton):.1f} SF/Ton")
    print(f"  Min: {min(valid_sf_per_ton):.1f} SF/Ton")
    print(f"  Max: {max(valid_sf_per_ton):.1f} SF/Ton")

# Save to CSV
output_csv = base_path / f"{model_name}_cooling_analysis.csv"
df.to_csv(output_csv, index=False)
print(f"\n\nResults saved to: {output_csv}")
