# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**EnergyPlus MCP Server** - A Model Context Protocol (MCP) server that provides comprehensive access to EnergyPlus building energy simulation results. The server enables users to:
- Discover and catalog EnergyPlus models (`.epJSON`, `.sql`, `.htm` files)
- Extract and analyze timeseries data from SQL databases
- Search and query HTML summary reports
- Explore building model objects and properties via epJSON files
- Execute pandas-based data analysis on results

The server is filename-agnostic and automatically discovers models by directory structure and filename stem.

## Development Setup

### Installation

```bash
# Install dependencies using uv (project uses Python 3.13+)
uv sync

# Verify Python version
python --version  # Should be 3.13+
```

### Running the Server

```bash
# Start the MCP server (uses stdio transport)
uv run main.py

# The server can be configured in Claude Desktop's config at ~/.claude/desktop/claude_desktop_config.json
```

## Architecture Overview

### Core Components

**Model Discovery & Caching** (`src/model_data.py`):
- `ModelMap` - Central class managing model catalog and metadata
- Automatically discovers models by scanning directories recursively
- Groups files by directory and filename stem (e.g., `models/run1/eplusout`)
- Caches model metadata in pickle format for fast access

**File Handlers**:
- `src/tools/func_sql.py` - SQLite database access for timeseries and tabular data
  - `SqlTimeseries` - Extracts hourly timeseries data by RDD ID
  - `SqlTables` - Extracts summary tables from SQL databases
- `src/tools/func_html.py` - HTML report parsing via BeautifulSoup
  - Extracts tabular data from HTML summary reports
  - Supports keyword-based table search
- `src/tools/func_epjson.py` - epJSON model file access
  - Reads and searches building component definitions

**Data Processing**:
- `src/dataloader.py` - Pandas integration for data queries
  - `execute_pandas_query()` - Single-line pandas expressions
  - `execute_multiline_pandas_query()` - Multi-line pandas code
  - Safe execution environment (restricted builtins)
  - Result formatting and truncation for token management

**MCP Server** (`src/server.py`):
- FastMCP-based server exposing tools to Claude
- 15+ tools covering model management, HTML analysis, timeseries extraction, epJSON exploration

**Monitoring & Logging** (`src/monitor.py`):
- Token counting via tiktoken
- Function call logging with input/output token tracking
- Logs stored in `monitor_logs/mcp_calls.log`

### Key Design Patterns

**Model ID Format**: `{relative_directory}/{filename_stem}`
- Example: `eplus_files/run1/eplusout`
- Allows multiple file types (.epJSON, .sql, .htm) to be grouped as one model

**Caching Strategy**:
- Model map cached in `mcp_cache/modelmap.pickle`
- Reduces repeated filesystem scans
- Expires and refreshes on initialization

**Safe Pandas Execution**:
- Restricted execution environment prevents dangerous operations
- Only allows specific builtins and pandas/numpy operations
- Useful for untrusted data analysis workflows

## Directory Structure

```
mcp-eplus-outputs/
├── main.py                      # Entry point - runs MCP server
├── README.md                    # User-facing documentation
├── pyproject.toml              # Project metadata and dependencies
├── uv.lock                     # Dependency lock file
│
├── src/                         # Main application code
│   ├── __init__.py             # Package initialization (cache paths)
│   ├── server.py               # MCP server definition (15+ tools)
│   ├── model_data.py           # Model discovery and caching
│   ├── dataloader.py           # Pandas query execution
│   ├── monitor.py              # Logging and token tracking
│   ├── CLAUDE.md               # User documentation (tool reference)
│   │
│   ├── tools/                  # File format handlers
│   │   ├── func_sql.py        # SQL database access
│   │   ├── func_html.py       # HTML report parsing
│   │   └── func_epjson.py     # epJSON model access
│   │
│   └── utils/                  # Utilities
│       ├── dtypes.py          # Data type definitions
│       ├── helpers.py         # Helper functions
│       └── logger.py          # Logging setup
│
├── schema/                      # Directory for result schema documentation
├── notebooks/                   # Jupyter notebooks for analysis
│
└── eplus_files/                # Example EnergyPlus model files (gitignored)
    └── prescriptive_variability_sample/
```

## Common Development Commands

### Testing

```bash
# There are currently no automated tests in the repo
# Manual testing involves:
# 1. Starting the server: uv run main.py
# 2. Using it via Claude Desktop or direct MCP client
```

### Code Structure Tips

- **Adding new tools**: Edit `src/server.py` and add `@mcp.tool()` decorated functions
- **Adding file format support**: Create new handler in `src/tools/` and integrate with `ModelMap` in `model_data.py`
- **Modifying data extraction**: Edit corresponding file handler (`func_sql.py`, `func_html.py`, `func_epjson.py`)
- **Changing logging behavior**: Modify `src/monitor.py` (token estimation) or `src/monitor.py` (logging)

### Dependencies

Key dependencies (see `pyproject.toml`):
- **fastmcp** - FastMCP server framework
- **pandas, numpy** - Data manipulation
- **bs4 (BeautifulSoup)** - HTML parsing
- **lxml** - XML/HTML processing
- **tiktoken** - Token counting for monitoring
- **pyarrow** - Arrow data format support
- **sqlite3** (built-in) - Database access

### Key Files to Understand

1. **`src/server.py`** (31KB) - Read first to understand available tools
2. **`src/model_data.py`** (23KB) - Understand model discovery and caching
3. **`src/tools/func_sql.py`** (17KB) - SQL data extraction patterns
4. **`src/tools/func_html.py`** (8KB) - HTML parsing approach
5. **`src/dataloader.py`** (8KB) - Pandas integration and result formatting

## Key Concepts

### Model Discovery (Filename-Agnostic)

The server works with ANY filename pattern. Models are identified by:
- **Directory structure** - Where files are located
- **Filename stem** - Filename without extension

Examples:
- `eplus_files/run1/model.epJSON` + `eplus_files/run1/model.sql` → model ID: `eplus_files/run1/model`
- `data/ASHRAE901_HotelLarge_STD2025_Buffalo_gshp.epJSON` → model ID: `data/ASHRAE901_HotelLarge_STD2025_Buffalo_gshp`

### Model File Types

Each EnergyPlus model may contain three file types:
- **`.epJSON`** - Building input definition (geometry, materials, HVAC systems, schedules)
- **`.sql`** - Simulation results database (timeseries data, summary tables)
- **`.table.htm`** - HTML summary reports (tabular performance summaries)

### RDD ID

Report Data Dictionary (RDD) ID - Unique identifier for timeseries variables in the SQL database. Used to extract specific hourly data like "Facility Total Electric Demand Power".

## Deployment & Configuration

### Claude Desktop Integration

Add to `~/.claude/desktop/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "mcp_eplus_outputs": {
      "command": "uv",
      "args": ["--directory", "/path/to/mcp-eplus-outputs", "run", "main.py"]
    }
  }
}
```

### Cache Management

- **Location**: `mcp_cache/modelmap.pickle`
- **Refresh**: Call `initialize_model_map()` to rescan and refresh
- **Size**: Small (pickled model metadata only, not data files)

## Performance Considerations

- **Model caching**: Initial `initialize_model_map()` scans filesystem; subsequent calls use cache
- **Result truncation**: Large datasets automatically truncated to prevent token overflow (see `dataloader.py:_format_result()`)
- **Token tracking**: All calls logged for monitoring (useful for budget management)
- **HTML parsing**: Tables parsed on-demand when accessed

## Notes for Future Developers

- The server is designed for read-only access to simulation results (no modifications to EnergyPlus files)
- All user code execution (pandas queries) happens in a restricted, safe environment
- The project was recently cleaned up (see `CLEANUP_SUMMARY.txt`) - extraneous analysis scripts were removed
- The existing `src/CLAUDE.md` is user-facing documentation for MCP tool usage, not developer docs
