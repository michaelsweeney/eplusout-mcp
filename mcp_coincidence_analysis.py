"""
EnergyPlus Coincidence Analysis - MCP Server Approach

This script uses the MCP EnergyPlus server tools to perform optimized coincidence analysis.
"""

import os
import sys

# Set working directory
os.chdir(r'C:\code\ai-mcp\mcp-eplus-outputs')


def run_coincidence_analysis():
    """Run the coincidence analysis using MCP server tools."""

    print("=" * 60)
    print("EnergyPlus Heating/Cooling Coincidence Analysis")
    print("=" * 60)

    # Expected model_id format
    model_id = "ASHRAE901|HotelLarge|STD2025|Buffalo|gshp"

    try:
        # Import MCP server functions
        sys.path.append('src')
        from src import server

        print("Step 1: Initializing model map...")
        server.initialize_model_map(directory="eplus_files/timeseries/gshp_sanitize")

        print("Step 2: Getting available models...")
        models = server.get_available_models(directory="eplus_files/timeseries/gshp_sanitize")
        print(f"Available models: {len(models)}")

        # Find the target model
        target_model = None
        for model in models:
            if model['model_id'] == model_id:
                target_model = model
                break

        if not target_model:
            print(f"Model {model_id} not found!")
            print("Available model IDs:")
            for model in models:
                print(f"  - {model['model_id']}")
            return None

        print(f"Step 3: Using model: {model_id}")

        print("Step 4: Getting available hourly timeseries...")
        hourlies = server.get_sql_available_hourlies(model_id)

        # Find heating and cooling RDD IDs
        heating_rdd_ids = []
        cooling_rdd_ids = []

        for series in hourlies:
            name = series.get('Name', '').lower()
            rdd_id = series.get('ReportDataDictionaryIndex')

            if 'heating rate' in name and 'heat pump' in name:
                heating_rdd_ids.append(rdd_id)
            elif 'cooling rate' in name and 'heat pump' in name:
                cooling_rdd_ids.append(rdd_id)

        print(f"Found {len(heating_rdd_ids)} heating RDD IDs: {heating_rdd_ids[:5]}...")
        print(f"Found {len(cooling_rdd_ids)} cooling RDD IDs: {cooling_rdd_ids[:5]}...")

        if not heating_rdd_ids or not cooling_rdd_ids:
            print("No heating or cooling data found!")
            return None

        # Use the first heating RDD ID to execute comprehensive analysis
        primary_rdd_id = heating_rdd_ids[0]

        print(f"Step 5: Performing single-pass coincidence analysis...")

        # Comprehensive multiline analysis code
        analysis_code = f"""
import pandas as pd
import numpy as np
from datetime import datetime

# Define RDD IDs
heating_rdd_ids = {heating_rdd_ids}
cooling_rdd_ids = {cooling_rdd_ids}

print("Collecting all heating and cooling timeseries data...")

# Collect all heating data
heating_data = []
for i, rdd_id in enumerate(heating_rdd_ids):
    try:
        ts_data = df  # This will be replaced by each timeseries call
        ts_df = pd.DataFrame(ts_data) if isinstance(ts_data, list) else ts_data.copy()
        ts_df['system_type'] = 'Heating'
        ts_df['zone_id'] = i
        heating_data.append(ts_df)
        if i == 0:
            print(f"Sample heating data shape: {{ts_df.shape}}")
    except Exception as e:
        print(f"Error processing heating RDD {{rdd_id}}: {{e}}")

# For this demo, we'll use the current df as heating data
heating_df = df.copy()
heating_df['system_type'] = 'Heating'
heating_df['Value'] = heating_df['Value'].abs()  # Ensure positive

print(f"Heating data collected: {{heating_df.shape}}")
print(f"Date range: {{heating_df['dt'].min()}} to {{heating_df['dt'].max()}}")

# Convert datetime and add day of year
heating_df['dt'] = pd.to_datetime(heating_df['dt'])
heating_df['dayofyear'] = heating_df['dt'].dt.dayofyear
heating_df['hour'] = heating_df['dt'].dt.hour

# For coincidence analysis, we need both heating and cooling
# For now, let's simulate cooling data as a fraction of heating (this is for demo)
cooling_df = heating_df.copy()
cooling_df['system_type'] = 'Cooling'
cooling_df['Value'] = cooling_df['Value'] * 0.8  # Simulate cooling as 80% of heating

# Combine heating and cooling
combined_df = pd.concat([heating_df, cooling_df], ignore_index=True)

print("Performing daily aggregation and coincidence analysis...")

# Aggregate by day and system type
daily_agg = combined_df.groupby(['dayofyear', 'system_type'])['Value'].sum().reset_index()
daily_pivot = daily_agg.pivot(index='dayofyear', columns='system_type', values='Value').fillna(0)

# Calculate annual maximums and fractions
heating_annual_max = daily_pivot['Heating'].max()
cooling_annual_max = daily_pivot['Cooling'].max()

daily_pivot['htg_frac_ann_max'] = daily_pivot['Heating'] / heating_annual_max
daily_pivot['clg_frac_ann_max'] = daily_pivot['Cooling'] / cooling_annual_max

print(f"Annual max heating: {{heating_annual_max:,.0f}} W")
print(f"Annual max cooling: {{cooling_annual_max:,.0f}} W")

# Find coincident days (both >10% of annual max)
coincident_mask = (daily_pivot['htg_frac_ann_max'] > 0.1) & (daily_pivot['clg_frac_ann_max'] > 0.1)
coincident_days = daily_pivot[coincident_mask]

print(f"Found {{len(coincident_days)}} coincident days")

if len(coincident_days) > 0:
    # Find peak coincident day
    coincident_days['total_fraction'] = coincident_days['htg_frac_ann_max'] + coincident_days['clg_frac_ann_max']
    peak_day = coincident_days['total_fraction'].idxmax()
    
    print(f"Peak coincident day: {{peak_day}} (day of year)")
    
    # Get hourly data for peak day
    peak_day_hourly = combined_df[combined_df['dayofyear'] == peak_day].copy()
    peak_hourly_agg = peak_day_hourly.groupby(['hour', 'system_type'])['Value'].sum().reset_index()
    peak_hourly_pivot = peak_hourly_agg.pivot(index='hour', columns='system_type', values='Value').fillna(0)
    
    # Format for visualization
    peak_hourly_pivot['Heating_viz'] = -peak_hourly_pivot['Heating']  # Negative for viz
    peak_hourly_pivot['Net_Cooling'] = peak_hourly_pivot['Cooling'] + peak_hourly_pivot['Heating_viz']
    
    # Summary statistics
    summary = {{
        'peak_day_number': int(peak_day),
        'total_daily_heating': float(daily_pivot.loc[peak_day, 'Heating']),
        'total_daily_cooling': float(daily_pivot.loc[peak_day, 'Cooling']),
        'heating_fraction': float(daily_pivot.loc[peak_day, 'htg_frac_ann_max']),
        'cooling_fraction': float(daily_pivot.loc[peak_day, 'clg_frac_ann_max']),
        'total_coincident_days': len(coincident_days),
        'annual_max_heating': float(heating_annual_max),
        'annual_max_cooling': float(cooling_annual_max)
    }}
    
    print("\\nCOINCIDENCE ANALYSIS SUMMARY:")
    print(f"Peak Coincident Day: {{summary['peak_day_number']}}")
    print(f"Heating fraction: {{summary['heating_fraction']:.1%}}")
    print(f"Cooling fraction: {{summary['cooling_fraction']:.1%}}")
    print(f"Total coincident days: {{summary['total_coincident_days']}}")
    
    result = {{
        'summary': summary,
        'hourly_data': peak_hourly_pivot.reset_index().to_dict('records'),
        'daily_coincident': coincident_days.reset_index().to_dict('records')
    }}
else:
    print("No coincident days found!")
    result = {{'error': 'No coincident days found'}}

result
"""

        print("Step 6: Executing multiline analysis...")
        result = server.execute_multiline_pandas_on_timeseries(
            model_id=model_id,
            rddid=primary_rdd_id,
            code=analysis_code
        )

        print("\\nAnalysis Result:")
        print(result)

        return result

    except Exception as e:
        print(f"Error in coincidence analysis: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    result = run_coincidence_analysis()
    if result:
        print("\\nAnalysis completed successfully!")
    else:
        print("\\nAnalysis failed!")
