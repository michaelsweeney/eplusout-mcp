# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**EnergyPlus MCP Server** — An MCP server for accessing EnergyPlus building energy simulation results. The server enables users to:
- Discover and catalog EnergyPlus models (`.epJSON`, `.sql`, `.htm` files)
- Extract timeseries data from SQL databases
- Search and query HTML summary reports
- Explore building model objects and properties via epJSON files

The server is filename-agnostic and automatically discovers models by directory structure and filename stem.

## Development Setup

### Installation

```bash
uv sync
```

### Running the Server

```bash
uv run main.py
```

See README.md for MCP client configuration.

## Architecture Overview

### Core Components

**Model Discovery** (`src/model_data.py`):
- `ModelMap` — Central class managing model catalog and metadata
- Discovers models by scanning directories recursively
- Groups files by directory and filename stem (e.g., `models/run1/eplusout`)

**File Handlers**:
- `src/tools/func_sql.py` — SQLite database access for timeseries and tabular data
  - `SqlTimeseries` — Extracts hourly timeseries data by RDD ID
  - `SqlTables` — Extracts summary tables from SQL databases
- `src/tools/func_html.py` — HTML report parsing
  - Extracts tabular data from HTML summary reports
  - Supports keyword-based table search
- `src/tools/func_epjson.py` — epJSON model file access
  - Reads and searches building component definitions

**MCP Server** (`src/server.py`):
- FastMCP-based server exposing 6 tools via MCP
- Tools cover model management, HTML analysis, and timeseries extraction

**Monitoring & Logging** (`src/monitor.py`):
- Function call logging with input/output token estimation
- Logs stored in `monitor_logs/mcp_calls.log`

### Key Design Patterns

**Model ID Format**: `{relative_directory}/{filename_stem}`
- Example: `eplus_files/run1/eplusout`
- Allows multiple file types (.epJSON, .sql, .htm) to be grouped as one model

## Directory Structure

```
eplusout-mcp/
├── main.py                      # Entry point
├── README.md                    # User-facing documentation
├── pyproject.toml               # Project metadata and dependencies
├── uv.lock                      # Dependency lock file
│
├── src/                         # Main application code
│   ├── __init__.py              # Package initialization
│   ├── server.py                # MCP server definition (tools)
│   ├── model_data.py            # Model discovery
│   ├── monitor.py               # Logging and token tracking
│   ├── CLAUDE.md                # User-facing tool documentation for LLM consumers of the MCP server
│   │
│   ├── tools/                   # File format handlers
│   │   ├── func_sql.py          # SQL database access
│   │   ├── func_html.py         # HTML report parsing
│   │   └── func_epjson.py       # epJSON model access
│
├── tests/                       # Pytest test suite
├── example-files/               # Sample EnergyPlus models for testing
├── ai-docs/                     # AI-generated analysis and audit docs
├── schema/                      # EnergyPlus JSON schema
└── notebooks/                   # Jupyter notebooks for exploration
```

## Common Development Commands

### Testing

```bash
uv run pytest
uv run pytest tests/test_sql_timeseries.py
```

### Code Structure Tips

- **Adding new tools**: Edit `src/server.py` and add `@mcp.tool()` decorated functions
- **Adding file format support**: Create new handler in `src/tools/` and integrate with `ModelMap` in `model_data.py`
- **Modifying data extraction**: Edit corresponding file handler (`func_sql.py`, `func_html.py`, `func_epjson.py`)

### Dependencies

Key dependencies (see `pyproject.toml`):
- **fastmcp** — MCP server framework
- **pandas, numpy** — Data manipulation
- **sqlite3** (built-in) — Database access

## Key Concepts

### RDD ID

Report Data Dictionary (RDD) ID — Unique identifier for timeseries variables in the SQL database. Used to extract specific hourly data like "Facility Total Electric Demand Power".

## Notes for Future Developers

- The server is read-only — it does not modify EnergyPlus files
- `src/CLAUDE.md` is user-facing tool documentation for LLM consumers of the MCP server, not developer docs
