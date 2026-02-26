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

## Model Discovery

The server automatically discovers models by scanning for `.epJSON`, `.sql`, and `.htm` files in the specified directory. Models are identified by their **directory location and filename stem** (filename without extension), making the server **completely filename-agnostic**. Files can use any naming convention.

Examples of valid model filenames:
- `ASHRAE901_HotelLarge_STD2025_Buffalo_SkipEC_gshp.epJSON`
- `my_building_model_v1.sql`
- `simple_model.htm`

All are discovered and grouped correctly regardless of naming pattern.

## Available Data

### Example Files Location

The `example-files` directory contains sample EnergyPlus models. See `example-files/about.md` for the location of the original project files these were copied from.

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
# Get the model_id from get_available_models() first
models = get_available_models()
model_id = models[0]['model_id']  # e.g., 'eplus_files/run1/eplusout'

# Find cooling-related tables
cooling_tables = search_html_tables_by_keyword(
    id=model_id,
    keywords=['cooling', 'sizing', 'capacity']
)

# Get available timeseries variables
timeseries_vars = get_sql_available_hourlies(id=model_id)
```

### 3. Extract and Analyze Data

```python
# Get a specific HTML table
sizing_data = get_html_table_by_tuple(
    id=model_id,
    query_tuple=('Entire Facility', 'HVAC Sizing Summary', 'Zone Sensible Cooling')
)

# Analyze timeseries data with pandas
energy_analysis = execute_multiline_pandas_on_timeseries(
    model_id=model_id,
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

## Future Security & Code Quality Considerations

This section documents security and code quality issues identified during review that should be addressed in future versions:

### Critical Security Issues (High Priority)

1. **SQL Injection Vulnerabilities** (`src/tools/func_sql.py`)
   - F-string SQL queries with user-controlled `rddid` parameter (lines 413, 424)
   - String concatenation with dynamic data in SQL queries (line 474)
   - **Mitigation:** Use parameterized queries with `?` placeholders instead of string formatting
   - **Impact:** Could allow attackers to exfiltrate or modify database contents

2. **Unsafe Pickle Deserialization** (`src/model_data.py`)
   - Model map cached using `pickle` which can execute arbitrary code if tampered with (lines 316, 587, 591)
   - **Mitigation:** Replace with JSON serialization or safer formats (protobuf, msgpack with schema validation)
   - **Impact:** If cache file is compromised, arbitrary code execution is possible
   - **Note:** Currently low risk as cache is local-only, but should be addressed for production use

3. **Unsafe Code Execution** (`src/dataloader.py`)
   - Use of `eval()` and `exec()` for pandas queries (lines 122, 233)
   - **Current Mitigation:** Restricted globals dictionary limits available functions
   - **Remaining Risk:** Can still access object attributes and methods to potentially bypass restrictions
   - **Recommendation:** Replace with safer expression evaluation (numexpr, asteval with sandboxing, or AST validation)

### High Priority Issues

4. **Unvalidated File Paths** (`src/tools/func_sql.py`)
   - No validation that SQL file paths are within expected directories
   - **Risk:** Path traversal attacks could access files outside intended scope
   - **Mitigation:** Add path validation using `Path.resolve()` and `Path.is_relative_to()`

5. **Missing Input Validation**
   - No bounds checking on string parameters (search patterns, keywords, code queries)
   - **Risk:** Could cause DoS attacks via extremely long regex patterns or code
   - **Mitigation:** Add input length validation and type checking to all user-facing tools

6. **Bare Exception Handling**
   - `except Exception as e:` catches all exceptions including SystemExit and KeyboardInterrupt (func_html.py:30, 206)
   - **Mitigation:** Catch specific exceptions only (FileNotFoundError, IOError, etc.)

### Code Quality Issues

7. **Dead Code & Broken Functions** (`src/tools/func_sql.py`)
   - `_exec_query()` function has a bug (execute() called without query parameter, line 88)
   - `old_getseries()` method is obsolete but not removed (lines 461-498)
   - Unreachable return statement in `availseries()` (line 382)
   - **Action:** Remove broken functions or properly implement and use them

8. **Unused Imports**
   - Multiple files have unused imports (func_epjson.py, func_html.py, helpers.py)
   - **Action:** Clean up to reduce code complexity

9. **Logging Issues**
   - `print()` statements used instead of logging module (model_data.py, func_sql.py)
   - No log levels (ERROR, WARNING, INFO, DEBUG)
   - **Action:** Replace with proper logging configuration

10. **Sensitive Data in Logs** (`src/monitor.py`)
    - Full arguments logged which may contain file paths or sensitive data
    - **Mitigation:** Sanitize logged arguments, avoid logging full file paths

### Known Bugs to Fix

- `get_tables()` in `src/model_data.py:123` instantiates wrong class (SqlTimeseries instead of SqlTables)
- Parameter mismatch in logging decorator (`src/monitor.py`) between function signature and call site
- Missing log entry keys in `get_log_stats()` that are expected to exist

### Testing Gaps

- No automated tests present in repository
- Recommended: Add unit tests for SQL functions, input validation, and data extraction tools
- Add integration tests for end-to-end workflows

## Support

For detailed usage instructions and examples, use:

```python
get_usage_instructions()
```

This returns the complete CLAUDE.md documentation file with comprehensive examples and best practices.
"# eplusout-mcp" 
