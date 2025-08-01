# EnergyPlus MCP Server

## Overview

This Model Context Protocol (MCP) server provides comprehensive access to EnergyPlus building energy simulation results through a rich set of tools for discovering, analyzing, and extracting data from EnergyPlus model files. The server includes advanced features like pandas-based data analysis, keyword-based table searching, and comprehensive logging with token consumption tracking.

## Key Features

- **Comprehensive Data Access**: Read epJSON input files, SQL result databases, and HTML summary reports
- **Advanced Search Capabilities**: Search HTML tables by keywords, find related epJSON objects, and explore model components
- **Pandas Integration**: Execute pandas queries directly on timeseries and tabular data
- **Logging & Monitoring**: Built-in token consumption tracking and function call monitoring
- **Flexible Model Discovery**: Automatic model cataloging and metadata extraction

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd mcp-eplus-outputs

# Install dependencies
uv sync

# Run the server
uv run main.py
```

## Configuration

Add to your Claude Desktop configuration:

```json
{
  "mcpServers": {
    "mcp_eplus_outputs": {
      "command": "uv",
      "args": ["--directory", "C:/path/to/mcp-eplus-outputs", "run", "main.py"]
    }
  }
}
```

## File Structure

Each EnergyPlus model consists of three main file types:

- **`.epJSON`** - Input model definition (building geometry, materials, HVAC systems, schedules)
- **`.sql`** - Simulation results database (hourly timeseries data, summary tables)
- **`.table.htm`** - HTML summary reports (tabular summaries of results)

## Model Naming Convention

Files follow this pattern:
`{CODENAME}_{PROTOTYPE}_{CODEYEAR}_{CITY}_{SKIPOPTIONS}_{HVAC_LABEL}.{EXTENSION}`

Example: `ASHRAE901_HotelLarge_STD2025_Buffalo_SkipEC_gshp.epJSON`

## Available Data

### Building Types

- **HotelLarge** - Large hotel building prototype
- **Warehouse** - Warehouse building prototype

### HVAC Systems

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

### Locations

- **Buffalo** - Cold climate (upstate New York)
- **Tampa** - Hot climate (Florida)

## Available Tools

### Core Model Management

- `initialize_model_map()` - Initialize model catalog
- `get_available_models()` - List all available models with metadata
- `get_usage_instructions()` - Get comprehensive usage documentation

### HTML Table Analysis

- `get_html_table_by_tuple()` - Retrieve specific HTML tables
- `search_html_tables_by_keyword()` - Find tables by keyword search
- `execute_pandas_on_html_table()` - Run pandas queries on HTML tables
- `execute_multiline_pandas_on_html_table()` - Run complex pandas code on HTML tables

### Timeseries Data Analysis

- `get_sql_available_hourlies()` - List available hourly variables
- `get_timeseries_report_by_rddid()` - Extract timeseries data by RDD ID
- `execute_pandas_on_timeseries()` - Run pandas queries on timeseries data
- `execute_multiline_pandas_on_timeseries()` - Run complex pandas code on timeseries data

### epJSON Model Exploration

- `search_epjson_objects()` - Search building model objects
- `get_object_properties()` - Get detailed object properties
- `list_objects_by_type()` - List all objects of specific type
- `search_related_objects()` - Find related objects by pattern

### General Data Processing

- `execute_query()` - Execute pandas queries on cached data
- `execute_multiline_query()` - Execute multi-line pandas code on cached data

## Quick Start Guide

### 1. Initialize the System

```python
# Always start here
initialize_model_map(directory='eplus_files')

# Discover available models
models = get_available_models()
```

### 2. Explore Available Data

```python
# Find cooling-related tables
cooling_tables = search_html_tables_by_keyword(
    id='ASHRAE901|HotelLarge|STD2025|Buffalo|gshp',
    keywords=['cooling', 'sizing', 'capacity']
)

# Get available timeseries variables
timeseries_vars = get_sql_available_hourlies(
    id='ASHRAE901|HotelLarge|STD2025|Buffalo|gshp'
)
```

### 3. Extract and Analyze Data

```python
# Get a specific HTML table
sizing_data = get_html_table_by_tuple(
    id='ASHRAE901|HotelLarge|STD2025|Buffalo|gshp',
    query_tuple=('Entire Facility', 'HVAC Sizing Summary', 'Zone Sensible Cooling')
)

# Analyze timeseries data with pandas
energy_analysis = execute_multiline_pandas_on_timeseries(
    model_id='ASHRAE901|HotelLarge|STD2025|Buffalo|gshp',
    rddid=179,
    code='''
    # Convert energy units and calculate monthly totals
    df['kWh'] = df['Value'] / 3.6e6
    df['month'] = df['dt'].dt.month
    monthly_consumption = df.groupby('month')['kWh'].sum()
    result = monthly_consumption.to_dict()
    '''
)
```

## Advanced Features

### Pandas Integration

The server includes secure pandas execution environments for both HTML table and timeseries data:

- **Single-line queries**: Use `execute_pandas_on_*` functions
- **Multi-line code**: Use `execute_multiline_pandas_on_*` functions with `result = ...` pattern
- **Security**: Restricted execution environment prevents dangerous operations

### Keyword Search

Find relevant data using flexible keyword searching:

```python
# Search for energy consumption tables
energy_tables = search_html_tables_by_keyword(
    id=model_id,
    keywords=['energy', 'consumption', 'end use'],
    case_sensitive=False
)
```

### Comprehensive Logging

All function calls are logged with token consumption tracking in `monitor_logs/mcp_calls.log`.

## Performance Considerations

- Model map is cached for fast repeated access
- Large datasets are automatically truncated in responses
- HTML table search is optimized for performance
- Token consumption is monitored and logged

## Error Handling

- Invalid model IDs return descriptive error messages
- Missing data returns empty results with status information
- Pandas execution errors are caught and reported safely

## Token Management

The server includes comprehensive token counting and logging:

- Input/output tokens tracked per function call
- Logs stored in JSON format for analysis
- Automatic result truncation to prevent token overflow

## Support

For detailed usage instructions and examples, use:

```python
get_usage_instructions()
```

This returns the complete CLAUDE.md documentation file with comprehensive examples and best practices.
