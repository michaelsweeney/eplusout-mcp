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

## AI Documentation & Analysis

The `ai-docs/` folder contains detailed analysis documents generated during code review and security audits:

- **SECURITY_REVIEW.md** - Complete security vulnerability analysis with risk assessment
- **SECURITY_FIXES_APPLIED.md** - Detailed implementation summary of all security fixes
- **ADDITIONAL_QUICK_FIXES.md** - Code quality and reliability improvements

These documents are generated by AI assistants during development iterations. Future developers and AI agents should:

1. **Always create analysis/review documents in the `ai-docs/` folder**, not the root directory
2. Use consistent naming: `*_REVIEW.md` for analysis, `*_FIXES_APPLIED.md` for implementations
3. Include implementation checklists and verification steps
4. Link to specific files and line numbers for reference

This keeps documentation organized and distinguishes AI-generated analysis from user-facing documentation.

## Security & Code Quality Status

### Recent Improvements (February 2026)

✅ **6 Security Issues Fixed**
- SQL Injection vulnerabilities (parameterized queries)
- Path traversal prevention (directory validation)
- Input validation (RDD ID type/range checking)
- Error information disclosure (generic error messages)
- Code execution sandbox hardening (AST-based attribute validation)

✅ **3 Code Quality Improvements**
- Removed unreachable code
- Replaced assert with proper exception handling
- Cleaned up debug comments

**See `ai-docs/` folder for detailed security audit reports.**

## Remaining Security & Code Quality Considerations

This section documents issues that remain for future versions. Many security issues have been addressed (see `ai-docs/` folder for details).

### ✅ Recently Fixed (February 2026)

- ✅ **SQL Injection** - Now using parameterized queries with `?` placeholders
- ✅ **Path Traversal** - Directory validation prevents `../` and absolute paths outside base directory
- ✅ **Input Validation** - RDD IDs now type-checked and range-validated
- ✅ **Error Disclosure** - Generic error messages; full details logged internally only
- ✅ **Code Execution Sandbox** - AST-based validation prevents dangerous attribute access
- ✅ **Dead Code** - Removed unreachable returns and debug comments
- ✅ **Exception Handling** - Replaced assert with proper ValueError exceptions

### Issues for Future Versions

1. **Unsafe Pickle Deserialization** (`src/model_data.py`)
   - Model map cached using `pickle` which can execute arbitrary code if tampered with
   - **Mitigation:** Replace with JSON serialization or safer formats (protobuf, msgpack)
   - **Note:** Currently low risk as cache is local-only

2. **Bare Exception Handling** (`src/tools/func_html.py`)
   - `except Exception as e:` catches all exceptions including SystemExit and KeyboardInterrupt
   - **Recommendation:** Catch specific exceptions only (FileNotFoundError, IOError, etc.)

3. **Unused Imports**
   - Multiple files have unused imports (func_epjson.py, func_html.py, helpers.py)
   - **Action:** Clean up to reduce code complexity

4. **Logging Issues**
   - Some `print()` statements used instead of logging module
   - **Action:** Consolidate logging for consistency

5. **Known Bugs**
   - `get_tables()` in `src/model_data.py:123` instantiates wrong class (SqlTimeseries instead of SqlTables)
   - Parameter mismatch in logging decorator (`src/monitor.py`)

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
