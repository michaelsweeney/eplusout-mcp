# EnergyPlus MCP Server Instructions

## Overview

This MCP (Model Context Protocol) server provides comprehensive access to EnergyPlus building energy simulation results through an advanced set of tools that can discover, analyze, and extract data from EnergyPlus model files. The server includes pandas integration, keyword searching, and comprehensive logging capabilities.

## Available Tools Overview

### Core Model Management

- `initialize_model_map()` - Initialize/refresh model catalog cache
- `get_available_models()` - List all available models with metadata
- `get_usage_instructions()` - Get this documentation

### HTML Table Analysis

- `get_html_table_by_tuple()` - Retrieve specific HTML tables
- `search_html_tables_by_keyword()` - Find tables using keyword search
- `execute_pandas_on_html_table()` - Run pandas queries on HTML tables
- `execute_multiline_pandas_on_html_table()` - Run complex pandas analysis on HTML tables

### Timeseries Data Analysis

- `get_sql_available_hourlies()` - List available hourly variables with RDD IDs
- `get_timeseries_report_by_rddid()` - Extract timeseries data by RDD ID
- `execute_pandas_on_timeseries()` - Run pandas queries on timeseries data
- `execute_multiline_pandas_on_timeseries()` - Run complex pandas analysis on timeseries data

### epJSON Model Exploration

- `search_epjson_objects()` - Search building model objects with flexible criteria
- `get_object_properties()` - Get detailed properties of specific objects
- `list_objects_by_type()` - List all objects of a specific EnergyPlus type
- `search_related_objects()` - Find related objects using name patterns

### General Data Processing

- `execute_query()` - Execute pandas queries on cached DataFrames
- `execute_multiline_query()` - Execute multi-line pandas code on cached DataFrames

## File Structure

Each EnergyPlus model consists of three main file types:

- **`.epJSON`** - Input model definition (building geometry, materials, HVAC systems, schedules)
- **`.sql`** - Simulation results database (hourly timeseries data, summary tables)
- **`.table.htm`** - HTML summary reports (tabular summaries of results)

## Model Discovery (Filename-Agnostic)

The server automatically discovers and groups files by **directory location and filename stem** (filename without extension). This means the server works with **any filename pattern** - there is no required naming convention.

Examples of valid filenames that are automatically discovered:
- `ASHRAE901_HotelLarge_STD2025_Buffalo_SkipEC_gshp.epJSON`
- `my_model_v1.sql`
- `building_simulation.htm`

Model IDs are generated as: `{relative_directory}/{filename_stem}`

Examples:
- `eplus_files/run1/eplusout`
- `simulations/hotel_model`
- `data/ASHRAE901_HotelLarge_STD2025_Buffalo_SkipEC_gshp`

## Available Building Types

- **HotelLarge** - Large hotel building prototype
- **Warehouse** - Warehouse building prototype

## Available HVAC Systems

Based on actual data files available:

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
- **pszvav_gas** - Packaged Single Zone VAV with Gas (Warehouse only)

## Available Locations

- **Buffalo** - Cold climate (upstate New York)
- **Tampa** - Hot climate (Florida)

## MCP Tool Workflow

### 1. Initialize the Model Map

```python
initialize_model_map(directory='eplus_files')
```

This scans the directory and creates a cached inventory of all available models. **Always start here.**

### 2. Discover Available Models

```python
models = get_available_models(directory='eplus_files')
```

Returns a list of all models with their metadata. Example model IDs:
- `eplus_files/run1/eplusout`
- `simulations/buffalo_hotel_gshp`
- `data/model_v2`

### 3. Explore Model Data

Using the `model_id` from step 2, you can:

#### Search HTML Tables by Keywords

```python
# First get your model_id from get_available_models()
models = get_available_models()
model_id = models[0]['model_id']  # e.g., 'eplus_files/run1/eplusout'

search_html_tables_by_keyword(
    id=model_id,
    keywords=['cooling', 'sizing', 'capacity'],
    case_sensitive=False
)
```

Returns tables matching keywords like:

- HVAC Sizing Summary
- Component Sizing Summary
- Zone Component Loads Summary

#### Get Specific HTML Tables

```python
get_html_table_by_tuple(
    id=model_id,
    query_tuple=('Entire Facility', 'HVAC Sizing Summary', 'Zone Sensible Cooling')
)
```

#### Get Timeseries Variables

```python
get_sql_available_hourlies(id=model_id)
```

Returns available hourly timeseries variables with their RDD IDs for data extraction.

#### Search Building Model Objects

```python
search_epjson_objects(
    model_id=model_id,
    search_pattern='cooling',
    case_sensitive=False
)
```

### 4. Extract Specific Timeseries Data

```python
get_timeseries_report_by_rddid(
    model_id=model_id,
    rddid=123
)
```

Returns hourly data for a specific variable (use RDD ID from step 3).

### 5. Advanced Data Analysis with Pandas

#### Single-Line Pandas Queries

```python
# Simple statistics on timeseries data
execute_pandas_on_timeseries(
    model_id=model_id,
    rddid=179,
    query="df['Value'].mean()"
)

# HTML table analysis
execute_pandas_on_html_table(
    id=model_id,
    query_tuple=('Entire Facility', 'HVAC Sizing Summary', 'Zone Sensible Cooling'),
    query="df.describe()"
)
```

#### Multi-Line Pandas Analysis

```python
# Complex timeseries analysis
execute_multiline_pandas_on_timeseries(
    model_id=model_id,
    rddid=179,
    code='''
    # Convert energy units and calculate monthly totals
    df['kWh'] = df['Value'] / 3.6e6
    df['month'] = df['dt'].dt.month
    monthly_consumption = df.groupby('month')['kWh'].sum()

    # Calculate peaks and averages
    monthly_peaks = df.groupby('month')['kWh'].max()

    result = {
        'monthly_totals': monthly_consumption.to_dict(),
        'monthly_peaks': monthly_peaks.to_dict()
    }
    '''
)

# Complex HTML table analysis
execute_multiline_pandas_on_html_table(
    id=model_id,
    query_tuple=('Entire Facility', 'HVAC Sizing Summary', 'Zone Sensible Cooling'),
    code='''
    # Convert to numeric and calculate totals
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    totals = df[numeric_cols].sum()

    # Calculate percentages
    percentages = (df[numeric_cols] / totals) * 100

    result = percentages
    '''
)
```

Returns hourly data for a specific variable (use RDD ID from step 3).

## Common Use Cases

### Compare HVAC Systems Energy Performance

```python
# 1. Get all available models
models = get_available_models()

# 2. Extract and analyze energy consumption for each model
for model in models:
    model_id = model['model_id']

    # Get electricity consumption timeseries (typically RDD ID 179)
    energy_analysis = execute_multiline_pandas_on_timeseries(
        model_id=model_id,
        rddid=179,
        code='''
        # Convert to kWh and calculate annual total
        df['kWh'] = df['Value'] / 3.6e6
        annual_total = df['kWh'].sum()
        peak_demand = df['kWh'].max()

        result = {
            'model_id': model_id,
            'annual_kwh': annual_total,
            'peak_kw': peak_demand
        }
        '''
    )
```

### Climate Impact Analysis

```python
# 1. Get all available models
models = get_available_models()

# 2. Extract heating vs cooling energy patterns for each location
for model in models:
    model_id = model['model_id']

    climate_analysis = execute_multiline_pandas_on_timeseries(
        model_id=model_id,
        rddid=179,
        code='''
        # Calculate seasonal energy patterns
        df['kWh'] = df['Value'] / 3.6e6
        df['month'] = df['dt'].dt.month

        # Winter months (Dec, Jan, Feb)
        winter_energy = df[df['month'].isin([12, 1, 2])]['kWh'].sum()

        # Summer months (Jun, Jul, Aug)
        summer_energy = df[df['month'].isin([6, 7, 8])]['kWh'].sum()

        result = {
            'model_id': model_id,
            'winter_kwh': winter_energy,
            'summer_kwh': summer_energy,
            'cooling_vs_heating_ratio': summer_energy / winter_energy if winter_energy > 0 else 'inf'
        }
        '''
    )
```

### Building Performance Deep Dive

```python
# Get a model_id first
models = get_available_models()
model_id = models[0]['model_id']

# 1. Get building characteristics from epJSON
building_components = search_epjson_objects(
    model_id=model_id,
    search_pattern='Zone',
    case_sensitive=False
)

# 2. Get HVAC sizing information
hvac_sizing = search_html_tables_by_keyword(
    id=model_id,
    keywords=['sizing', 'capacity', 'coil']
)

# 3. Analyze zone-level performance
zone_cooling_loads = get_html_table_by_tuple(
    id=model_id,
    query_tuple=('Entire Facility', 'HVAC Sizing Summary', 'Zone Sensible Cooling')
)

# 4. Run complex analysis combining multiple data sources
load_analysis = execute_pandas_on_html_table(
    id=model_id,
    query_tuple=('Entire Facility', 'HVAC Sizing Summary', 'Zone Sensible Cooling'),
    query="df.groupby(df.index)['Calculated Design Load [W]'].sum()"
)
```

### Advanced Keyword Searching

```python
# Get a model_id first
models = get_available_models()
model_id = models[0]['model_id']

# Find all cooling-related data
cooling_tables = search_html_tables_by_keyword(
    id=model_id,
    keywords=['cooling', 'coil', 'capacity', 'chiller', 'dx cooling'],
    case_sensitive=False
)

# Find energy consumption summaries
energy_tables = search_html_tables_by_keyword(
    id=model_id,
    keywords=['energy', 'consumption', 'end use', 'utility'],
    case_sensitive=False
)

# Find HVAC component details
hvac_tables = search_html_tables_by_keyword(
    id=model_id,
    keywords=['fan', 'pump', 'air loop', 'plant loop'],
    case_sensitive=False
)
```

## Data Types in Returns

### Model Summary Data

Each model includes:

- `model_id`: Unique identifier (e.g., 'ASHRAE901|HotelLarge|STD2025|Buffalo|gshp')
- `codename`: Standard (e.g., 'ASHRAE901')
- `prototype`: Building type ('HotelLarge', 'Warehouse')
- `codeyear`: Code year (e.g., 'STD2025')
- `city`: Location ('Buffalo', 'Tampa')
- `label`: HVAC system type (e.g., 'gshp', 'vav_ac_blr')
- File paths for epJSON, SQL, and HTML files

### Timeseries Data

Each timeseries record contains:

- `dt`: Timestamp (datetime)
- `Value`: Numeric value (float)
- `Name`: Variable name (e.g., 'Facility Total Electric Demand Power')
- `KeyValue`: Zone or component identifier
- `Units`: Units of measurement (e.g., 'J', 'W')
- `ReportingFrequency`: Data frequency ('Hourly')
- `Type`: Data type ('Sum', 'Avg')

### HTML Table Data

Tables are returned as lists of dictionaries with column headers as keys.

### Search Results

Search functions return structured data with:

- `search_results`: Matching items organized by type/category
- `search_criteria`: The search parameters used
- `search_stats`: Statistics about matches found
- `total_matches`: Number of items found

## Advanced Features

### Pandas Execution Environment

The server provides secure pandas execution with:

**Available Libraries:**

- `df`: The target DataFrame
- `pd`: pandas library
- `np`: numpy library
- Built-in functions: `len`, `str`, `int`, `float`, `list`, `dict`, `sum`, `max`, `min`

**Security Features:**

- Restricted execution environment
- No file system access
- No dangerous function imports
- Safe error handling

**Usage Patterns:**

- Single-line: Return value directly from expression
- Multi-line: Use `result = ...` to specify return value

### Keyword Search Categories

**Energy & Consumption:**
`['energy', 'consumption', 'end use', 'site energy', 'source energy', 'electricity', 'natural gas', 'fuel', 'annual', 'monthly', 'utility', 'cost', 'performance']`

**Cooling Systems:**
`['cooling', 'coil', 'capacity', 'chiller', 'dx cooling', 'sensible cooling', 'latent cooling', 'peak cooling', 'cooling tower', 'evaporative cooler', 'refrigeration']`

**Heating Systems:**
`['heating', 'boiler', 'heat pump', 'heating coil', 'heat recovery', 'sensible heating', 'peak heating', 'furnace', 'baseboard', 'radiant heating', 'heat exchanger']`

**HVAC Components:**
`['fan', 'pump', 'air loop', 'plant loop', 'zone equipment', 'terminal unit', 'ahu', 'air handler', 'vav', 'cav']`

**Building Envelope:**
`['window', 'wall', 'roof', 'floor', 'construction', 'material', 'thermal bridge', 'infiltration', 'ventilation']`

**Lighting & Equipment:**
`['lighting', 'electric equipment', 'gas equipment', 'occupancy', 'schedule', 'internal load', 'plug load']`

### Logging and Monitoring

All function calls are logged with:

- Timestamp
- Function name
- Input/output token counts
- Execution time
- Parameters summary
- Result summary

Logs are stored in: `monitor_logs/mcp_calls.log`

## Tips for Effective Use

1. **Always start with `initialize_model_map()`** to initialize the cache
2. **Use `get_available_models()`** to discover available models and get their model_ids
3. **Model IDs are generated from directory structure and filename stem** (e.g., `eplus_files/run1/eplusout`)
4. **Filename format is flexible** - the server works with any filename pattern
5. **Use keyword search** with `search_html_tables_by_keyword()` to find relevant tables quickly
6. **Check `get_sql_available_hourlies()`** to see what timeseries variables are available before extracting data
7. **Use pandas functions** for complex data analysis instead of extracting raw data
8. **For large datasets**, use multi-line pandas code with summary calculations rather than returning full datasets
9. **Leverage search functions** to explore unfamiliar models before extracting specific data
10. **Use tuple format** for HTML table queries: `(report_for, report_name, table_name)`

## Function Reference Quick Guide

### Essential Workflow Functions

```python
# Start here - ALWAYS
initialize_model_map()
models = get_available_models()

# Find what you need
tables = search_html_tables_by_keyword(id, ['cooling', 'sizing'])
variables = get_sql_available_hourlies(id)

# Get specific data
table_data = get_html_table_by_tuple(id, tuple)
timeseries = get_timeseries_report_by_rddid(model_id, rddid)

# Analyze with pandas
analysis = execute_multiline_pandas_on_timeseries(model_id, rddid, code)
```

### Exploration Functions

```python
# Find objects in building model
objects = search_epjson_objects(model_id, search_pattern='cooling')
properties = get_object_properties(model_id, object_type, object_name)
all_coils = list_objects_by_type(model_id, 'Coil:Cooling:DX:SingleSpeed')
related = search_related_objects(model_id, 'ROOM_1_FLR_3')
```

## Error Handling

- **Invalid model_id**: Returns error message with available options
- **Missing RDD ID**: Returns empty list with status message
- **Pandas execution errors**: Returns formatted error message with line number
- **File access issues**: Returns descriptive error with troubleshooting suggestions
- **Invalid table tuples**: Returns error with available table names

## Performance Notes

- **Model map caching**: Subsequent calls are fast after initial `initialize_model_map()`
- **Large dataset handling**: Results automatically truncated to prevent token overflow
- **Pandas execution**: Runs in restricted environment for security and performance
- **Search optimization**: Keyword searches are case-insensitive and efficient
- **Token tracking**: All calls logged for performance monitoring

## Troubleshooting

### Common Issues

1. **"Model not found"**: Run `initialize_model_map()` first, then check `get_available_models()`
2. **"Empty timeseries result"**: Verify RDD ID exists using `get_sql_available_hourlies()`
3. **"Table not found"**: Use `search_html_tables_by_keyword()` to find available tables
4. **"Pandas execution error"**: Check syntax and use only allowed functions/libraries
5. **"Permission denied"**: Ensure directory access and file permissions are correct

### Getting Help

```python
# Get complete documentation
help_text = get_usage_instructions()

# Explore available data
models = get_available_models()
tables = search_html_tables_by_keyword(model_id, ['summary'])
variables = get_sql_available_hourlies(model_id)
```
