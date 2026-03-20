# EnergyPlus MCP Server Instructions

## Overview

This MCP server provides access to EnergyPlus building energy simulation results. It discovers model files, extracts data from SQL databases and HTML reports, and lets you explore epJSON building definitions.

## Available Tools

### Model Management
- `initialize_model_map(directory)` — Scan a directory for EnergyPlus files. **Call this first.**
- `get_available_models()` — List all discovered models with IDs and file paths
- `get_usage_instructions()` — Get this documentation

### HTML Tables
- `search_html_tables_by_keyword(id, keywords, case_sensitive)` — Find tables by keyword
- `get_html_table_by_tuple(id, query_tuple)` — Get a specific table by `(report_for, report_name, table_name)`

### Timeseries
- `get_sql_available_hourlies(id)` — List available hourly variables with RDD IDs
- `get_timeseries_report_by_rddid_list(model_id, rddid)` — Extract timeseries data by list of RDD IDs

### epJSON Exploration
- `search_epjson_objects(model_id, object_type, object_name, search_pattern, case_sensitive)` — Search model objects
- `get_object_properties(model_id, object_type, object_name)` — Get all properties of a specific object
- `list_objects_by_type(model_id, object_type)` — List all objects of a given type
- `search_related_objects(model_id, search_pattern)` — Find objects related to a component or zone

### Debugging
- `get_error_file(id)` — Read the EnergyPlus error file
- `get_rdd_file(id)` — Read the RDD (Report Data Dictionary) file

## Workflow

### 1. Initialize

```python
initialize_model_map(directory='example-files')
```

Scans the directory recursively for `.epJSON`, `.sql`, and `.htm` files, grouping them by directory and filename stem.

### 2. Discover Models

```python
models = get_available_models()
```

Returns a list with `model_id`, `directory`, `stem`, `display_name`, and `files` (paths to epJSON/sql/html).

### 3. Explore Data

```python
model_id = models[0]['model_id']

# Find tables by keyword
search_html_tables_by_keyword(id=model_id, keywords=['cooling', 'sizing'])

# Get a specific table
get_html_table_by_tuple(id=model_id, query_tuple=('Entire Facility', 'HVAC Sizing Summary', 'Zone Sensible Cooling'))

# List available timeseries variables
get_sql_available_hourlies(id=model_id)

# Search building model objects
search_epjson_objects(model_id=model_id, search_pattern='cooling')
```

### 4. Extract Timeseries

```python
# Use RDD IDs from get_sql_available_hourlies()
get_timeseries_report_by_rddid_list(model_id=model_id, rddid=[179])
```

Returns a DataFrame with columns named `{KeyValue}-{Name}-{TimestepType}-{Units}` and a datetime index.

## Model Discovery

Files are grouped by **directory + filename stem**. Any naming convention works:
- `run1/eplusout.sql` + `run1/eplusout.epJSON` → model ID `run1/eplusout`
- `results/MyBuilding.sql` + `results/MyBuilding.htm` → model ID `results/MyBuilding`

## File Types

- **`.epJSON`** — Input model (geometry, materials, HVAC, schedules)
- **`.sql`** — SQLite results database (hourly timeseries, summary tables)
- **`.table.htm`** — HTML summary reports (tabular result summaries)

## Data Returned

### Model Info
- `model_id`: Unique identifier for use with other tools
- `directory`: Path where model files are located
- `stem`: Filename without extension
- `files`: Dict of available file paths (`epjson`, `sql`, `html`)

### Timeseries Records
- `dt`: Timestamp
- `Value`: Numeric value
- `Name`: Variable name (e.g., `Electricity:Facility`)
- `KeyValue`: Zone or component identifier
- `Units`: Units of measurement (e.g., `J`, `W`)

### HTML Tables
Returned as lists of dictionaries with column headers as keys.

### Search Results
- `search_results`: Matching items organized by type
- `search_criteria`: Parameters used
- `search_stats`: Match statistics

## Keyword Search Categories

**Energy**: `energy`, `consumption`, `end use`, `electricity`, `natural gas`, `annual`, `monthly`, `utility`

**Cooling**: `cooling`, `coil`, `capacity`, `chiller`, `dx cooling`, `sensible cooling`, `peak cooling`

**Heating**: `heating`, `boiler`, `heat pump`, `heating coil`, `heat recovery`, `peak heating`, `furnace`

**HVAC**: `fan`, `pump`, `air loop`, `plant loop`, `zone equipment`, `terminal unit`, `vav`

**Envelope**: `window`, `wall`, `roof`, `floor`, `construction`, `infiltration`, `ventilation`

**Internal Loads**: `lighting`, `electric equipment`, `gas equipment`, `occupancy`, `schedule`

## Error Handling

- **Invalid model_id**: Raises `ValueError` with list of available model IDs
- **Missing file type**: If a model has no `.sql` file, timeseries tools will fail — check `files` in model info
- **Invalid table tuple**: Returns empty list — use `search_html_tables_by_keyword()` to find valid tuples

## Tips

1. Always start with `initialize_model_map()`
2. Use `get_available_models()` to get model IDs and see which file types are available
3. Use `search_html_tables_by_keyword()` to find tables before requesting specific ones
4. Check `get_sql_available_hourlies()` for RDD IDs before extracting timeseries
5. Use tuple format `(report_for, report_name, table_name)` for HTML table queries
