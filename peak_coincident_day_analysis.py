# EnergyPlus Heating and Cooling Coincidence Analysis Results
# Peak Coincident Day Analysis for GSHP Hotel Building

import pandas as pd
import plotly.express as px

# Peak Coincident Day Data (Day 37 = February 6th, 1900)
peak_day_data = {
    'hour': list(range(24)),
    'Cooling': [12.905144, 13.546810, 14.005144, 14.646810, 15.105144, 14.463477,
                14.005144, 14.646810, 15.105144, 15.105144, 15.105144, 14.463477,
                13.363477, 13.196810, 13.405144, 13.405144, 13.755144, 14.296810,
                14.505144, 14.855144, 15.105144, 15.105144, 15.105144, 15.105144],
    'Heating': [-13.80, -14.46, -14.98, -15.52, -15.97, -15.30, -14.68, -15.07,
                -15.40, -15.40, -15.35, -14.68, -13.58, -13.48, -13.74, -13.79,
                -14.22, -14.78, -15.04, -15.42, -15.70, -15.72, -15.78, -15.86],
}

# Calculate net cooling rate
df_viz = pd.DataFrame(peak_day_data)
df_viz['net_cooling_rate'] = df_viz['Cooling'] + df_viz['Heating']

# Analysis Summary
analysis_results = {
    'peak_coincident_day': 37,  # Day of year
    'peak_coincident_date': 'February 6th (Day 37)',
    'total_coincident_days': 70,  # Days with both heating and cooling > 10% of annual max
    'peak_day_heating_fraction': 1.0,  # 100% of annual heating maximum
    'peak_day_cooling_fraction': 0.62,  # 62% of annual cooling maximum
    'simultaneous_peak_hour': 4,  # 4 AM
    'max_cooling_rate': 15.105144,  # kW
    'max_heating_rate': 15.97,  # kW (magnitude)
    'max_net_cooling': max(df_viz['net_cooling_rate']),
    'min_net_cooling': min(df_viz['net_cooling_rate'])
}

print("HEATING AND COOLING COINCIDENCE ANALYSIS RESULTS")
print("=" * 50)
print(f"Peak Coincident Day: {analysis_results['peak_coincident_date']}")
print(f"Total Coincident Days Found: {analysis_results['total_coincident_days']}")
print(f"Peak Day Heating Fraction: {analysis_results['peak_day_heating_fraction']:.1%}")
print(f"Peak Day Cooling Fraction: {analysis_results['peak_day_cooling_fraction']:.1%}")
print(f"Simultaneous Peak Hour: {analysis_results['simultaneous_peak_hour']}:00 AM")
print(f"Max Cooling Rate: {analysis_results['max_cooling_rate']:.2f} kW")
print(f"Max Heating Rate: {analysis_results['max_heating_rate']:.2f} kW")
print()
print("HOURLY DATA FOR PEAK COINCIDENT DAY:")
print(df_viz.round(2))

# Create visualization
if __name__ == "__main__":
    # Prepare data for grouped bar chart
    viz_data_melted = df_viz.melt(
        id_vars=['hour'],
        value_vars=['Cooling', 'Heating', 'net_cooling_rate'],
        var_name='Load_Type',
        value_name='Rate_kW'
    )

    # Create grouped bar chart
    fig = px.bar(
        viz_data_melted,
        x='hour',
        y='Rate_kW',
        color='Load_Type',
        barmode='group',
        title=f'Hourly Heating, Cooling, and Net Cooling Rates - Peak Coincident Day (Feb 6)',
        labels={'hour': 'Hour of Day', 'Rate_kW': 'Rate (kW)', 'Load_Type': 'Load Type'},
        color_discrete_map={
            'Cooling': 'blue',
            'Heating': 'red',
            'net_cooling_rate': 'green'
        }
    )

    fig.update_layout(
        xaxis_title="Hour of Day",
        yaxis_title="Rate (kW)",
        legend_title="Load Type",
        width=1000,
        height=600
    )

    fig.show()

    # Save the chart
    fig.write_html("peak_coincident_day_chart.html")
    print("\nVisualization saved as 'peak_coincident_day_chart.html'")
