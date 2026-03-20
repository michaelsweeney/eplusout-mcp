# Tool Consolidation & Dead Code Removal

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Cut the MCP server from 13 tools to 6, remove all dead code, drop the tiktoken dependency, and trim tool docstrings — reducing schema overhead per conversation by ~60%.

**Architecture:** The 6 surviving tools are the ones that provide capabilities Claude can't replicate with Read/Grep: SQL timeseries queries, HTML table parsing, and model discovery. Everything else (epJSON browsing, file reading, docs serving) is removed. Monitoring is simplified to character-count logging.

**Tech Stack:** Python 3.13, FastMCP, pandas, sqlite3, pytest

---

## File Map

| Action | File | Responsibility |
|--------|------|----------------|
| Modify | `src/server.py` | Remove 7 tools, trim docstrings, enhance `get_available_models` |
| Modify | `src/model_data.py` | Remove `SqlTables` import, remove `get_associated_files_by_type`, add file paths to `get_basic_attributes` |
| Modify | `src/monitor.py` | Remove tiktoken, `monitor_mcp_call`, `get_log_stats`, `clear_logs`; fix mutable default arg |
| Modify | `pyproject.toml` | Remove `tiktoken` dependency |
| Delete | `src/utils/helpers.py` | Dead code (never imported) |
| Delete | `src/utils/dtypes.py` | Dead code (never imported) |
| Delete | `src/utils/logger.py` | Dead code (entirely commented out) |
| Modify | `src/CLAUDE.md` | Update tool reference docs to match new tool set |
| Modify | `CLAUDE.md` | Update root project docs to reflect 6-tool server |
| Delete | `tests/test_epjson.py` | Tests for removed epJSON tools |
| Delete | `tests/test_utility_tools.py` | Tests for removed get_error_file/get_rdd_file |
| Modify | `tests/test_model_discovery.py` | Update `get_basic_attributes` test for new file_paths field |

---

### Task 1: Delete dead utility modules

**Files:**
- Delete: `src/utils/helpers.py`
- Delete: `src/utils/dtypes.py`
- Delete: `src/utils/logger.py`

- [ ] **Step 1: Verify no imports exist**

Run: `grep -r "from src.utils.helpers\|from src.utils.dtypes\|from src.utils.logger\|import helpers\|import dtypes" src/ tests/`
Expected: No output

- [ ] **Step 2: Delete the files**

```bash
rm src/utils/helpers.py src/utils/dtypes.py src/utils/logger.py
```

- [ ] **Step 3: Run tests to verify nothing breaks**

Run: `uv run pytest -v`
Expected: 34 passed

- [ ] **Step 4: Commit**

```bash
git add -A src/utils/
git commit -m "chore: remove dead utility modules (helpers.py, dtypes.py, logger.py)"
```

---

### Task 2: Simplify monitor.py and drop tiktoken

**Files:**
- Modify: `src/monitor.py`
- Modify: `pyproject.toml`

- [ ] **Step 1: Rewrite monitor.py**

Replace the entire file with a minimal version that uses character count instead of tiktoken. Note: fixes the mutable default argument bug (`kwargs: dict = {}` → `kwargs: dict | None = None`).

```python
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Any


def estimate_tokens(text: str) -> int:
    """Estimate token count using character-based heuristic (~4 chars per token)."""
    if not text:
        return 0
    return len(str(text)) // 4


def setup_logging() -> Path:
    """Set up the logging directory and return the log file path."""
    project_root = Path(__file__).parent.parent
    log_dir = project_root / 'monitor_logs'
    log_dir.mkdir(exist_ok=True)
    return log_dir / 'mcp_calls.log'


def log_mcp_call(
    function_name: str,
    result: Any,
    kwargs: dict | None = None,
    args: tuple = ()
) -> None:
    """Log MCP function call details to file."""
    if kwargs is None:
        kwargs = {}

    log_file = setup_logging()

    input_text = f"args: {args}, kwargs: {kwargs}"
    output_text = str(result) if result is not None else ""

    input_tokens = estimate_tokens(input_text)
    output_tokens = estimate_tokens(output_text)

    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "function_name": function_name,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
        "args_summary": str(args)[:200] + "..." if len(str(args)) > 200 else str(args),
        "kwargs_summary": str(kwargs)[:200] + "..." if len(str(kwargs)) > 200 else str(kwargs),
        "result_summary": str(result)[:200] + "..." if len(str(result)) > 200 else str(result)
    }

    try:
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry) + '\n')
    except Exception as e:
        logging.getLogger(__name__).error(f"Failed to write MCP log: {e}")
```

- [ ] **Step 2: Remove tiktoken from pyproject.toml**

In `pyproject.toml`, remove the line `"tiktoken>=0.9.0",` from the `dependencies` list.

- [ ] **Step 3: Sync dependencies**

Run: `uv sync`

- [ ] **Step 4: Run tests**

Run: `uv run pytest -v`
Expected: 34 passed

- [ ] **Step 5: Commit**

```bash
git add src/monitor.py pyproject.toml uv.lock
git commit -m "chore: drop tiktoken dependency, simplify monitor to char-count estimation"
```

---

### Task 3: Clean up model_data.py (SqlTables, get_associated_files_by_type)

**Files:**
- Modify: `src/model_data.py:12` — remove `SqlTables` from import
- Modify: `src/model_data.py:100-124` — simplify `SqlFileData`
- Modify: `src/model_data.py:191-219` — remove `get_associated_files_by_type`
- Delete: `tests/test_utility_tools.py` — tests for the removed method

- [ ] **Step 1: Edit the import**

At `src/model_data.py:12`, change:
```python
from src.tools.func_sql import SqlTimeseries, SqlTables
```
to:
```python
from src.tools.func_sql import SqlTimeseries
```

- [ ] **Step 2: Simplify SqlFileData**

Replace the `SqlFileData` class (lines 100-124) with:
```python
class SqlFileData(BaseModel):
    """Represents a SQL output file and provides access to timeseries data."""
    file_path: str
    sql_timeseries: SqlTimeseries | None = None

    def get_timeseries(self):
        if self.sql_timeseries is None:
            self.sql_timeseries = SqlTimeseries(sql_file=self.file_path)
        return self.sql_timeseries
```

- [ ] **Step 3: Remove get_associated_files_by_type method**

Delete the `get_associated_files_by_type` method from `ModelFileData` (lines 191-219). No tool calls it after the server consolidation.

- [ ] **Step 4: Delete test_utility_tools.py**

```bash
rm tests/test_utility_tools.py
```

- [ ] **Step 5: Run tests**

Run: `uv run pytest -v`
Expected: 30 passed (4 utility tests removed)

- [ ] **Step 6: Commit**

```bash
git add src/model_data.py tests/test_utility_tools.py
git commit -m "chore: remove unused SqlTables wiring and get_associated_files_by_type"
```

---

### Task 4: Add file paths to get_basic_attributes

**Files:**
- Modify: `src/model_data.py` — `get_basic_attributes` method
- Modify: `tests/test_model_discovery.py` — add new tests

This replaces the need for `get_error_file` / `get_rdd_file` tools — file paths are surfaced in model info so Claude can `Read` them directly.

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_model_discovery.py`:

```python
def test_get_basic_attributes_includes_file_paths(atlanta_model):
    attrs = atlanta_model.get_basic_attributes()
    assert "file_paths" in attrs
    assert "epjson" in attrs["file_paths"]
    assert "sql" in attrs["file_paths"]
    assert "html" in attrs["file_paths"]
    from pathlib import Path
    for path in attrs["file_paths"].values():
        assert Path(path).exists()


def test_get_basic_attributes_partial_files(atlanta_dd_model):
    """DD model has no epJSON — file_paths should only include sql and html."""
    attrs = atlanta_dd_model.get_basic_attributes()
    assert "epjson" not in attrs["file_paths"]
    assert "sql" in attrs["file_paths"]
    assert "html" in attrs["file_paths"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_model_discovery.py::test_get_basic_attributes_includes_file_paths tests/test_model_discovery.py::test_get_basic_attributes_partial_files -v`
Expected: FAIL with `KeyError: 'file_paths'`

- [ ] **Step 3: Update get_basic_attributes in model_data.py**

Replace the `get_basic_attributes` method:

```python
def get_basic_attributes(self):
    """Get basic model attributes for display."""
    file_types = []
    file_paths = {}
    if self.epjson_data:
        file_types.append('epjson')
        file_paths['epjson'] = self.epjson_data.file_path
    if self.sql_data:
        file_types.append('sql')
        file_paths['sql'] = self.sql_data.file_path
    if self.html_data:
        file_types.append('html')
        file_paths['html'] = self.html_data.file_path

    return {
        'model_id': self.model_id,
        'stem': self.stem,
        'file_types': file_types,
        'file_paths': file_paths,
    }
```

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/test_model_discovery.py -v`
Expected: All pass including 2 new tests

- [ ] **Step 5: Commit**

```bash
git add src/model_data.py tests/test_model_discovery.py
git commit -m "feat: include file paths in get_basic_attributes for direct file access"
```

---

### Task 5: Remove 7 tools from server.py

**Files:**
- Modify: `src/server.py` — remove tools, trim docstrings, remove dead state
- Delete: `tests/test_epjson.py` — tests for epJSON parsing (underlying func_epjson.py stays, just not exposed via MCP)

Tools to remove:
1. `get_usage_instructions` (lines 582-607)
2. `get_error_file` (lines 218-234)
3. `get_rdd_file` (lines 200-215)
4. `get_object_properties` (lines 372-417)
5. `list_objects_by_type` (lines 420-461)
6. `search_related_objects` (lines 464-510)
7. `search_epjson_objects` (lines 267-369)

Also removes dead state: `_current_directory`, `_get_current_directory`, `_set_current_directory`, `_validate_directory` — none are read by any surviving tool.

- [ ] **Step 1: Rewrite server.py**

Replace the entire file. The surviving tools are:
1. `initialize_model_map`
2. `get_available_models`
3. `search_html_tables_by_keyword` (trimmed docstring)
4. `get_html_table_by_tuple`
5. `get_sql_available_hourlies`
6. `get_timeseries_report_by_rddid_list`

```python
from pathlib import Path
import pandas as pd
import logging
import json

from typing import Any
from mcp.server.fastmcp import FastMCP
from src.monitor import log_mcp_call
from src.model_data import initialize_model_map_from_directory

logger = logging.getLogger(__name__)

mcp = FastMCP("eplus_outputs")

DEFAULT_DIRECTORY = 'example-files'
MAX_RESPONSE_CHARS = 10000


def _truncate_response(result, label: str = "result"):
    """Truncate a response if it exceeds MAX_RESPONSE_CHARS."""
    text = json.dumps(result, default=str) if not isinstance(result, str) else result

    if len(text) <= MAX_RESPONSE_CHARS:
        return result

    if isinstance(result, list):
        total = len(result)
        for i in range(total, 0, -1):
            subset = json.dumps(result[:i], default=str)
            if len(subset) <= MAX_RESPONSE_CHARS - 200:
                return {
                    "truncated": True,
                    "showing": i,
                    "total_rows": total,
                    "message": f"Response truncated: showing {i} of {total} rows. Request a more specific query to see all data.",
                    label: result[:i]
                }
        return {
            "truncated": True,
            "total_rows": total,
            "message": f"Response too large ({total} rows). Request a more specific query."
        }

    return {
        "truncated": True,
        "total_chars": len(text),
        "message": f"Response too large ({len(text)} chars). Request a more specific query."
    }


# Global state
_model_map = None


def _get_model_map():
    """Get the current model map, raising if not initialized."""
    if _model_map is None:
        raise ValueError(
            "Model map not initialized. Call initialize_model_map(directory) first."
        )
    return _model_map


@mcp.tool()
def initialize_model_map(directory: str = DEFAULT_DIRECTORY) -> str:
    """Scan a directory for EnergyPlus model files (.epJSON, .sql, .htm) and build a model catalog. Call this first."""

    global _model_map
    target_path = Path(directory).resolve()
    if not target_path.exists():
        raise ValueError(f"Directory does not exist: {target_path}")
    if not target_path.is_dir():
        raise ValueError(f"Path is not a directory: {target_path}")

    _model_map = initialize_model_map_from_directory(directory)
    model_count = len(_model_map.models)
    result = f"Model map initialized successfully for directory: {directory} ({model_count} models found)"
    log_mcp_call('initialize_model_map', result, kwargs={'directory': directory})
    return result


@mcp.tool()
def get_available_models() -> list:
    """List all discovered models with IDs, file types, and file paths for direct access."""

    model_map = _get_model_map()
    result = [x.get_basic_attributes() for x in model_map.models]
    log_mcp_call('get_available_models', result)
    return result


@mcp.tool()
def search_html_tables_by_keyword(id: str, keywords: str | list[str], case_sensitive: bool = False) -> dict:
    """Search for HTML report tables matching keywords in table/report names. Returns list of (report_for, report_name, table_name) tuples for use with get_html_table_by_tuple."""

    if isinstance(keywords, str):
        keywords = [keywords]

    model_map = _get_model_map()
    model = model_map.get_model_by_id(id)
    report_data = model.html_data.get_report_names()

    matching_tables = []

    if isinstance(report_data, list):
        for table_info in report_data:
            if isinstance(table_info, tuple):
                combined_text = ' '.join(str(field) for field in table_info)
                search_text = combined_text if case_sensitive else combined_text.lower()
                search_keywords = keywords if case_sensitive else [kw.lower() for kw in keywords]

                if any(keyword in search_text for keyword in search_keywords):
                    matching_tables.append(table_info)

    result = {
        "total_matches": len(matching_tables),
        "matching_tables": matching_tables,
    }

    log_mcp_call(
        'search_html_tables_by_keyword', result,
        kwargs={'id': id, 'keywords': keywords, 'case_sensitive': case_sensitive}
    )
    return result


@mcp.tool()
def get_html_table_by_tuple(id: str, query_tuple: tuple) -> list[dict]:
    """Retrieve a specific HTML table using a (report_for, report_name, table_name) tuple from search results."""

    model_map = _get_model_map()
    model = model_map.get_model_by_id(id)
    table = model.html_data.get_table_by_tuple(query_tuple, asjson=True)

    log_mcp_call(
        'get_html_table_by_tuple', table,
        kwargs={'id': id, 'query_tuple': query_tuple}
    )
    return _truncate_response(table, "rows")


@mcp.tool()
def get_sql_available_hourlies(id: str) -> list | dict:
    """List available hourly timeseries variables with RDD IDs for use with get_timeseries_report_by_rddid_list."""

    model_map = _get_model_map()
    model = model_map.get_model_by_id(id)
    result = model.sql_data.get_timeseries().availseries()

    log_mcp_call('get_sql_available_hourlies', result, kwargs={'id': id})
    return _truncate_response(result, "variables")


@mcp.tool()
def get_timeseries_report_by_rddid_list(model_id: str, rddid: int | list[int]) -> Any:
    """Extract hourly timeseries data by RDD ID(s). Returns columnar data with datetime index."""

    if isinstance(rddid, int):
        rddid = [rddid]

    model_map = _get_model_map()
    model = model_map.get_model_by_id(model_id)

    dflist = []
    for rdd in rddid:
        if not isinstance(rdd, int) or rdd <= 0:
            raise ValueError(f"Invalid RDD ID: {rdd}. Must be a positive integer.")
        r = model.sql_data.get_timeseries().getseries_by_record_id(rdd)
        tr = r[0]
        r_lbl = f'{tr["KeyValue"]}-{tr["Name"]}-{tr["TimestepType"]}-{tr["Units"]}'
        dfr = pd.DataFrame(r).set_index('dt')
        dfr = dfr.rename({"Value": r_lbl}, axis=1)
        dflist.append(dfr[r_lbl])

    dff = pd.concat(dflist, axis=1)
    split = dff.reset_index().to_dict(orient='split')
    result = {"columns": split["columns"], "data": split["data"]}

    log_mcp_call(
        'get_timeseries_report_by_rddid_list', f'{len(result)} records',
        kwargs={'model_id': model_id, 'rddid': rddid}
    )
    return _truncate_response(result, "records")
```

- [ ] **Step 2: Delete test file for removed epJSON tools**

```bash
rm tests/test_epjson.py
```

- [ ] **Step 3: Run tests**

Run: `uv run pytest -v`
Expected: 26 passed (6 epjson tests removed from 32 remaining after Task 3)

- [ ] **Step 4: Commit**

```bash
git add src/server.py tests/test_epjson.py
git commit -m "feat: consolidate from 13 to 6 MCP tools, remove epJSON/utility wrappers"
```

---

### Task 6: Update documentation

**Files:**
- Modify: `src/CLAUDE.md`
- Modify: `CLAUDE.md`

- [ ] **Step 1: Rewrite src/CLAUDE.md**

```markdown
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

## HTML Keyword Categories

**Energy**: `energy`, `consumption`, `end use`, `electricity`, `natural gas`, `annual`, `monthly`

**Cooling**: `cooling`, `coil`, `capacity`, `chiller`, `sensible cooling`, `peak cooling`

**Heating**: `heating`, `boiler`, `heat pump`, `heating coil`, `heat recovery`, `peak heating`

**HVAC**: `fan`, `pump`, `air loop`, `plant loop`, `zone equipment`, `terminal unit`, `vav`

**Envelope**: `window`, `wall`, `roof`, `floor`, `construction`, `infiltration`, `ventilation`

**Internal Loads**: `lighting`, `electric equipment`, `gas equipment`, `occupancy`, `schedule`
```

- [ ] **Step 2: Update root CLAUDE.md**

In `CLAUDE.md`, update the **MCP Server** section under `src/server.py` description to say:
`src/server.py` — FastMCP-based server exposing 6 tools to Claude (model management, HTML tables, SQL timeseries)

Remove references to epJSON tools from the "Tools cover..." sentence.

- [ ] **Step 3: Commit**

```bash
git add src/CLAUDE.md CLAUDE.md
git commit -m "docs: update tool reference for consolidated 6-tool server"
```

---

### Task 7: Clean up empty utils directory

**Files:**
- Delete: `src/utils/` directory (all files already removed in Task 1)

- [ ] **Step 1: Check what's left**

Run: `ls src/utils/`
Expected: Empty, or only `__init__.py`

- [ ] **Step 2: Delete the directory**

```bash
rm -rf src/utils/
```

- [ ] **Step 3: Verify no imports reference src.utils**

Run: `grep -r "from src.utils\|import src.utils" src/ tests/`
Expected: No output

- [ ] **Step 4: Run tests**

Run: `uv run pytest -v`
Expected: 26 passed

- [ ] **Step 5: Commit**

```bash
git add -A src/utils/
git commit -m "chore: remove empty utils directory"
```

---

### Task 8: Final verification

- [ ] **Step 1: Run full test suite**

Run: `uv run pytest -v`
Expected: 26 passed, 0 failed

- [ ] **Step 2: Start the server and verify it loads**

Run: `uv run python -c "from src.server import mcp; print([t.name for t in mcp._tool_manager._tools.values()])"`
Expected: List of exactly 6 tool names

- [ ] **Step 3: Verify no dead imports**

Run: `uv run python -c "import src.server; import src.model_data; import src.monitor; print('All imports clean')"`
Expected: `All imports clean`
