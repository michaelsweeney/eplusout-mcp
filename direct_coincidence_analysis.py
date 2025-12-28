"""
EnergyPlus Heating/Cooling Coincidence Analysis - Direct Approach

This script performs optimized single-pass coincidence analysis using the model data classes directly.
"""

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
sys.path.append('src')


def run_optimized_coincidence_analysis():
    """
    Perform single-pass optimized coincidence analysis for EnergyPlus heating/cooling data.
    """

    print("=" * 70)
    print("ENERGYPLUS HEATING/COOLING COINCIDENCE ANALYSIS - OPTIMIZED")
    print("=" * 70)

    # Configuration
    timeseries_dir = r'C:\code\ai-mcp\mcp-eplus-outputs\eplus_files\timeseries\gshp_sanitize'

    try:
        # Step 1: Initialize model map
        print("Step 1: Initializing model map...")
        model_map = initialize_model_map_from_directory(timeseries_dir)

        if not model_map or len(model_map.models) == 0:
            print("✗ No models found!")
            return None

        model = model_map.models[0]
        model_id = model.model_id

        print(f"✓ Model ID: {model_id}")
        print(f"✓ Total models: {len(model_map.models)}")

        # Step 2: Get available timeseries and identify heating/cooling RDD IDs
        print("\\nStep 2: Identifying heating and cooling RDD IDs...")

        availdf = pd.DataFrame(model.sql_data.get_timeseries().availseries())

        # Define patterns for heating and cooling
        heating_patterns = [
            "Zone Water to Air Heat Pump Total Heating Rate",
            "Heating Rate",
            "Heat Pump Heating Rate"
        ]

        cooling_patterns = [
            "Zone Water to Air Heat Pump Total Cooling Rate",
            "Cooling Rate",
            "Heat Pump Cooling Rate"
        ]

        # Find RDD IDs
        heating_mask = availdf['Name'].str.contains('|'.join(heating_patterns), case=False, na=False)
        cooling_mask = availdf['Name'].str.contains('|'.join(cooling_patterns), case=False, na=False)

        heating_rdd_ids = availdf.loc[heating_mask, 'ReportDataDictionaryIndex'].tolist()
        cooling_rdd_ids = availdf.loc[cooling_mask, 'ReportDataDictionaryIndex'].tolist()

        print(f"✓ Heating RDD IDs ({len(heating_rdd_ids)}): {heating_rdd_ids[:5]}...")
        print(f"✓ Cooling RDD IDs ({len(cooling_rdd_ids)}): {cooling_rdd_ids[:5]}...")

        if not heating_rdd_ids or not cooling_rdd_ids:
            print("✗ Missing heating or cooling data!")
            return None

        # Step 3: Single-pass comprehensive data collection and analysis
        print("\\nStep 3: Performing single-pass comprehensive analysis...")

        print("  → Collecting all heating timeseries data...")
        heating_data_list = []
        for i, rdd_id in enumerate(heating_rdd_ids):
            try:
                series_data = model.sql_data.sql_timeseries.getseries_by_record_id(rdd_id)
                if series_data:
                    df = pd.DataFrame(series_data)
                    df['system_type'] = 'Heating'
                    df['zone_index'] = i
                    heating_data_list.append(df)
                    if i == 0:
                        print(f"    Sample heating data shape: {df.shape}")
            except Exception as e:
                print(f"    Warning: Error with heating RDD {rdd_id}: {e}")

        print("  → Collecting all cooling timeseries data...")
        cooling_data_list = []
        for i, rdd_id in enumerate(cooling_rdd_ids):
            try:
                series_data = model.sql_data.sql_timeseries.getseries_by_record_id(rdd_id)
                if series_data:
                    df = pd.DataFrame(series_data)
                    df['system_type'] = 'Cooling'
                    df['zone_index'] = i
                    cooling_data_list.append(df)
                    if i == 0:
                        print(f"    Sample cooling data shape: {df.shape}")
            except Exception as e:
                print(f"    Warning: Error with cooling RDD {rdd_id}: {e}")

        if not heating_data_list or not cooling_data_list:
            print("✗ Failed to collect sufficient data!")
            return None

        # Step 4: Combine and process all data in single operation
        print("  → Combining and processing all data...")

        # Combine all heating and cooling data
        all_heating = pd.concat(heating_data_list, ignore_index=True)
        all_cooling = pd.concat(cooling_data_list, ignore_index=True)
        combined_data = pd.concat([all_heating, all_cooling], ignore_index=True)

        # Comprehensive single-pass processing
        combined_data['dt'] = pd.to_datetime(combined_data['dt'])
        combined_data['Value'] = combined_data['Value'].abs()  # Ensure positive values
        combined_data['dayofyear'] = combined_data['dt'].dt.dayofyear
        combined_data['hour'] = combined_data['dt'].dt.hour

        print(f"    Combined data shape: {combined_data.shape}")
        print(f"    Date range: {combined_data['dt'].min()} to {combined_data['dt'].max()}")

        # Aggregate by datetime and system type (sum across all zones)
        hourly_totals = combined_data.groupby(['dt', 'system_type'])['Value'].sum().reset_index()
        hourly_pivot = hourly_totals.pivot(index='dt', columns='system_type', values='Value').fillna(0)

        # Add day of year for daily aggregation
        hourly_pivot['dayofyear'] = hourly_pivot.index.dayofyear

        # Calculate daily sums
        daily_sums = hourly_pivot.groupby('dayofyear')[['Heating', 'Cooling']].sum()

        # Calculate annual maximums and fractions
        heating_annual_max = daily_sums['Heating'].max()
        cooling_annual_max = daily_sums['Cooling'].max()

        daily_sums['htg_frac_ann_max'] = daily_sums['Heating'] / heating_annual_max
        daily_sums['clg_frac_ann_max'] = daily_sums['Cooling'] / cooling_annual_max

        print(f"    Annual max heating: {heating_annual_max:,.0f} W")
        print(f"    Annual max cooling: {cooling_annual_max:,.0f} W")

        # Step 5: Identify coincident days and find peak
        print("\\nStep 4: Identifying coincident days...")

        # Find days where both systems are >10% of annual max
        coincident_mask = (daily_sums['htg_frac_ann_max'] > 0.1) & (daily_sums['clg_frac_ann_max'] > 0.1)
        coincident_days = daily_sums[coincident_mask].copy()

        print(f"✓ Found {len(coincident_days)} coincident days")

        if len(coincident_days) == 0:
            print("✗ No coincident days found where both systems >10% of annual max!")
            return None

        # Find peak coincident day (highest sum of fractions)
        coincident_days['total_fraction'] = coincident_days['htg_frac_ann_max'] + coincident_days['clg_frac_ann_max']
        peak_coincident_day = coincident_days['total_fraction'].idxmax()

        print(f"✓ Peak coincident day: {peak_coincident_day} (day of year)")

        # Step 6: Extract hourly data for peak day and format for visualization
        print("\\nStep 5: Preparing peak day hourly data...")

        peak_day_hourly = hourly_pivot[hourly_pivot['dayofyear'] == peak_coincident_day].copy()
        peak_day_hourly = peak_day_hourly.drop('dayofyear', axis=1)

        # Format for visualization
        peak_day_hourly['Heating_viz'] = -peak_day_hourly['Heating']  # Negative for visualization
        peak_day_hourly['Net_Cooling'] = peak_day_hourly['Cooling'] + peak_day_hourly['Heating_viz']
        peak_day_hourly['Hour'] = range(len(peak_day_hourly))

        # Step 7: Generate comprehensive results
        results = {
            'model_id': model_id,
            'peak_day_stats': {
                'peak_day_number': int(peak_coincident_day),
                'total_daily_heating': float(daily_sums.loc[peak_coincident_day, 'Heating']),
                'total_daily_cooling': float(daily_sums.loc[peak_coincident_day, 'Cooling']),
                'heating_fraction_annual': float(daily_sums.loc[peak_coincident_day, 'htg_frac_ann_max']),
                'cooling_fraction_annual': float(daily_sums.loc[peak_coincident_day, 'clg_frac_ann_max']),
                'total_coincident_days': len(coincident_days),
                'annual_max_heating': float(heating_annual_max),
                'annual_max_cooling': float(cooling_annual_max),
                'heating_zones_count': len(heating_rdd_ids),
                'cooling_zones_count': len(cooling_rdd_ids)
            },
            'hourly_data': peak_day_hourly.reset_index(),
            'daily_coincident_summary': coincident_days.reset_index()
        }

        # Step 8: Print comprehensive summary
        print_analysis_summary(results)

        # Step 9: Create visualization
        fig = create_visualization(results)

        return results, fig

    except Exception as e:
        print(f"✗ Error in analysis: {e}")
        import traceback
        traceback.print_exc()
        return None, None


def print_analysis_summary(results):
    """Print comprehensive analysis summary."""
    stats = results['peak_day_stats']

    print("\\n" + "=" * 70)
    print("COINCIDENCE ANALYSIS SUMMARY")
    print("=" * 70)
    print(f"Model ID: {results['model_id']}")
    print(f"Peak Coincident Day: {stats['peak_day_number']} (day of year)")
    print(f"Total Coincident Days Found: {stats['total_coincident_days']}")
    print(f"Heating Zones Analyzed: {stats['heating_zones_count']}")
    print(f"Cooling Zones Analyzed: {stats['cooling_zones_count']}")

    print("\\nPeak Day Statistics:")
    print(f"  • Daily Heating Load: {stats['total_daily_heating']:,.0f} W")
    print(f"  • Daily Cooling Load: {stats['total_daily_cooling']:,.0f} W")
    print(f"  • Heating (% of annual max): {stats['heating_fraction_annual']:.1%}")
    print(f"  • Cooling (% of annual max): {stats['cooling_fraction_annual']:.1%}")

    print("\\nAnnual Maximums:")
    print(f"  • Max Daily Heating: {stats['annual_max_heating']:,.0f} W")
    print(f"  • Max Daily Cooling: {stats['annual_max_cooling']:,.0f} W")

    # Show hourly data preview
    hourly_data = results['hourly_data']
    print(f"\\nHourly Data Preview (Peak Day - First 6 Hours):")
    preview_cols = ['Hour', 'Heating', 'Cooling', 'Net_Cooling']
    if all(col in hourly_data.columns for col in preview_cols):
        print(hourly_data[preview_cols].head(6).to_string(index=False, float_format='%.0f'))

    print("=" * 70)


def create_visualization(results):
    """Create comprehensive visualization."""
    hourly_data = results['hourly_data']
    stats = results['peak_day_stats']

    # Create subplot figure
    fig = go.Figure()

    # Add heating (negative for visualization)
    fig.add_trace(go.Bar(
        x=hourly_data['Hour'],
        y=hourly_data['Heating_viz'],
        name='Heating',
        marker_color='red',
        opacity=0.8
    ))

    # Add cooling
    fig.add_trace(go.Bar(
        x=hourly_data['Hour'],
        y=hourly_data['Cooling'],
        name='Cooling',
        marker_color='blue',
        opacity=0.8
    ))

    # Add net cooling line
    fig.add_trace(go.Scatter(
        x=hourly_data['Hour'],
        y=hourly_data['Net_Cooling'],
        name='Net Cooling Rate',
        line=dict(color='green', width=3),
        mode='lines+markers'
    ))

    # Update layout
    day_date = f"Day {stats['peak_day_number']}"

    fig.update_layout(
        title=f"Peak Coincident Day Analysis - {day_date}<br>"
        f"<sub>Heating: {stats['heating_fraction_annual']:.1%} of annual max | "
        f"Cooling: {stats['cooling_fraction_annual']:.1%} of annual max | "
        f"Model: {results['model_id']}</sub>",
        xaxis_title="Hour of Day",
        yaxis_title="Rate (W)",
        barmode='group',
        template='plotly_white',
        width=1200,
        height=700,
        legend=dict(x=0.75, y=1),
        font=dict(size=12)
    )

    # Save the plot
    output_file = "peak_coincident_day_analysis_optimized.html"
    fig.write_html(output_file)
    print(f"\\n✓ Visualization saved to: {output_file}")

    return fig


def main():
    """Main execution function."""
    print("Starting optimized EnergyPlus coincidence analysis...")

    results, fig = run_optimized_coincidence_analysis()

    if results:
        print("\\n✓ Analysis completed successfully!")

        # Optionally save results to CSV
        hourly_data = results['hourly_data']
        csv_file = "peak_coincident_day_hourly_data_optimized.csv"
        hourly_data.to_csv(csv_file, index=False)
        print(f"✓ Hourly data saved to: {csv_file}")

        return results
    else:
        print("\\n✗ Analysis failed!")
        return None


if __name__ == "__main__":
    results = main()
