# EnergyPlus MCP Server

A [Model Context Protocol](https://modelcontextprotocol.io/) (MCP) server that provides access to EnergyPlus building energy simulation results. Connect it to Claude (Desktop or Code) to discover, query, and analyze EnergyPlus output files using natural language.

## Key Features

- **Model Discovery**: Automatically scans directories for `.epJSON`, `.sql`, and `.htm` files, grouping them by filename stem
- **HTML Report Analysis**: Search and extract tabular data from EnergyPlus HTML summary reports
- **Timeseries Extraction**: Query hourly simulation data from SQL output databases
- **epJSON Exploration**: Search and inspect building model objects and properties
- **Pandas Integration**: Execute pandas queries directly on extracted data

## Quickstart

### Prerequisites

- [uv](https://docs.astral.sh/uv/getting-started/installation/) (Python package manager)
- [Claude Desktop](https://claude.ai/download) or [Claude Code](https://docs.anthropic.com/en/docs/claude-code)

### Install

```bash
git clone https://github.com/michaelsweeney/eplusout-mcp.git
cd eplusout-mcp
uv sync
```

### Configure Claude Desktop

Open your Claude Desktop config file:

| OS      | Config file location                                                        |
|---------|-----------------------------------------------------------------------------|
| macOS   | `~/Library/Application Support/Claude/claude_desktop_config.json`           |
| Windows | `%APPDATA%\Claude\claude_desktop_config.json`                               |
| Linux   | `~/.config/Claude/claude_desktop_config.json`                               |

Add the server entry (replace the path with your actual clone location):

```json
{
  "mcpServers": {
    "mcp_eplus_outputs": {
      "command": "uv",
      "args": ["--directory", "/path/to/eplusout-mcp", "run", "main.py"]
    }
  }
}
```

Restart Claude Desktop. The server will appear in the tools menu.

### Configure Claude Code

```bash
claude mcp add eplus_outputs -- uv --directory /path/to/eplusout-mcp run main.py
```

### Verify

Ask Claude:

> "Initialize the EnergyPlus model map with directory `example-files` and show me available models."

## File Structure

Each EnergyPlus model consists of three file types:

- **`.epJSON`** — Input model definition (geometry, materials, HVAC, schedules)
- **`.sql`** — Simulation results database (hourly timeseries, summary tables)
- **`.table.htm`** — HTML summary reports (tabular result summaries)

The server groups files by directory and filename stem. For example, `run1/eplusout.sql` and `run1/eplusout.epJSON` are treated as the same model with ID `run1/eplusout`.

## Available Tools

### Model Management
- `initialize_model_map()` — Scan a directory and build the model catalog
- `get_available_models()` — List all discovered models with metadata
- `get_usage_instructions()` — Get detailed usage documentation

### HTML Tables
- `search_html_tables_by_keyword()` — Find tables by keyword (e.g., `['cooling', 'sizing']`)
- `get_html_table_by_tuple()` — Retrieve a specific table by `(report_for, report_name, table_name)`
- `execute_pandas_on_html_table()` — Run a pandas expression on a table
- `execute_multiline_pandas_on_html_table()` — Run multi-line pandas code on a table

### Timeseries
- `get_sql_available_hourlies()` — List available hourly variables with RDD IDs
- `get_timeseries_report_by_rddid_list()` — Extract timeseries data by RDD ID
- `execute_pandas_on_timeseries()` — Run a pandas expression on timeseries data
- `execute_multiline_pandas_on_timeseries()` — Run multi-line pandas code on timeseries data

### epJSON
- `search_epjson_objects()` — Search building model objects by type, name, or pattern
- `get_object_properties()` — Get all properties of a specific object
- `list_objects_by_type()` — List all objects of a given EnergyPlus type
- `search_related_objects()` — Find objects related to a component or zone

### Debugging
- `get_error_file()` — Read the EnergyPlus error file for a model
- `get_rdd_file()` — Read the RDD (Report Data Dictionary) file

## Usage

A typical workflow:

```
1. initialize_model_map(directory='path/to/simulation_outputs')
2. get_available_models()                              → see what's available
3. search_html_tables_by_keyword(id=..., keywords=[...]) → find relevant tables
4. get_sql_available_hourlies(id=...)                  → find timeseries variables
5. execute_pandas_on_timeseries(model_id=..., rddid=..., query=...) → analyze
```

## Example Files

The `example-files/` directory contains sample EnergyPlus outputs for testing:

- `ASHRAE901_HotelLarge_STD2013_Atlanta` — Large hotel, Atlanta climate
- `ASHRAE901_HotelLarge_STD2013_Buffalo` — Large hotel, Buffalo climate

Each includes `.epJSON`, `.sql`, and `.table.htm` files. See `example-files/about.md` for provenance.

## Testing

```bash
uv run pytest
```

See `tests/TESTING.md` for coverage details.

## Known Issues

- `execute_pandas_on_*` and `execute_multiline_pandas_on_*` tools run user-provided code in a restricted `eval`/`exec` environment. The sandbox blocks common escape patterns but is not a full security boundary. Do not expose this server to untrusted users without additional sandboxing.

## Security

Security improvements applied include parameterized SQL queries, path traversal prevention, input validation, and error disclosure hardening. See `ai-docs/` for full audit reports.
