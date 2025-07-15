# EnergyPlus MCP Server Instructions

## Overview

This MCP (Model Context Protocol) server provides access to EnergyPlus building energy simulation results through a set of tools that can discover, analyze, and extract data from EnergyPlus model files.

## File Structure

Each EnergyPlus model consists of three main file types:

- **`.epJSON`** - Input model definition (building geometry, materials, HVAC systems, schedules)
- **`.sql`** - Simulation results database (hourly timeseries data, summary tables)
- **`.table.htm`** - HTML summary reports (tabular summaries of results)

## Model Naming Convention

Files follow this naming pattern:
`{CODENAME}_{PROTOTYPE}_{CODEYEAR}_{CITY}_{SKIPOPTIONS}_{HVAC_LABEL}.{EXTENSION}`

Example: `ASHRAE901_HotelLarge_STD2025_Buffalo_SkipEC_gshp.epJSON`

## Available Building Types

- **HotelLarge** - Large hotel building prototype
- **Warehouse** - Warehouse building prototype

## Available HVAC Systems

- **gshp** - Ground Source Heat Pump
- **pkgdx_gas** - Packaged DX with Gas
- **pkgdx_hp** - Packaged DX Heat Pump
- **pvav_awhp** - Packaged VAV with Air-to-Water Heat Pump
- **pvav_blr** - Packaged VAV with Boiler
- **vav_ac_blr** - VAV with Air-Cooled Chiller and Boiler
- **vav_ac_blr_doas** - VAV with Air-Cooled Chiller, Boiler, and DOAS
- **vav_wc_blr** - VAV with Water-Cooled Chiller and Boiler
- **vrf** - Variable Refrigerant Flow
- **wshp_gas** - Water Source Heat Pump with Gas
- **pszvav_gas** - Packaged Single Zone VAV with Gas

## Available Locations

- **Buffalo** - Cold climate (upstate New York)
- **Tampa** - Hot climate (Florida)

## MCP Tool Workflow

### 1. Initialize the Model Map

```
setup_model_map(directory='eplus_files')
```

This scans the directory and creates a cached inventory of all available models.

### 2. Discover Available Models

```
get_available_models(directory='eplus_files')
```

Returns a list of all models with their metadata and unique `model_id` values.

### 3. Explore Model Data

Using the `model_id` from step 2, you can:

#### Get HTML Report Tables

```
get_html_table_names(id='ASHRAE901|HotelLarge|STD2025|Buffalo|gshp')
```

Returns names of available summary tables like:

- Annual Building Utility Performance Summary
- HVAC Sizing Summary
- Zone Component Loads Summary

#### Get Timeseries Variables

```
get_sql_available_hourlies(id='ASHRAE901|HotelLarge|STD2025|Buffalo|gshp')
```

Returns available hourly timeseries variables with their RDD IDs.

#### Get Model Input Data

```
get_epjson_dict(id='ASHRAE901|HotelLarge|STD2025|Buffalo|gshp')
```

Returns the complete building model definition as a Python dictionary.

### 4. Extract Specific Timeseries Data

```
get_timeseries_report_by_rddid(model_id='ASHRAE901|HotelLarge|STD2025|Buffalo|gshp', rddid=123)
```

Returns hourly data for a specific variable (use RDD ID from step 3).

## Common Use Cases

### Compare HVAC Systems

1. Get models for the same building type and location with different HVAC systems
2. Extract energy consumption data for each system
3. Compare performance metrics

### Climate Analysis

1. Get models for the same building/HVAC combination in different cities
2. Extract heating/cooling energy data
3. Analyze climate impact on energy use

### Building Performance Analysis

1. Get epJSON data to understand building characteristics
2. Extract relevant timeseries data (temperatures, energy use, etc.)
3. Analyze relationships between building design and performance

## Data Types in Returns

### Model Summary Data

- `model_id`: Unique identifier for the model
- `codename`: Standard (e.g., 'ASHRAE901')
- `prototype`: Building type
- `codeyear`: Code year
- `city`: Location
- `label`: HVAC system type

### Timeseries Data

- `dt`: Timestamp
- `Value`: Numeric value
- `Name`: Variable name
- `KeyValue`: Zone or component identifier
- `Units`: Units of measurement

## Tips for Effective Use

1. **Always start with `setup_model_map()`** to initialize the cache
2. **Use `get_available_models()`** to discover what's available before diving into specific models
3. **Check `get_sql_available_hourlies()`** to see what timeseries variables are available before extracting data
4. **Model IDs are case-sensitive** and must match exactly
5. **Timeseries data can be large** - consider filtering or sampling for initial exploration
6. **HTML table names vary by model** - always check what's available first

## Error Handling

- If a model_id is not found, the tool will return an error
- If RDD ID doesn't exist, you'll get an empty result
- File permission issues may occur if the directory is not accessible

## Performance Notes

- The model map is cached for fast access after initial setup
- Large timeseries datasets may take time to extract
- Consider using specific time ranges or variables rather than extracting all data at once
