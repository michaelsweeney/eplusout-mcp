# EnergyPlus Heating/Cooling Coincidence Analysis Results

## Analysis Summary

**Model:** ASHRAE901|HotelLarge|STD2025|Buffalo|gshp  
**Analysis Date:** October 2, 2025  
**Method:** Optimized Single-Pass Analysis

## Key Findings

### Peak Coincident Day: **Day 303** (October 30th)

This day represents the peak coincidence when both heating and cooling systems operate significantly (>10% of their respective annual maximums).

### System Performance Statistics

- **Total Coincident Days Found:** 3 days
- **Zones Analyzed:** 27 heating zones, 27 cooling zones
- **Peak Day Heating Load:** 272,110 W (10.7% of annual max)
- **Peak Day Cooling Load:** 609,430 W (14.7% of annual max)

### Annual System Maximums

- **Maximum Daily Heating:** 2,544,140 W
- **Maximum Daily Cooling:** 4,158,946 W

## Hourly Profile Analysis (Peak Day - October 30th)

The coincident day shows a clear transition pattern:

### Night/Early Morning (Hours 0-7)

- **Dominated by heating loads** (up to 38,384 W at 3 AM)
- **Minimal cooling** (near-zero values)
- **Peak heating occurs at 3-4 AM** during coldest outdoor conditions

### Transition Period (Hours 8-9)

- **Mixed heating and cooling loads**
- Hour 8: 904 W cooling, 17,071 W heating
- Hour 9: 11,207 W cooling, 16,279 W heating
- **Net heating still dominates**

### Daytime (Hours 10-17)

- **Cooling-dominated period** (peak 98,441 W at 3 PM)
- **Minimal heating loads** (essentially zero)
- **Peak cooling at 3 PM** during warmest conditions

### Evening Transition (Hours 18-23)

- **Gradual return to heating dominance**
- **Mixed loads during transition**
- **Net heating by end of day**

## Technical Insights

### Load Coincidence Characteristics

1. **Clear seasonal transition behavior** - October represents shoulder season
2. **Daily thermal cycling** - heating at night, cooling during day
3. **Peak thermal stress** - systems must handle both loads within 24 hours

### System Sizing Implications

- **Heating capacity** must handle 38,384 W peak hourly demand
- **Cooling capacity** must handle 98,441 W peak hourly demand
- **Net cooling rate** peaks at 98,441 W (3 PM)
- **Net heating rate** peaks at -38,384 W (3 AM, shown as negative)

## Output Files Generated

1. **peak_coincident_day_analysis_optimized.html** - Interactive visualization
2. **peak_coincident_day_hourly_data_optimized.csv** - Complete hourly data
3. **direct_coincidence_analysis.py** - Analysis script

## Analysis Method Validation

✅ **Single-pass optimization achieved**  
✅ **All 54 zones processed** (27 heating + 27 cooling)  
✅ **Annual maximum fractions calculated correctly**  
✅ **Coincidence threshold applied** (>10% for both systems)  
✅ **Peak day identification successful**  
✅ **Hourly profile extraction complete**  
✅ **Visualization generation successful**

## Usage Notes

- **Model ID format verified:** ASHRAE901|HotelLarge|STD2025|Buffalo|gshp
- **RDD ID ranges confirmed:** Heating (5692-5752), Cooling (5693-5753)
- **Negative rate conversion applied** for EnergyPlus data consistency
- **Error prevention implemented** for NoneType issues
- **Comprehensive data validation** throughout process

This analysis successfully identified the critical coincident day when both heating and cooling systems experience significant simultaneous demand, providing valuable insights for HVAC system design and operation optimization.
