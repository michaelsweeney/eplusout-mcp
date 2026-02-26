# EnergyPlus MCP Server - Memory

## Fixed Issues

### Model Loading Failure (FIXED) ✅
**Problem**: `initialize_model_map()` returns success but `get_available_models()` returns empty results

**Root Cause**: Directory parameter was accepted but ignored by all tools except initialize_model_map()
- `initialize_model_map(directory)` scanned the given directory
- But `get_available_models()` and 11 other tools hardcoded `EPLUS_RUNS_DIRECTORY` instead of using the directory parameter
- Result: Models scanned from one directory, then queried from a different hardcoded directory

**Solution Implemented**: Global directory state management
- Added `_current_directory` module-level variable in src/server.py
- Added `_get_current_directory()` and `_set_current_directory()` functions
- `initialize_model_map()` now calls `_set_current_directory(directory)` after scanning
- All 12 tool functions now use `_get_current_directory()` instead of hardcoded EPLUS_RUNS_DIRECTORY
- Updated docstring for `get_available_models()` to clarify behavior

**Files Modified**: `src/server.py`
- Lines 19-33: Added state management functions
- Line 55: Added `_set_current_directory(directory)` call
- Lines 82, 106, 136, 155, 193, 233, 502, 627, 749, 821, 887, 954: Replaced EPLUS_RUNS_DIRECTORY with `_get_current_directory()`
- Lines 71-72: Updated docstring

## Project Architecture (from CLAUDE.md)

- **Model Discovery**: Filename-agnostic, groups by directory + filename stem
- **File Types**: .epJSON (input), .sql (results), .table.htm (summaries)
- **Caching**: ModelMap pickled to `mcp_cache/modelmap.pickle`
- **Key Files**:
  - `src/server.py` - MCP tools (15+)
  - `src/model_data.py` - Model discovery
  - `src/tools/func_sql.py`, `func_html.py` - File handlers

## Development Commands
```bash
uv sync              # Install dependencies (Python 3.13+)
uv run main.py       # Start MCP server
```
