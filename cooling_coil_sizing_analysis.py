"""
Cooling Coil Sizing Analysis
Analyzes cooling load sizing data for Coil:Cooling:WaterToAirHeatPump:EquationFit objects
"""

import pandas as pd
import json

# Coil data from epJSON
coil_epjson = {
    "Room_1_Flr_3 Cooling Coil": {
        "air_inlet_node_name": "Room_1_Flr_3 Return",
        "air_outlet_node_name": "Room_1_Flr_3 Cooling Coil Outlet",
    },
    "Room_2_Flr_3 Cooling Coil": {
        "air_inlet_node_name": "Room_2_Flr_3 Return",
        "air_outlet_node_name": "Room_2_Flr_3 Cooling Coil Outlet",
    },
    "Room_3_Mult19_Flr_3 Cooling Coil": {
        "air_inlet_node_name": "Room_3_Mult19_Flr_3 Return",
        "air_outlet_node_name": "Room_3_Mult19_Flr_3 Cooling Coil Outlet",
    },
    "Room_4_Mult19_Flr_3 Cooling Coil": {
        "air_inlet_node_name": "Room_4_Mult19_Flr_3 Return",
        "air_outlet_node_name": "Room_4_Mult19_Flr_3 Cooling Coil Outlet",
    },
    "Room_5_Flr_3 Cooling Coil": {
        "air_inlet_node_name": "Room_5_Flr_3 Return",
        "air_outlet_node_name": "Room_5_Flr_3 Cooling Coil Outlet",
    },
    "Room_6_Flr_3 Cooling Coil": {
        "air_inlet_node_name": "Room_6_Flr_3 Return",
        "air_outlet_node_name": "Room_6_Flr_3 Cooling Coil Outlet",
    },
    "Room_1_Flr_6 Cooling Coil": {
        "air_inlet_node_name": "Room_1_Flr_6 Return",
        "air_outlet_node_name": "Room_1_Flr_6 Cooling Coil Outlet",
    },
    "Room_2_Flr_6 Cooling Coil": {
        "air_inlet_node_name": "Room_2_Flr_6 Return",
        "air_outlet_node_name": "Room_2_Flr_6 Cooling Coil Outlet",
    },
    "Room_3_Mult9_Flr_6 Cooling Coil": {
        "air_inlet_node_name": "Room_3_Mult9_Flr_6 Return",
        "air_outlet_node_name": "Room_3_Mult9_Flr_6 Cooling Coil Outlet",
    },
}

# Zone data (volume in m3, need to calculate floor area)
zones = {
    "Room_1_Flr_3": {"volume": 118.9391, "multiplier": 4},
    "Room_2_Flr_3": {"volume": 118.9252, "multiplier": 4},
    "Room_3_Mult19_Flr_3": {"volume": 74.7487, "multiplier": 76},
    "Room_4_Mult19_Flr_3": {"volume": 74.7691, "multiplier": 76},
    "Room_5_Flr_3": {"volume": 118.9391, "multiplier": 4},
    "Room_6_Flr_3": {"volume": 118.9252, "multiplier": 4},
    "Room_1_Flr_6": {"volume": 118.9391, "multiplier": 1},
    "Room_2_Flr_6": {"volume": 118.9252, "multiplier": 1},
    "Room_3_Mult9_Flr_6": {"volume": 74.7691, "multiplier": 9},
}

# Cooling Coils table data from HTML
cooling_coils_html = [
    {"Coil Name": "ROOM_1_FLR_3 COOLING COIL", "Type": "Coil:Cooling:WaterToAirHeatPump:EquationFit", "Nominal Total Capacity [W]": 15319.85, "Nominal Sensible Capacity [W]": 13620.12, "Nominal Latent Capacity [W]": 1699.73, "Nominal Sensible Heat Ratio": 0.89, "Nominal Efficiency [W/W]": 4.69},
    {"Coil Name": "ROOM_2_FLR_3 COOLING COIL", "Type": "Coil:Cooling:WaterToAirHeatPump:EquationFit", "Nominal Total Capacity [W]": 14874.61, "Nominal Sensible Capacity [W]": 13215.38, "Nominal Latent Capacity [W]": 1659.23, "Nominal Sensible Heat Ratio": 0.89, "Nominal Efficiency [W/W]": 4.69},
    {"Coil Name": "ROOM_3_MULT19_FLR_3 COOLING COIL", "Type": "Coil:Cooling:WaterToAirHeatPump:EquationFit", "Nominal Total Capacity [W]": 77127.42, "Nominal Sensible Capacity [W]": 69447.11, "Nominal Latent Capacity [W]": 7680.31, "Nominal Sensible Heat Ratio": 0.90, "Nominal Efficiency [W/W]": 4.69},
    {"Coil Name": "ROOM_4_MULT19_FLR_3 COOLING COIL", "Type": "Coil:Cooling:WaterToAirHeatPump:EquationFit", "Nominal Total Capacity [W]": 91921.16, "Nominal Sensible Capacity [W]": 79894.49, "Nominal Latent Capacity [W]": 12026.67, "Nominal Sensible Heat Ratio": 0.87, "Nominal Efficiency [W/W]": 4.69},
    {"Coil Name": "ROOM_5_FLR_3 COOLING COIL", "Type": "Coil:Cooling:WaterToAirHeatPump:EquationFit", "Nominal Total Capacity [W]": 13604.54, "Nominal Sensible Capacity [W]": 12057.81, "Nominal Latent Capacity [W]": 1546.73, "Nominal Sensible Heat Ratio": 0.89, "Nominal Efficiency [W/W]": 4.69},
    {"Coil Name": "ROOM_6_FLR_3 COOLING COIL", "Type": "Coil:Cooling:WaterToAirHeatPump:EquationFit", "Nominal Total Capacity [W]": 13067.31, "Nominal Sensible Capacity [W]": 11567.31, "Nominal Latent Capacity [W]": 1500.00, "Nominal Sensible Heat Ratio": 0.89, "Nominal Efficiency [W/W]": 4.69},
    {"Coil Name": "ROOM_1_FLR_6 COOLING COIL", "Type": "Coil:Cooling:WaterToAirHeatPump:EquationFit", "Nominal Total Capacity [W]": 4158.46, "Nominal Sensible Capacity [W]": 3704.05, "Nominal Latent Capacity [W]": 454.41, "Nominal Sensible Heat Ratio": 0.89, "Nominal Efficiency [W/W]": 4.69},
    {"Coil Name": "ROOM_2_FLR_6 COOLING COIL", "Type": "Coil:Cooling:WaterToAirHeatPump:EquationFit", "Nominal Total Capacity [W]": 4033.45, "Nominal Sensible Capacity [W]": 3590.41, "Nominal Latent Capacity [W]": 443.04, "Nominal Sensible Heat Ratio": 0.89, "Nominal Efficiency [W/W]": 4.69},
    {"Coil Name": "ROOM_3_MULT9_FLR_6 COOLING COIL", "Type": "Coil:Cooling:WaterToAirHeatPump:EquationFit", "Nominal Total Capacity [W]": 16171.65, "Nominal Sensible Capacity [W]": 14181.58, "Nominal Latent Capacity [W]": 1990.07, "Nominal Sensible Heat Ratio": 0.88, "Nominal Efficiency [W/W]": 4.69},
]

# Coil Sizing Summary from HTML
coil_sizing_summary = [
    {"Coil Name": "ROOM_1_FLR_3 COOLING COIL", "Coil Final Gross Sensible Capacity [W]": 13620.120, "Coil Final Reference Air Volume Flow Rate [m3/s]": 1.291884, "HVAC Name": "ROOM_1_FLR_3"},
    {"Coil Name": "ROOM_2_FLR_3 COOLING COIL", "Coil Final Gross Sensible Capacity [W]": 13215.378, "Coil Final Reference Air Volume Flow Rate [m3/s]": 1.253060, "HVAC Name": "ROOM_2_FLR_3"},
    {"Coil Name": "ROOM_3_MULT19_FLR_3 COOLING COIL", "Coil Final Gross Sensible Capacity [W]": 69447.113, "Coil Final Reference Air Volume Flow Rate [m3/s]": 6.649862, "HVAC Name": "ROOM_3_MULT19_FLR_3"},
    {"Coil Name": "ROOM_4_MULT19_FLR_3 COOLING COIL", "Coil Final Gross Sensible Capacity [W]": 79894.493, "Coil Final Reference Air Volume Flow Rate [m3/s]": 7.485767, "HVAC Name": "ROOM_4_MULT19_FLR_3"},
    {"Coil Name": "ROOM_5_FLR_3 COOLING COIL", "Coil Final Gross Sensible Capacity [W]": 12057.808, "Coil Final Reference Air Volume Flow Rate [m3/s]": 1.141862, "HVAC Name": "ROOM_5_FLR_3"},
    {"Coil Name": "ROOM_6_FLR_3 COOLING COIL", "Coil Final Gross Sensible Capacity [W]": 11567.315, "Coil Final Reference Air Volume Flow Rate [m3/s]": 1.094695, "HVAC Name": "ROOM_6_FLR_3"},
    {"Coil Name": "ROOM_1_FLR_6 COOLING COIL", "Coil Final Gross Sensible Capacity [W]": 3704.051, "Coil Final Reference Air Volume Flow Rate [m3/s]": 0.351674, "HVAC Name": "ROOM_1_FLR_6"},
    {"Coil Name": "ROOM_2_FLR_6 COOLING COIL", "Coil Final Gross Sensible Capacity [W]": 3590.407, "Coil Final Reference Air Volume Flow Rate [m3/s]": 0.340774, "HVAC Name": "ROOM_2_FLR_6"},
    {"Coil Name": "ROOM_3_MULT9_FLR_6 COOLING COIL", "Coil Final Gross Sensible Capacity [W]": 14181.581, "Coil Final Reference Air Volume Flow Rate [m3/s]": 1.335318, "HVAC Name": "ROOM_3_MULT9_FLR_6"},
]

# Create the main dataframe
data = []

for coil_name, coil_info in coil_epjson.items():
    # Get zone name from coil name (remove " Cooling Coil")
    zone_name = coil_name.replace(" Cooling Coil", "")
    
    # Get zone data
    zone_data = zones.get(zone_name, {})
    volume = zone_data.get("volume", 0)
    multiplier = zone_data.get("multiplier", 1)
    
    # Estimate floor area from volume (assuming ~3m ceiling height typical for hotel)
    ceiling_height = 3.0
    floor_area = volume / ceiling_height if volume > 0 else 0
    total_floor_area = floor_area * multiplier
    
    # Find matching data from HTML tables
    # Convert coil name to match HTML format (e.g., "Room_1_Flr_3 Cooling Coil" -> "ROOM_1_FLR_3 COOLING COIL")
    html_coil_name = coil_name.upper().replace("_", "_")  # Keep underscores, just uppercase
    coil_html_data = next((c for c in cooling_coils_html if c["Coil Name"] == html_coil_name), {})
    sizing_data = next((s for s in coil_sizing_summary if s["Coil Name"] == html_coil_name), {})
    
    # Compile all data
    row = {
        "Coil Name": coil_name,
        "Zone Name": zone_name,
        "Air Inlet Node": coil_info.get("air_inlet_node_name", ""),
        "Air Outlet Node": coil_info.get("air_outlet_node_name", ""),
        "Zone Volume [m3]": volume,
        "Zone Multiplier": multiplier,
        "Zone Floor Area (Single) [m2]": round(floor_area, 2),
        "Total Zone Floor Area [m2]": round(total_floor_area, 2),
        "Nominal Total Capacity [W]": coil_html_data.get("Nominal Total Capacity [W]", ""),
        "Nominal Sensible Capacity [W]": coil_html_data.get("Nominal Sensible Capacity [W]", ""),
        "Nominal Latent Capacity [W]": coil_html_data.get("Nominal Latent Capacity [W]", ""),
        "Nominal Sensible Heat Ratio": coil_html_data.get("Nominal Sensible Heat Ratio", ""),
        "Nominal Efficiency [W/W]": coil_html_data.get("Nominal Efficiency [W/W]", ""),
        "Coil Final Gross Sensible Capacity [W]": sizing_data.get("Coil Final Gross Sensible Capacity [W]", ""),
        "Coil Final Air Volume Flow Rate [m3/s]": sizing_data.get("Coil Final Reference Air Volume Flow Rate [m3/s]", ""),
        "HVAC System Name": sizing_data.get("HVAC Name", ""),
    }
    
    # Calculate cooling load per area if we have the data
    if total_floor_area > 0 and coil_html_data.get("Nominal Total Capacity [W]"):
        row["Cooling Load per Area [W/m2]"] = round(coil_html_data["Nominal Total Capacity [W]"] / total_floor_area, 2)
    else:
        row["Cooling Load per Area [W/m2]"] = ""
    
    data.append(row)

# Create DataFrame and save to CSV
df = pd.DataFrame(data)

# Reorder columns for better readability
column_order = [
    "Coil Name",
    "Zone Name",
    "HVAC System Name",
    "Air Inlet Node",
    "Air Outlet Node",
    "Zone Volume [m3]",
    "Zone Multiplier",
    "Zone Floor Area (Single) [m2]",
    "Total Zone Floor Area [m2]",
    "Nominal Total Capacity [W]",
    "Nominal Sensible Capacity [W]",
    "Nominal Latent Capacity [W]",
    "Nominal Sensible Heat Ratio",
    "Nominal Efficiency [W/W]",
    "Coil Final Gross Sensible Capacity [W]",
    "Coil Final Air Volume Flow Rate [m3/s]",
    "Cooling Load per Area [W/m2]",
]

df = df[column_order]

# Save to CSV
output_file = "cooling_coil_sizing_analysis_output.csv"
df.to_csv(output_file, index=False)

print(f"Analysis complete! Results saved to: {output_file}")
print(f"\nSummary:")
print(f"  - Total coils analyzed: {len(df)}")
print(f"  - Total floor area served: {df['Total Zone Floor Area [m2]'].sum():.2f} m2")

# Calculate totals with proper handling of numeric values
total_capacity = pd.to_numeric(df['Nominal Total Capacity [W]'], errors='coerce').sum()
avg_cooling_load = pd.to_numeric(df['Cooling Load per Area [W/m2]'], errors='coerce').mean()

print(f"  - Total cooling capacity: {total_capacity:.2f} W")
print(f"  - Average cooling load per area: {avg_cooling_load:.2f} W/m2")
print(f"\nFirst few rows of the output:")
print(df.head())
