# EnergyPlus MCP Server Instructions

## Available Tools

### Setup
- `initialize_model_map(directory)` — Scan a directory for EnergyPlus files. **Call this first.**
- `get_available_models()` — List all discovered models with IDs, file types, and file paths

### HTML Tables
- `search_html_tables_by_keyword(id, keywords)` — Find tables by keyword
- `get_html_table_by_tuple(id, query_tuple)` — Get a specific table by `(report_for, report_name, table_name)`

### Timeseries
- `get_sql_available_hourlies(id)` — List available hourly variables with RDD IDs
- `get_timeseries_report_by_rddid_list(model_id, rddid)` — Extract timeseries data by RDD ID(s)

## Workflow

1. `initialize_model_map(directory)` — scan for models
2. `get_available_models()` — get model IDs and file paths
3. Use HTML/timeseries tools with a model ID
4. For epJSON or error files, use the file paths from step 2 to read files directly

## Model Discovery

Files are grouped by **directory + filename stem**:
- `run1/eplusout.sql` + `run1/eplusout.epJSON` → model ID `run1/eplusout`

## File Types

- **`.epJSON`** — Input model definition (read directly via file path)
- **`.sql`** — SQLite results database (accessed via timeseries tools)
- **`.table.htm`** — HTML summary reports (accessed via HTML tools)
- **`.err`** / **`.rdd`** — Error and report data dictionary files (read directly via file path)

## EnergyPlus Reference Documentation

The official EnergyPlus Input/Output Reference is hosted by Big Ladder Software:

- **Docs index**: `https://bigladdersoftware.com/epx/docs/`
- **I/O Reference (v24.1)**: `https://bigladdersoftware.com/epx/docs/24-1/input-output-reference/`
- **Engineering Reference (v24.1)**: `https://bigladdersoftware.com/epx/docs/24-1/engineering-reference/`

**URL pattern**: `https://bigladdersoftware.com/epx/docs/{major}-{minor}/input-output-reference/`

Replace `{major}-{minor}` with the EnergyPlus version (e.g., `25-2`, `24-1`, `23-2`, `9-6`). Available versions: 8.0 through 25.2.

**Object documentation** is organized by group pages:
- `group-coils.html` — Coil objects
- `group-hvac-templates.html` — HVAC template objects
- `group-surface-construction-elements.html` — Construction/material objects
- `group-thermal-zones-and-surfaces.html` — Zone and surface objects

To look up a specific EnergyPlus object type, use `WebFetch` on the appropriate group page URL.

## HTML Keyword Categories

**Energy**: `energy`, `consumption`, `end use`, `electricity`, `natural gas`, `annual`, `monthly`

**Cooling**: `cooling`, `coil`, `capacity`, `chiller`, `sensible cooling`, `peak cooling`

**Heating**: `heating`, `boiler`, `heat pump`, `heating coil`, `heat recovery`, `peak heating`

**HVAC**: `fan`, `pump`, `air loop`, `plant loop`, `zone equipment`, `terminal unit`, `vav`

**Envelope**: `window`, `wall`, `roof`, `floor`, `construction`, `infiltration`, `ventilation`

**Internal Loads**: `lighting`, `electric equipment`, `gas equipment`, `occupancy`, `schedule`
