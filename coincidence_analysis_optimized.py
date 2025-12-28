"""
EnergyPlus Heating/Cooling Coincidence Analysis - Optimized Single-Pass Approach

This script performs a comprehensive coincidence analysis to identify the peak day 
when both heating and cooling loads are significant (>10% of annual maximum).

Data Context:
- Location: C:\code\ai-mcp\mcp-eplus-outputs\eplus_files\timeseries\gshp_sanitize
- Expected: ~60 zones, heating RDD IDs (34,37,40...), cooling RDD IDs (35,38,41...)
- Values: Negative EnergyPlus rates need conversion to positive
"""

from src import server
from src.model_data import initialize_model_map_from_directory
import os
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import sys

# Set working directory
os.chdir(r'C:\code\ai-mcp\mcp-eplus-outputs')

# Import local modules


class CoincidenceAnalyzer:
    """Optimized single-pass coincidence analysis for EnergyPlus data."""

    def __init__(self, timeseries_dir):
        """Initialize the analyzer with model data."""
        self.timeseries_dir = timeseries_dir
        self.model_map = None
        self.model = None
        self.model_id = None
        self.results = {}

    def initialize_model_map(self):
        """Initialize model map with error handling."""
        print("Initializing model map...")
        try:
            self.model_map = initialize_model_map_from_directory(self.timeseries_dir)
            self.model = self.model_map.models[0]
            self.model_id = self.model.model_id
            print(f"✓ Model ID: {self.model_id}")
            print(f"✓ Total models found: {len(self.model_map.models)}")
            return True
        except Exception as e:
            print(f"✗ Error initializing model map: {e}")
            # Attempt reinitialize
            try:
                print("Attempting to reinitialize...")
                self.model_map = initialize_model_map_from_directory(self.timeseries_dir)
                self.model = self.model_map.models[0]
                self.model_id = self.model.model_id
                print(f"✓ Reinitialized - Model ID: {self.model_id}")
                return True
            except Exception as e2:
                print(f"✗ Failed to reinitialize: {e2}")
                return False

    def get_heating_cooling_rdd_ids(self):
        """Identify heating and cooling RDD IDs from available timeseries."""
        print("\nIdentifying heating and cooling RDD IDs...")

        try:
            # Get available timeseries data
            availdf = pd.DataFrame(self.model.sql_data.get_timeseries().availseries())

            # Define heating and cooling column patterns
            heating_patterns = [
                "Zone Water to Air Heat Pump Total Heating Rate",
                "Heating Rate",
                "Heat Pump Heating Rate",
                "Boiler Heating Rate"
            ]

            cooling_patterns = [
                "Zone Water to Air Heat Pump Total Cooling Rate",
                "Cooling Rate",
                "Heat Pump Cooling Rate",
                "Chiller Cooling Rate"
            ]

            # Find matching RDD IDs
            heating_mask = availdf['Name'].str.contains('|'.join(heating_patterns), case=False, na=False)
            cooling_mask = availdf['Name'].str.contains('|'.join(cooling_patterns), case=False, na=False)

            heating_rdd_ids = availdf.loc[heating_mask, 'ReportDataDictionaryIndex'].unique()
            cooling_rdd_ids = availdf.loc[cooling_mask, 'ReportDataDictionaryIndex'].unique()

            print(f"✓ Found {len(heating_rdd_ids)} heating RDD IDs: {list(heating_rdd_ids)[:10]}...")
            print(f"✓ Found {len(cooling_rdd_ids)} cooling RDD IDs: {list(cooling_rdd_ids)[:10]}...")

            return heating_rdd_ids, cooling_rdd_ids, availdf

        except Exception as e:
            print(f"✗ Error getting RDD IDs: {e}")
            return None, None, None

    def perform_single_pass_analysis(self):
        """
        Comprehensive single-pass analysis using multiline pandas operations.
        This replaces multiple separate operations with one optimized query.
        """
        print("\n" + "=" * 60)
        print("PERFORMING SINGLE-PASS COINCIDENCE ANALYSIS")
        print("=" * 60)

        # Get RDD IDs
        heating_rdd_ids, cooling_rdd_ids, availdf = self.get_heating_cooling_rdd_ids()
        if heating_rdd_ids is None:
            return None

        all_rdd_ids = list(heating_rdd_ids) + list(cooling_rdd_ids)

        print(f"\nCollecting timeseries data for {len(all_rdd_ids)} RDD IDs...")

        # Use MCP server for single comprehensive query
        code_query = f"""
# Single-pass comprehensive coincidence analysis
import pandas as pd
import numpy as np

# Get all timeseries data in one operation
heating_rdd_ids = {list(heating_rdd_ids)}
cooling_rdd_ids = {list(cooling_rdd_ids)}
all_rdd_ids = heating_rdd_ids + cooling_rdd_ids

print(f"Processing {{len(all_rdd_ids)}} RDD IDs...")

# Collect all data
all_series_data = []
for rdd_id in all_rdd_ids:
    try:
        series_data = model.sql_data.sql_timeseries.getseries_by_record_id(rdd_id)
        series_df = pd.DataFrame(series_data)
        series_df['rdd_id'] = rdd_id
        series_df['system_type'] = 'Heating' if rdd_id in heating_rdd_ids else 'Cooling'
        all_series_data.append(series_df)
    except Exception as e:
        print(f"Warning: Error processing RDD ID {{rdd_id}}: {{e}}")
        continue

# Combine all data
print("Combining all timeseries data...")
df_combined = pd.concat(all_series_data, ignore_index=True)

# Convert datetime and ensure positive values
df_combined['dt'] = pd.to_datetime(df_combined['dt'])
df_combined['Value'] = df_combined['Value'].abs()  # Convert negative rates to positive

# Aggregate by datetime and system type
print("Aggregating by datetime and system type...")
df_aggregated = df_combined.groupby(['dt', 'system_type'])['Value'].sum().reset_index()
df_pivot = df_aggregated.pivot(index='dt', columns='system_type', values='Value').fillna(0)

# Ensure both columns exist
if 'Heating' not in df_pivot.columns:
    df_pivot['Heating'] = 0
if 'Cooling' not in df_pivot.columns:
    df_pivot['Cooling'] = 0

# Add day of year for daily aggregation
df_pivot['dayofyear'] = df_pivot.index.dayofyear

# Calculate daily sums and annual max fractions
print("Calculating daily aggregations and fractions...")
daily_sums = df_pivot.groupby('dayofyear')[['Heating', 'Cooling']].sum()

# Annual maximum values
heating_annual_max = daily_sums['Heating'].max()
cooling_annual_max = daily_sums['Cooling'].max()

print(f"Annual max heating: {{heating_annual_max:,.0f}} W")
print(f"Annual max cooling: {{cooling_annual_max:,.0f}} W")

# Calculate fractions of annual maximum
daily_sums['htg_frac_ann_max'] = daily_sums['Heating'] / heating_annual_max
daily_sums['clg_frac_ann_max'] = daily_sums['Cooling'] / cooling_annual_max

# Find coincident days (both >10% of annual max)
print("Identifying coincident days...")
coincident_mask = (daily_sums['htg_frac_ann_max'] > 0.1) & (daily_sums['clg_frac_ann_max'] > 0.1)
daily_sums_coincident = daily_sums[coincident_mask]

print(f"Found {{len(daily_sums_coincident)}} coincident days")

if len(daily_sums_coincident) == 0:
    print("No coincident days found with both systems >10% of annual max!")
    result = {{'error': 'No coincident days found'}}
else:
    # Find peak coincident day (highest sum of fractions)
    daily_sums_coincident['total_fraction'] = daily_sums_coincident['htg_frac_ann_max'] + daily_sums_coincident['clg_frac_ann_max']
    peak_coincident_day = daily_sums_coincident['total_fraction'].idxmax()
    
    print(f"Peak coincident day: {{peak_coincident_day}} (day of year)")
    
    # Extract hourly data for peak coincident day
    peak_day_hourly = df_pivot[df_pivot['dayofyear'] == peak_coincident_day].copy()
    
    # Format for visualization (heating negative, calculate net cooling)
    peak_day_hourly['Heating_viz'] = -peak_day_hourly['Heating']  # Negative for visualization
    peak_day_hourly['Net_Cooling'] = peak_day_hourly['Cooling'] + peak_day_hourly['Heating_viz']
    peak_day_hourly['Hour'] = range(len(peak_day_hourly))
    
    # Calculate summary statistics
    peak_day_stats = {{
        'peak_day_number': int(peak_coincident_day),
        'total_daily_heating': float(daily_sums.loc[peak_coincident_day, 'Heating']),
        'total_daily_cooling': float(daily_sums.loc[peak_coincident_day, 'Cooling']),
        'heating_fraction_annual': float(daily_sums.loc[peak_coincident_day, 'htg_frac_ann_max']),
        'cooling_fraction_annual': float(daily_sums.loc[peak_coincident_day, 'clg_frac_ann_max']),
        'total_coincident_days': int(len(daily_sums_coincident)),
        'annual_max_heating': float(heating_annual_max),
        'annual_max_cooling': float(cooling_annual_max)
    }}
    
    result = {{
        'peak_day_stats': peak_day_stats,
        'hourly_data': peak_day_hourly[['Hour', 'Heating', 'Cooling', 'Heating_viz', 'Net_Cooling']].to_dict('records'),
        'daily_coincident_summary': daily_sums_coincident.to_dict('records'),
        'success': True
    }}

print("Analysis complete!")
result
"""

        try:
            # Execute the comprehensive analysis using MCP server
            from src import server
            analysis_result = server.execute_multiline_pandas_on_timeseries(
                model_id=self.model_id,
                rddid=int(heating_rdd_ids[0]),  # Use first heating RDD ID as placeholder
                code=code_query
            )

            # Parse the result
            if 'error' in str(analysis_result):
                print(f"✗ Analysis error: {analysis_result}")
                return None

            # Store results
            self.results = eval(analysis_result) if isinstance(analysis_result, str) else analysis_result
            return self.results

        except Exception as e:
            print(f"✗ Error in single-pass analysis: {e}")
            return None

    def create_visualization(self):
        """Create visualization of the peak coincident day."""
        if not self.results or 'hourly_data' not in self.results:
            print("No data available for visualization")
            return None

        hourly_data = pd.DataFrame(self.results['hourly_data'])
        stats = self.results['peak_day_stats']

        # Create the plot
        fig = go.Figure()

        # Add traces
        fig.add_trace(go.Bar(
            x=hourly_data['Hour'],
            y=hourly_data['Cooling'],
            name='Cooling',
            marker_color='blue',
            opacity=0.8
        ))

        fig.add_trace(go.Bar(
            x=hourly_data['Hour'],
            y=hourly_data['Heating_viz'],  # Negative values for visualization
            name='Heating',
            marker_color='red',
            opacity=0.8
        ))

        fig.add_trace(go.Scatter(
            x=hourly_data['Hour'],
            y=hourly_data['Net_Cooling'],
            name='Net Cooling',
            line=dict(color='green', width=3),
            mode='lines+markers'
        ))

        # Update layout
        fig.update_layout(
            title=f"Peak Coincident Day Analysis - Day {stats['peak_day_number']}<br>"
            f"Heating: {stats['heating_fraction_annual']:.1%} of annual max | "
            f"Cooling: {stats['cooling_fraction_annual']:.1%} of annual max",
            xaxis_title="Hour of Day",
            yaxis_title="Rate (W)",
            barmode='group',
            template='plotly_white',
            width=1000,
            height=600,
            legend=dict(x=0.8, y=1)
        )

        return fig

    def print_summary(self):
        """Print comprehensive analysis summary."""
        if not self.results:
            print("No results available")
            return

        stats = self.results['peak_day_stats']

        print("\n" + "=" * 60)
        print("COINCIDENCE ANALYSIS SUMMARY")
        print("=" * 60)
        print(f"Model ID: {self.model_id}")
        print(f"Peak Coincident Day: {stats['peak_day_number']} (day of year)")
        print(f"Total Coincident Days Found: {stats['total_coincident_days']}")
        print("\nPeak Day Statistics:")
        print(f"  • Daily Heating Load: {stats['total_daily_heating']:,.0f} W")
        print(f"  • Daily Cooling Load: {stats['total_daily_cooling']:,.0f} W")
        print(f"  • Heating (% of annual max): {stats['heating_fraction_annual']:.1%}")
        print(f"  • Cooling (% of annual max): {stats['cooling_fraction_annual']:.1%}")
        print("\nAnnual Maximums:")
        print(f"  • Max Daily Heating: {stats['annual_max_heating']:,.0f} W")
        print(f"  • Max Daily Cooling: {stats['annual_max_cooling']:,.0f} W")

        # Show first few hourly data points
        hourly_data = pd.DataFrame(self.results['hourly_data'])
        print(f"\nHourly Data Preview (first 5 hours):")
        print(hourly_data[['Hour', 'Heating', 'Cooling', 'Net_Cooling']].head().to_string(index=False))
        print("=" * 60)


def main():
    """Main execution function."""
    # Configuration
    timeseries_dir = r'C:\code\ai-mcp\mcp-eplus-outputs\eplus_files\timeseries\gshp_sanitize'

    # Initialize analyzer
    analyzer = CoincidenceAnalyzer(timeseries_dir)

    # Step 1: Initialize model map
    if not analyzer.initialize_model_map():
        print("Failed to initialize model map. Exiting.")
        return None

    # Step 2: Perform single-pass analysis
    results = analyzer.perform_single_pass_analysis()
    if results is None:
        print("Analysis failed. Exiting.")
        return None

    # Step 3: Print summary
    analyzer.print_summary()

    # Step 4: Create visualization
    fig = analyzer.create_visualization()
    if fig:
        print(f"\nVisualization created successfully!")
        # Optionally save or show the plot
        # fig.show()
        # fig.write_html("peak_coincident_day_analysis.html")

    return analyzer


if __name__ == "__main__":
    analyzer = main()
