# EnergyPlus MCP Server

## Overview

This Model Context Protocol (MCP) server provides comprehensive access to EnergyPlus building energy simulation results through a rich set of tools for discovering, analyzing, and extracting data from EnergyPlus model files. The server includes advanced features like pandas-based data analysis, keyword-based table searching, and comprehensive logging with token consumption tracking.

## Key Features

- **Comprehensive Data Access**: Read epJSON input files, SQL result databases, and HTML summary reports
- **Advanced Search Capabilities**: Search HTML tables by keywords, find related epJSON objects, and explore model components
- **Pandas Integration**: Execute pandas queries directly on timeseries and tabular data
- **Logging & Monitoring**: Built-in token consumption tracking and function call monitoring
- **Flexible Model Discovery**: Automatic model cataloging and metadata extraction

## Quickstart: Setup with Claude Desktop

### Prerequisites

- [uv](https://docs.astral.sh/uv/getting-started/installation/) (Python package manager)
- [Claude Desktop](https://claude.ai/download)

### Step 1: Clone the repository

```bash
git clone https://github.com/your-org/mcp-eplus-outputs.git
cd mcp-eplus-outputs
```

### Step 2: Install dependencies

```bash
uv sync
```

This installs Python 3.13+ and all required packages automatically.

### Step 3: Verify the server runs

```bash
uv run main.py
```

You should see the server start without errors. Press `Ctrl+C` to stop it.

### Step 4: Configure Claude Desktop

Open your Claude Desktop config file:

| OS      | Config file location                                                        |
|---------|-----------------------------------------------------------------------------|
| macOS   | `~/Library/Application Support/Claude/claude_desktop_config.json`           |
| Windows | `%APPDATA%\Claude\claude_desktop_config.json`                               |
| Linux   | `~/.config/Claude/claude_desktop_config.json`                               |

Add the MCP server entry (create the file if it doesn't exist). Replace the path with the **absolute path** to where you cloned the repo:

**macOS / Linux:**

```json
{
  "mcpServers": {
    "mcp_eplus_outputs": {
      "command": "uv",
      "args": ["--directory", "/Users/yourname/code/mcp-eplus-outputs", "run", "main.py"]
    }
  }
}
```

**Windows:**

```json
{
  "mcpServers": {
    "mcp_eplus_outputs": {
      "command": "uv",
      "args": ["--directory", "C:/Users/yourname/code/mcp-eplus-outputs", "run", "main.py"]
    }
  }
}
```

> **Note:** Use forward slashes (`/`) in the path, even on Windows.

### Step 5: Restart Claude Desktop

Quit and reopen Claude Desktop. The MCP server will appear in the tools menu (hammer icon). You can verify the connection by asking Claude:

> "Initialize the EnergyPlus model map and show me available models."

### Step 6: Point it at your simulation results

Tell Claude to scan any directory containing EnergyPlus output files (`.epJSON`, `.sql`, `.table.htm`) — this can be your simulation output directory directly, or a separate folder where you've copied files you want to analyze:

> "Initialize the model map with directory `path/to/my/simulation_outputs`"

The server will automatically discover and group files by directory and filename stem.

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

## Example Files

The `example-files/` directory contains sample EnergyPlus output files for testing and exploration. See `example-files/about.md` for provenance.

Included models:
- `ASHRAE901_HotelLarge_STD2013_Atlanta` — Large hotel, Atlanta climate
- `ASHRAE901_HotelLarge_STD2013_Buffalo` — Large hotel, Buffalo climate

Each includes `.epJSON`, `.sql`, and `.table.htm` files along with associated simulation outputs.

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

## Usage Examples

Once connected via Claude Desktop, here's a typical workflow using the MCP tools:

### 1. Initialize and discover models

```python
initialize_model_map(directory='example-files')
models = get_available_models()
```

### 2. Explore available data

```python
model_id = models[0]['model_id']

# Find cooling-related tables
search_html_tables_by_keyword(id=model_id, keywords=['cooling', 'sizing', 'capacity'])

# Get available timeseries variables
get_sql_available_hourlies(id=model_id)
```

### 3. Extract and analyze data

```python
# Get a specific HTML table
get_html_table_by_tuple(
    id=model_id,
    query_tuple=('Entire Facility', 'HVAC Sizing Summary', 'Zone Sensible Cooling')
)

# Analyze timeseries data with pandas
execute_multiline_pandas_on_timeseries(
    model_id=model_id,
    rddid=179,
    code='''
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

## Security & Code Quality

Security fixes applied in February 2026 include parameterized SQL queries, path traversal prevention, input validation, error disclosure hardening, and sandbox improvements. See `ai-docs/` for full audit reports.

### Known Issues for Future Versions

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

### Testing

Tests are in the `tests/` directory. Run with:

```bash
uv run pytest
```

See `tests/TESTING.md` for details on test coverage and structure.

## Support

For detailed usage instructions and examples, use:

```python
get_usage_instructions()
```

This returns the complete CLAUDE.md documentation file with comprehensive examples and best practices.
