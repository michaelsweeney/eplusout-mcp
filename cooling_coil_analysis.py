import pandas as pd

# Coil data from epJSON
coils = {
    "Room_1_Flr_3 Cooling Coil": {"zone": "Room_1_Flr_3", "air_inlet": "Room_1_Flr_3 Return", "air_outlet": "Room_1_Flr_3 Cooling Coil Outlet"},
    "Room_1_Flr_6 Cooling Coil": {"zone": "Room_1_Flr_6", "air_inlet": "Room_1_Flr_6 Return", "air_outlet": "Room_1_Flr_6 Cooling Coil Outlet"},
    "Room_2_Flr_3 Cooling Coil": {"zone": "Room_2_Flr_3", "air_inlet": "Room_2_Flr_3 Return", "air_outlet": "Room_2_Flr_3 Cooling Coil Outlet"},
    "Room_2_Flr_6 Cooling Coil": {"zone": "Room_2_Flr_6", "air_inlet": "Room_2_Flr_6 Return", "air_outlet": "Room_2_Flr_6 Cooling Coil Outlet"},
    "Room_3_Mult9_Flr_6 Cooling Coil": {"zone": "Room_3_Mult9_Flr_6", "air_inlet": "Room_3_Mult9_Flr_6 Return", "air_outlet": "Room_3_Mult9_Flr_6 Cooling Coil Outlet"},
    "Room_3_Mult19_Flr_3 Cooling Coil": {"zone": "Room_3_Mult19_Flr_3", "air_inlet": "Room_3_Mult19_Flr_3 Return", "air_outlet": "Room_3_Mult19_Flr_3 Cooling Coil Outlet"},
    "Room_4_Mult19_Flr_3 Cooling Coil": {"zone": "Room_4_Mult19_Flr_3", "air_inlet": "Room_4_Mult19_Flr_3 Return", "air_outlet": "Room_4_Mult19_Flr_3 Cooling Coil Outlet"},
    "Room_5_Flr_3 Cooling Coil": {"zone": "Room_5_Flr_3", "air_inlet": "Room_5_Flr_3 Return", "air_outlet": "Room_5_Flr_3 Cooling Coil Outlet"},
    "Room_6_Flr_3 Cooling Coil": {"zone": "Room_6_Flr_3", "air_inlet": "Room_6_Flr_3 Return", "air_outlet": "Room_6_Flr_3 Cooling Coil Outlet"},
}

# Zone data from epJSON (volume in m3)
zones = {
    "Room_1_Flr_3": {"volume": 118.9391, "multiplier": 4},
    "Room_1_Flr_6": {"volume": 118.9391, "multiplier": 1},
    "Room_2_Flr_3": {"volume": 118.9252, "multiplier": 4},
    "Room_2_Flr_6": {"volume": 118.9252, "multiplier": 1},
    "Room_3_Mult9_Flr_6": {"volume": 74.7691, "multiplier": 9},
    "Room_3_Mult19_Flr_3": {"volume": 74.7487, "multiplier": 76},
    "Room_4_Mult19_Flr_3": {"volume": 74.7691, "multiplier": 76},
    "Room_5_Flr_3": {"volume": 118.9391, "multiplier": 4},
    "Room_6_Flr_3": {"volume": 118.9252, "multiplier": 4},
}

# Capacity data from HTML "Cooling Coils" report (Nominal Total Capacity in W)
cooling_coils_capacity = {
    "Room_1_Flr_3 Cooling Coil": {"nominal_total_capacity_w": 15319.85, "nominal_sensible_capacity_w": 13620.12, "shr": 0.89, "cop": 4.69},
    "Room_2_Flr_3 Cooling Coil": {"nominal_total_capacity_w": 14874.61, "nominal_sensible_capacity_w": 13215.38, "shr": 0.89, "cop": 4.69},
    "Room_3_Mult19_Flr_3 Cooling Coil": {"nominal_total_capacity_w": 77127.42, "nominal_sensible_capacity_w": 69447.11, "shr": 0.90, "cop": 4.69},
    "Room_4_Mult19_Flr_3 Cooling Coil": {"nominal_total_capacity_w": 91921.16, "nominal_sensible_capacity_w": 79894.49, "shr": 0.87, "cop": 4.69},
    "Room_5_Flr_3 Cooling Coil": {"nominal_total_capacity_w": 13604.54, "nominal_sensible_capacity_w": 12057.81, "shr": 0.89, "cop": 4.69},
    "Room_6_Flr_3 Cooling Coil": {"nominal_total_capacity_w": 13067.31, "nominal_sensible_capacity_w": 11567.31, "shr": 0.89, "cop": 4.69},
    "Room_1_Flr_6 Cooling Coil": {"nominal_total_capacity_w": 4158.46, "nominal_sensible_capacity_w": 3704.05, "shr": 0.89, "cop": 4.69},
    "Room_2_Flr_6 Cooling Coil": {"nominal_total_capacity_w": 4033.45, "nominal_sensible_capacity_w": 3590.41, "shr": 0.89, "cop": 4.69},
    "Room_3_Mult9_Flr_6 Cooling Coil": {"nominal_total_capacity_w": 16171.65, "nominal_sensible_capacity_w": 14181.58, "shr": 0.88, "cop": 4.69},
}

# Coil Sizing Summary data from HTML
coil_sizing_summary = {
    "Room_1_Flr_3 Cooling Coil": {"final_sensible_capacity_w": 13620.12, "air_flow_m3s": 1.291884},
    "Room_2_Flr_3 Cooling Coil": {"final_sensible_capacity_w": 13215.378, "air_flow_m3s": 1.253060},
    "Room_3_Mult19_Flr_3 Cooling Coil": {"final_sensible_capacity_w": 69447.113, "air_flow_m3s": 6.649862},
    "Room_4_Mult19_Flr_3 Cooling Coil": {"final_sensible_capacity_w": 79894.493, "air_flow_m3s": 7.485767},
    "Room_5_Flr_3 Cooling Coil": {"final_sensible_capacity_w": 12057.808, "air_flow_m3s": 1.141862},
    "Room_6_Flr_3 Cooling Coil": {"final_sensible_capacity_w": 11567.315, "air_flow_m3s": 1.094695},
    "Room_1_Flr_6 Cooling Coil": {"final_sensible_capacity_w": 3704.051, "air_flow_m3s": 0.351674},
    "Room_2_Flr_6 Cooling Coil": {"final_sensible_capacity_w": 3590.407, "air_flow_m3s": 0.340774},
    "Room_3_Mult9_Flr_6 Cooling Coil": {"final_sensible_capacity_w": 14181.581, "air_flow_m3s": 1.335318},
}

# Zone sensible cooling data (User Design Load in W and Load per Area in W/m2)
zone_sizing = {
    "Room_1_Flr_3": {"user_design_load_w": 13895.27, "load_per_area_wm2": 356.09},
    "Room_2_Flr_3": {"user_design_load_w": 13479.09, "load_per_area_wm2": 345.46},
    "Room_3_Mult19_Flr_3": {"user_design_load_w": 70642.86, "load_per_area_wm2": 2880.58},
    "Room_4_Mult19_Flr_3": {"user_design_load_w": 80953.57, "load_per_area_wm2": 3300.11},
    "Room_5_Flr_3": {"user_design_load_w": 12288.77, "load_per_area_wm2": 314.92},
    "Room_6_Flr_3": {"user_design_load_w": 11785.33, "load_per_area_wm2": 302.05},
    "Room_1_Flr_6": {"user_design_load_w": 3781.00, "load_per_area_wm2": 96.89},
    "Room_2_Flr_6": {"user_design_load_w": 3664.14, "load_per_area_wm2": 93.91},
    "Room_3_Mult9_Flr_6": {"user_design_load_w": 14391.74, "load_per_area_wm2": 586.69},
}

# Calculate SF per Ton for each coil
results = []
for coil_name, coil_data in coils.items():
    zone_name = coil_data["zone"]
    
    # Get capacity in tons (1 ton = 3516.85 W)
    capacity_data = cooling_coils_capacity.get(coil_name, {})
    capacity_w = capacity_data.get("nominal_total_capacity_w", 0)
    sensible_capacity_w = capacity_data.get("nominal_sensible_capacity_w", 0)
    shr = capacity_data.get("shr", 0)
    cop = capacity_data.get("cop", 0)
    
    capacity_tons = capacity_w / 3516.85
    
    # Get zone area in SF (calculate from load and load per area)
    zone_data = zone_sizing.get(zone_name, {})
    load_w = zone_data.get("user_design_load_w", 0)
    load_per_area_wm2 = zone_data.get("load_per_area_wm2", 0)
    
    # Area in m²
    area_m2 = load_w / load_per_area_wm2 if load_per_area_wm2 > 0 else 0
    # Area in SF (1 m² = 10.7639 SF)
    area_sf = area_m2 * 10.7639
    
    # Calculate SF per Ton
    sf_per_ton = area_sf / capacity_tons if capacity_tons > 0 else 0
    
    # Get coil sizing data
    sizing_data = coil_sizing_summary.get(coil_name, {})
    final_sensible_w = sizing_data.get("final_sensible_capacity_w", 0)
    air_flow_m3s = sizing_data.get("air_flow_m3s", 0)
    air_flow_cfm = air_flow_m3s * 2118.88  # 1 m³/s = 2118.88 CFM
    
    # CFM per Ton
    cfm_per_ton = air_flow_cfm / capacity_tons if capacity_tons > 0 else 0
    
    results.append({
        "Coil Name": coil_name,
        "Zone": zone_name,
        "Air Inlet Node": coil_data["air_inlet"],
        "Air Outlet Node": coil_data["air_outlet"],
        "Zone Area (m²)": round(area_m2, 2),
        "Zone Area (SF)": round(area_sf, 2),
        "Nominal Total Capacity (W)": capacity_w,
        "Nominal Sensible Capacity (W)": sensible_capacity_w,
        "Nominal Total Capacity (Tons)": round(capacity_tons, 2),
        "Sensible Heat Ratio": shr,
        "COP": cop,
        "Final Sensible Capacity (W)": final_sensible_w,
        "Air Flow (m³/s)": air_flow_m3s,
        "Air Flow (CFM)": round(air_flow_cfm, 2),
        "SF per Ton": round(sf_per_ton, 2),
        "CFM per Ton": round(cfm_per_ton, 2),
    })

df = pd.DataFrame(results)

# Display summary
print("=" * 120)
print("COOLING LOAD SIZING ANALYSIS")
print("=" * 120)
print("\nCOIL SUMMARY TABLE:")
print(df[["Coil Name", "Zone Area (SF)", "Nominal Total Capacity (Tons)", "SF per Ton", "CFM per Ton", "Sensible Heat Ratio"]].to_string(index=False))

print("\n\nDETAILED COIL DATA:")
print(df.to_string(index=False))

# Export to CSV
output_file = "cooling_coil_analysis_results.csv"
df.to_csv(output_file, index=False)
print(f"\n\nData exported to: {output_file}")
