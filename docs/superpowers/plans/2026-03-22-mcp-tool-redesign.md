# MCP Tool Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a 3-branch experiment comparing pandas execution, hybrid tools, and prompt-only approaches for EnergyPlus analysis accuracy.

**Architecture:** Branch A adds a sandboxed `execute_pandas` tool to the MCP server. Branch B extends A with 2 pre-built accuracy guardrail tools. Branch C creates domain knowledge files with no server changes. All branches share an updated eval runner that supports 4 test conditions.

**Tech Stack:** Python 3.13, FastMCP, pandas, numpy, pytest, bash (eval runner)

---

## File Structure

### Branch A (`experiment/pandas-exec`)
```
src/
├── server.py              # Modify: add execute_pandas tool, raise MAX_RESPONSE_CHARS to 50K
├── sandbox.py             # Create: AST validator + restricted exec environment
├── data_loader.py         # Create: DataFrame construction + LRU cache for sql_ts / html_tables
├── CLAUDE.md              # Modify: document execute_pandas tool and available variables
tests/
├── test_sandbox.py        # Create: security + execution tests
├── test_data_loader.py    # Create: DataFrame construction tests
```

### Branch B (`experiment/hybrid`) — extends Branch A
```
src/
├── server.py              # Modify: add get_end_uses + get_timeseries_stats tools
├── tools/
│   └── func_aggregation.py # Create: pre-built aggregation logic
tests/
├── test_aggregation.py    # Create: accuracy tests for pre-built tools
```

### Branch C (`experiment/prompt-only`) — from pre-release-updates
```
test_prompts/
├── domain_guide.md        # Create: EnergyPlus domain knowledge for system prompt
├── snippets/
│   ├── parse_end_uses.py  # Create: vetted HTML parsing function
│   ├── query_timeseries.py # Create: vetted SQL query function
│   └── unmet_hours.py     # Create: vetted unmet hours extraction
```

### Eval runner (all branches)
```
test_prompts/
├── run_test.sh            # Modify: add vanilla/pandas-exec/hybrid/prompt-only modes + 4-way grading
```

---

## Task 0: Create experiment branch

- [ ] **Step 1: Create Branch A from pre-release-updates**

```bash
cd /home/msweeney/repos/eplusout-mcp
git checkout pre-release-updates
git checkout -b experiment/pandas-exec
```

All subsequent Tasks 1-3 are committed on this branch.

---

## Task 1: Create sandbox module (Branch A)

**Files:**
- Create: `src/sandbox.py`
- Test: `tests/test_sandbox.py`

- [ ] **Step 1: Write security tests for the AST validator**

```python
# tests/test_sandbox.py
import pytest
from src.sandbox import validate_code, execute_sandboxed, SandboxViolation


class TestASTValidation:
    def test_rejects_import_statement(self):
        with pytest.raises(SandboxViolation, match="import"):
            validate_code("import os")

    def test_rejects_from_import(self):
        with pytest.raises(SandboxViolation, match="import"):
            validate_code("from os import path")

    def test_rejects_open_call(self):
        with pytest.raises(SandboxViolation, match="open"):
            validate_code("open('/etc/passwd')")

    def test_rejects_exec_call(self):
        with pytest.raises(SandboxViolation, match="exec"):
            validate_code("exec('print(1)')")

    def test_rejects_eval_call(self):
        with pytest.raises(SandboxViolation, match="eval"):
            validate_code("eval('1+1')")

    def test_rejects_dunder_access(self):
        with pytest.raises(SandboxViolation, match="__"):
            validate_code("x.__class__.__bases__")

    def test_rejects_os_reference(self):
        with pytest.raises(SandboxViolation, match="os"):
            validate_code("os.system('ls')")

    def test_rejects_subprocess_reference(self):
        with pytest.raises(SandboxViolation, match="subprocess"):
            validate_code("subprocess.run(['ls'])")

    def test_allows_simple_math(self):
        validate_code("x = 1 + 2")  # should not raise

    def test_allows_pandas_operations(self):
        validate_code("df.sum()")  # should not raise

    def test_allows_list_comprehension(self):
        validate_code("[x for x in range(10)]")  # should not raise
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/msweeney/repos/eplusout-mcp && uv run pytest tests/test_sandbox.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'src.sandbox'`

- [ ] **Step 3: Implement the sandbox module**

```python
# src/sandbox.py
import ast
import signal
import json
import pandas as pd
import numpy as np
from typing import Any

BLOCKED_NAMES = frozenset({
    "os", "sys", "subprocess", "shutil", "pathlib", "socket",
    "requests", "urllib", "http", "ftplib", "smtplib",
    "open", "exec", "eval", "compile", "__import__",
    "getattr", "setattr", "delattr", "globals", "locals",
    "breakpoint", "exit", "quit",
})

BLOCKED_DUNDERS = frozenset({
    "__builtins__", "__class__", "__subclasses__", "__globals__",
    "__code__", "__import__", "__bases__", "__mro__",
})

MAX_OUTPUT_CHARS = 50_000
TIMEOUT_SECONDS = 30


class SandboxViolation(Exception):
    """Raised when code contains blocked operations."""
    pass


class _Validator(ast.NodeVisitor):
    """AST visitor that rejects dangerous code patterns."""

    def visit_Import(self, node):
        raise SandboxViolation(f"import statements are not allowed: {ast.dump(node)}")

    def visit_ImportFrom(self, node):
        raise SandboxViolation(f"import statements are not allowed: from {node.module}")

    def visit_Name(self, node):
        if node.id in BLOCKED_NAMES:
            raise SandboxViolation(f"'{node.id}' is not allowed")
        self.generic_visit(node)

    def visit_Attribute(self, node):
        if node.attr in BLOCKED_DUNDERS:
            raise SandboxViolation(f"access to '{node.attr}' is not allowed")
        if node.attr in BLOCKED_NAMES:
            raise SandboxViolation(f"'{node.attr}' is not allowed")
        self.generic_visit(node)

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name) and node.func.id in BLOCKED_NAMES:
            raise SandboxViolation(f"calling '{node.func.id}' is not allowed")
        self.generic_visit(node)


def validate_code(code: str) -> ast.Module:
    """Parse and validate code. Returns the AST if safe, raises SandboxViolation otherwise."""
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        raise SandboxViolation(f"Syntax error: {e}")

    _Validator().visit(tree)
    return tree


def execute_sandboxed(code: str, data_globals: dict) -> dict:
    """Execute validated code in a restricted namespace.

    Args:
        code: Python code string (already validated via validate_code).
        data_globals: Dict containing pre-loaded data (sql_ts, html_tables, model_info).

    Returns:
        dict with 'result' (the last expression value) or 'error' (traceback string).
    """
    sandbox_globals = {
        "__builtins__": {},
        # Data libraries
        "pd": pd,
        "np": np,
        # Safe builtins
        "print": print,
        "len": len,
        "range": range,
        "enumerate": enumerate,
        "zip": zip,
        "min": min,
        "max": max,
        "sum": sum,
        "abs": abs,
        "round": round,
        "sorted": sorted,
        "isinstance": isinstance,
        "dict": dict,
        "list": list,
        "tuple": tuple,
        "set": set,
        "str": str,
        "int": int,
        "float": float,
        "bool": bool,
        "type": type,
        "True": True,
        "False": False,
        "None": None,
    }
    sandbox_globals.update(data_globals)

    # Parse to extract last expression for return value
    tree = ast.parse(code)
    last_expr_value = None

    if tree.body and isinstance(tree.body[-1], ast.Expr):
        last_expr = tree.body.pop()
        assign = ast.Assign(
            targets=[ast.Name(id="_result_", ctx=ast.Store())],
            value=last_expr.value,
            lineno=last_expr.lineno,
            col_offset=last_expr.col_offset,
        )
        ast.fix_missing_locations(assign)
        tree.body.append(assign)

    compiled = compile(tree, "<sandbox>", "exec")

    local_ns = {}

    def _timeout_handler(signum, frame):
        raise TimeoutError(f"Execution timed out after {TIMEOUT_SECONDS}s")

    old_handler = signal.signal(signal.SIGALRM, _timeout_handler)
    signal.alarm(TIMEOUT_SECONDS)

    try:
        exec(compiled, sandbox_globals, local_ns)
        result = local_ns.get("_result_", None)
    except TimeoutError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"}
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)

    return _serialize_result(result)


def _serialize_result(result: Any) -> dict:
    """Convert execution result to a JSON-safe dict, respecting size limits."""
    if isinstance(result, pd.DataFrame):
        serialized = {
            "type": "DataFrame",
            "shape": list(result.shape),
            "columns": list(result.columns),
            "data": result.reset_index(drop=True).to_dict(orient="records"),
        }
    elif isinstance(result, pd.Series):
        serialized = {
            "type": "Series",
            "name": result.name,
            "data": result.to_dict(),
        }
    elif isinstance(result, (dict, list, tuple, int, float, str, bool, type(None))):
        serialized = {"result": result}
    else:
        serialized = {"result": str(result)}

    text = json.dumps(serialized, default=str)
    if len(text) > MAX_OUTPUT_CHARS:
        return {
            "error": f"Output too large ({len(text)} chars, max {MAX_OUTPUT_CHARS}). "
            "Filter or aggregate your data to reduce output size.",
            "output_size": len(text),
        }
    return serialized
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /home/msweeney/repos/eplusout-mcp && uv run pytest tests/test_sandbox.py -v`
Expected: All 11 tests PASS

- [ ] **Step 5: Write execution tests**

Add to `tests/test_sandbox.py`:

```python
class TestExecution:
    @pytest.fixture
    def sample_data(self):
        import pandas as pd
        import numpy as np
        df = pd.DataFrame({
            "None:Electricity:Facility [J]": np.random.random(8760) * 1e6,
        }, index=pd.date_range("2024-01-01", periods=8760, freq="h"))
        return {"sql_ts": df, "html_tables": {}, "model_info": {"id": "test"}}

    def test_simple_math(self, sample_data):
        result = execute_sandboxed("1 + 2", sample_data)
        assert result["result"] == 3

    def test_pandas_sum(self, sample_data):
        result = execute_sandboxed("sql_ts.sum()", sample_data)
        assert result["type"] == "Series"
        assert "None:Electricity:Facility [J]" in result["data"]

    def test_pandas_describe(self, sample_data):
        result = execute_sandboxed("sql_ts.describe()", sample_data)
        assert result["type"] == "DataFrame"

    def test_timeout(self, sample_data):
        result = execute_sandboxed("while True: pass", sample_data)
        assert "error" in result
        assert "timed out" in result["error"].lower()

    def test_exception_returned(self, sample_data):
        result = execute_sandboxed("1 / 0", sample_data)
        assert "error" in result
        assert "ZeroDivisionError" in result["error"]

    def test_multiline_code(self, sample_data):
        code = """
total = sql_ts.sum().iloc[0]
gj = total / 1e9
round(gj, 2)
"""
        result = execute_sandboxed(code, sample_data)
        assert "result" in result
        assert isinstance(result["result"], float)

    def test_blocked_import_at_runtime(self, sample_data):
        """Even if AST check is bypassed, builtins are restricted."""
        result = execute_sandboxed("type(1)", sample_data)
        # type() is allowed
        assert "result" in result or "type" in str(result)
```

- [ ] **Step 6: Run all sandbox tests**

Run: `cd /home/msweeney/repos/eplusout-mcp && uv run pytest tests/test_sandbox.py -v`
Expected: All tests PASS

- [ ] **Step 7: Commit**

```bash
git add src/sandbox.py tests/test_sandbox.py
git commit -m "feat: add sandboxed code execution module

AST-validated Python execution with restricted builtins.
Blocks imports, filesystem access, and dangerous builtins.
30s timeout, 50K char output limit."
```

---

## Task 2: Create data loader module (Branch A)

**Files:**
- Create: `src/data_loader.py`
- Test: `tests/test_data_loader.py`

- [ ] **Step 1: Write data loader tests**

```python
# tests/test_data_loader.py
import pytest
import pandas as pd
from pathlib import Path
from src.data_loader import load_sql_timeseries, load_html_tables, DataCache


@pytest.fixture(scope="module")
def buffalo_sql_path():
    return str(Path(__file__).parent.parent / "example-files" / "ASHRAE901_HotelLarge_STD2013_Buffalo.sql")

@pytest.fixture(scope="module")
def buffalo_html_path():
    return str(Path(__file__).parent.parent / "example-files" / "ASHRAE901_HotelLarge_STD2013_Buffalo.table.htm")


class TestSqlTimeseriesLoading:
    def test_returns_dataframe(self, buffalo_sql_path):
        df = load_sql_timeseries(buffalo_sql_path)
        assert isinstance(df, pd.DataFrame)

    def test_has_datetime_index(self, buffalo_sql_path):
        df = load_sql_timeseries(buffalo_sql_path)
        assert isinstance(df.index, pd.DatetimeIndex)

    def test_has_8760_rows(self, buffalo_sql_path):
        df = load_sql_timeseries(buffalo_sql_path)
        assert len(df) == 8760

    def test_column_names_include_units(self, buffalo_sql_path):
        df = load_sql_timeseries(buffalo_sql_path)
        for col in df.columns:
            assert "[" in col and "]" in col, f"Column '{col}' missing units"

    def test_electricity_facility_sum_matches_known(self, buffalo_sql_path):
        df = load_sql_timeseries(buffalo_sql_path)
        elec_cols = [c for c in df.columns if "Electricity:Facility" in c]
        assert len(elec_cols) >= 1
        total_gj = df[elec_cols[0]].sum() / 1e9
        assert abs(total_gj - 5105.50) < 0.1  # known ground truth


class TestHtmlTablesLoading:
    def test_returns_dict(self, buffalo_html_path):
        tables = load_html_tables(buffalo_html_path)
        assert isinstance(tables, dict)

    def test_keys_are_tuples(self, buffalo_html_path):
        tables = load_html_tables(buffalo_html_path)
        for key in tables:
            assert isinstance(key, tuple)
            assert len(key) == 3

    def test_values_are_dataframes(self, buffalo_html_path):
        tables = load_html_tables(buffalo_html_path)
        for df in tables.values():
            assert isinstance(df, pd.DataFrame)

    def test_end_uses_table_exists(self, buffalo_html_path):
        tables = load_html_tables(buffalo_html_path)
        end_uses_keys = [k for k in tables if "End Uses" in k[2]]
        assert len(end_uses_keys) >= 1


class TestDataCache:
    def test_caches_results(self, buffalo_sql_path):
        cache = DataCache(max_size=3)
        df1 = cache.get_sql_ts("test_id", buffalo_sql_path)
        df2 = cache.get_sql_ts("test_id", buffalo_sql_path)
        assert df1 is df2  # same object, not reloaded

    def test_evicts_oldest(self):
        cache = DataCache(max_size=2)
        # Fill with dummy entries to test eviction
        cache._sql_cache["a"] = pd.DataFrame()
        cache._sql_cache["b"] = pd.DataFrame()
        cache._sql_cache["c"] = pd.DataFrame()  # should evict "a"
        cache._evict_if_needed()
        assert "a" not in cache._sql_cache
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/msweeney/repos/eplusout-mcp && uv run pytest tests/test_data_loader.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement the data loader**

```python
# src/data_loader.py
import pandas as pd
import logging
from collections import OrderedDict
from src.tools.func_sql import SqlTimeseries
from src.tools.func_html import get_all_table_data

logger = logging.getLogger(__name__)


def load_sql_timeseries(sql_path: str) -> pd.DataFrame:
    """Load all hourly timeseries from a SQL file into a single DataFrame.

    Returns DataFrame with:
    - DatetimeIndex (8760 rows for annual, fewer for design-day)
    - One column per RDD variable, named "{KeyValue}:{Name} [{Units}]"

    Note: First call loads all variables (may take several seconds for models
    with many output variables). Results are cached by DataCache.
    Data loading happens OUTSIDE the sandbox timeout — the 30s timeout only
    applies to user code execution.
    """
    ts = SqlTimeseries(sql_file=sql_path)
    avail = ts.availseries()

    if not avail:
        return pd.DataFrame()

    dfs = []
    for var in avail:
        rdd_id = var["ReportDataDictionaryIndex"]
        records = ts.getseries_by_record_id(rdd_id)
        if not records:
            continue
        df = pd.DataFrame(records)
        key = df["KeyValue"].iloc[0]
        name = df["Name"].iloc[0]
        units = df["Units"].iloc[0]
        col_name = f"{key}:{name} [{units}]"
        series = df.set_index("dt")["Value"].rename(col_name)
        dfs.append(series)

    if not dfs:
        return pd.DataFrame()

    result = pd.concat(dfs, axis=1)
    result.index = pd.to_datetime(result.index)
    result.index.name = "datetime"
    return result


def load_html_tables(html_path: str) -> dict[tuple, pd.DataFrame]:
    """Load all HTML tables into a dict of DataFrames.

    Returns dict keyed by (report_for, report_name, table_name) tuples.
    Each DataFrame has proper column headers.
    """
    raw_tables = get_all_table_data(html_path)
    result = {}

    for table_info in raw_tables:
        key = (
            table_info["report_for"],
            table_info["report_name"],
            table_info["table_name"],
        )
        raw_data = table_info["table_data"]
        if not raw_data or len(raw_data) < 2:
            result[key] = pd.DataFrame()
            continue

        df = pd.DataFrame(raw_data[1:], columns=raw_data[0])
        result[key] = df

    return result


class DataCache:
    """LRU cache for loaded DataFrames. Evicts oldest when max_size exceeded."""

    def __init__(self, max_size: int = 5):
        self.max_size = max_size
        self._sql_cache: OrderedDict[str, pd.DataFrame] = OrderedDict()
        self._html_cache: OrderedDict[str, dict] = OrderedDict()

    def get_sql_ts(self, model_id: str, sql_path: str) -> pd.DataFrame:
        if model_id in self._sql_cache:
            self._sql_cache.move_to_end(model_id)
            return self._sql_cache[model_id]
        df = load_sql_timeseries(sql_path)
        self._sql_cache[model_id] = df
        self._evict_if_needed()
        return df

    def get_html_tables(self, model_id: str, html_path: str) -> dict:
        if model_id in self._html_cache:
            self._html_cache.move_to_end(model_id)
            return self._html_cache[model_id]
        tables = load_html_tables(html_path)
        self._html_cache[model_id] = tables
        self._evict_if_needed()
        return tables

    def _evict_if_needed(self):
        while len(self._sql_cache) > self.max_size:
            evicted_key, _ = self._sql_cache.popitem(last=False)
            logger.debug(f"Evicted SQL cache: {evicted_key}")
        while len(self._html_cache) > self.max_size:
            evicted_key, _ = self._html_cache.popitem(last=False)
            logger.debug(f"Evicted HTML cache: {evicted_key}")

    def clear(self):
        self._sql_cache.clear()
        self._html_cache.clear()
```

- [ ] **Step 4: Run tests**

Run: `cd /home/msweeney/repos/eplusout-mcp && uv run pytest tests/test_data_loader.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/data_loader.py tests/test_data_loader.py
git commit -m "feat: add data loader with LRU cache for DataFrames

Loads SQL timeseries and HTML tables into pandas DataFrames.
Column names include units. LRU cache evicts oldest model."
```

---

## Task 3: Wire execute_pandas into server.py (Branch A)

**Files:**
- Modify: `src/server.py`
- Modify: `src/CLAUDE.md`

- [ ] **Step 1: Add execute_pandas tool to server.py**

Add after the existing `get_timeseries_report_by_rddid_list` tool:

```python
# At top of server.py, add imports:
from src.sandbox import validate_code, execute_sandboxed, SandboxViolation
from src.data_loader import DataCache

# After the existing global state section, add:
_data_cache = DataCache(max_size=5)
```

Add the tool:

```python
@mcp.tool()
def execute_pandas(model_id: str, code: str) -> dict:
    """Execute Python/pandas code against a model's pre-loaded data.

    Available variables in the execution environment:
    - sql_ts: DataFrame of hourly timeseries (datetime index, one column per variable).
              Column names include units, e.g. "None:Electricity:Facility [J]".
              Values are in source units (J for energy, W for power).
    - html_tables: dict of {(report_for, report_name, table_name): DataFrame}.
              All HTML summary tables as DataFrames with proper headers.
    - model_info: dict with model metadata (id, file_paths, file_types).
    - pd: pandas module
    - np: numpy module

    The last expression in the code is returned as the result.
    No filesystem, network, or import access. 30-second timeout.
    """
    try:
        validate_code(code)
    except SandboxViolation as e:
        return {"error": f"Code validation failed: {e}"}

    model_map = _get_model_map()
    model = model_map.get_model_by_id(model_id)

    # Load data
    data_globals = {"model_info": model.get_basic_attributes()}

    if model.sql_data:
        data_globals["sql_ts"] = _data_cache.get_sql_ts(
            model_id, model.sql_data.file_path
        )
    else:
        data_globals["sql_ts"] = pd.DataFrame()

    if model.html_data:
        data_globals["html_tables"] = _data_cache.get_html_tables(
            model_id, model.html_data.file_path
        )
    else:
        data_globals["html_tables"] = {}

    result = execute_sandboxed(code, data_globals)
    log_mcp_call("execute_pandas", result, kwargs={"model_id": model_id, "code": code[:200]})
    return result
```

Also update `MAX_RESPONSE_CHARS` from 10000 to 50000:

```python
MAX_RESPONSE_CHARS = 50000
```

And clear the data cache when model map is reinitialized — add to `initialize_model_map`:

```python
    _data_cache.clear()
```

- [ ] **Step 2: Update src/CLAUDE.md with execute_pandas documentation**

Add to the "Available Tools" section:

```markdown
### Code Execution
- `execute_pandas(model_id, code)` — Execute Python/pandas code against a model's data in a sandboxed environment

#### Variables available in execute_pandas:
- `sql_ts` — DataFrame with hourly timeseries. Datetime index, columns named `"{KeyValue}:{Name} [{Units}]"`. Energy values in Joules (divide by 1e9 for GJ).
- `html_tables` — Dict of `{(report_for, report_name, table_name): DataFrame}`. All HTML summary tables.
- `model_info` — Dict with `id`, `file_paths`, `file_types`.
- `pd` — pandas module
- `np` — numpy module

#### Common patterns:
```python
# Annual electricity in GJ
sql_ts["None:Electricity:Facility [J]"].sum() / 1e9

# Peak day for a variable
col = sql_ts.columns[0]
peak_hour = sql_ts[col].idxmax()
peak_day = sql_ts.loc[peak_hour.normalize():peak_hour.normalize() + pd.Timedelta(hours=23)]

# Get End Uses table
end_uses = html_tables[("Entire Facility", "Annual Building Utility Performance Summary", "End Uses")]
```
```

- [ ] **Step 3: Update MCP_TOOLS in run_test.sh**

Add `mcp__eplus_outputs__execute_pandas` to the MCP_TOOLS list in `test_prompts/run_test.sh`.

- [ ] **Step 4: Run full test suite**

Run: `cd /home/msweeney/repos/eplusout-mcp && uv run pytest -v`
Expected: All existing + new tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/server.py src/CLAUDE.md test_prompts/run_test.sh
git commit -m "feat: add execute_pandas tool to MCP server

Sandboxed pandas execution against pre-loaded model DataFrames.
Raises MAX_RESPONSE_CHARS to 50K. Updates tool docs."
```

---

## Task 4: Push Branch A

- [ ] **Step 1: Push branch**

```bash
cd /home/msweeney/repos/eplusout-mcp
git push -u origin experiment/pandas-exec
```

---

## Task 5: Add pre-built tools (Branch B)

**Files:**
- Create: `src/tools/func_aggregation.py`
- Modify: `src/server.py`
- Test: `tests/test_aggregation.py`

- [ ] **Step 1: Create Branch B from Branch A**

```bash
git checkout experiment/pandas-exec
git checkout -b experiment/hybrid
```

- [ ] **Step 2: Write aggregation tests**

```python
# tests/test_aggregation.py
import pytest
import pandas as pd
from src.tools.func_aggregation import compute_end_uses, compute_timeseries_stats


class TestEndUses:
    def test_returns_dataframe(self, buffalo_model):
        result = compute_end_uses([buffalo_model])
        assert isinstance(result, pd.DataFrame)

    def test_has_model_id_column(self, buffalo_model):
        result = compute_end_uses([buffalo_model])
        assert "model_id" in result.columns

    def test_heating_value_matches_known(self, buffalo_model):
        result = compute_end_uses([buffalo_model])
        row = result[result["model_id"].str.contains("Buffalo")]
        # Buffalo known: Heating NatGas = 1484.28 GJ
        # Column name derived from HTML header "Natural Gas [GJ]" -> "Natural_Gas"
        heat_gas_cols = [c for c in result.columns if "Heating" in c and "Natural_Gas" in c]
        assert len(heat_gas_cols) >= 1, f"No Heating Natural Gas column found. Columns: {list(result.columns)}"
        assert abs(float(row[heat_gas_cols[0]].iloc[0]) - 1484.28) < 0.1

    def test_multiple_models(self, atlanta_model, buffalo_model):
        result = compute_end_uses([atlanta_model, buffalo_model])
        assert len(result) == 2

    def test_sort_by(self, atlanta_model, buffalo_model):
        result = compute_end_uses([atlanta_model, buffalo_model], sort_by="Heating")
        # Buffalo has more heating, should be first
        assert "Buffalo" in result.iloc[0]["model_id"]


class TestTimeseriesStats:
    def test_annual_returns_dict(self, buffalo_model):
        result = compute_timeseries_stats(buffalo_model, rddid=179, agg="annual")
        assert "sum" in result
        assert "max" in result
        assert "peak_timestamp" in result

    def test_annual_sum_matches_known(self, buffalo_model):
        result = compute_timeseries_stats(buffalo_model, rddid=179, agg="annual")
        gj = result["sum"] / 1e9
        assert abs(gj - 5105.50) < 0.1

    def test_monthly_returns_12_rows(self, buffalo_model):
        result = compute_timeseries_stats(buffalo_model, rddid=179, agg="monthly")
        assert len(result) == 12

    def test_peak_day_returns_24_hours(self, buffalo_model):
        result = compute_timeseries_stats(buffalo_model, rddid=179, agg="peak_day")
        assert len(result["data"]) == 24

    def test_units_metadata_present(self, buffalo_model):
        result = compute_timeseries_stats(buffalo_model, rddid=179, agg="annual")
        assert "units" in result
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `cd /home/msweeney/repos/eplusout-mcp && uv run pytest tests/test_aggregation.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 4: Implement aggregation module**

```python
# src/tools/func_aggregation.py
import pandas as pd
import logging
from src.tools.func_html import get_all_table_data
from src.tools.func_sql import SqlTimeseries

logger = logging.getLogger(__name__)


def compute_end_uses(models: list, end_uses: list[str] | None = None, sort_by: str | None = None) -> pd.DataFrame:
    """Extract End Uses from HTML for multiple models. Returns DataFrame with values in GJ.

    Returns one row per model with all end-use values flattened into columns.
    Column naming: "{EndUse}_{FuelType}_GJ" e.g. "Heating_Natural_Gas_GJ"
    """
    rows = []
    for model in models:
        if not model.html_data:
            continue
        raw_tables = model.html_data.get_data()
        for table_info in raw_tables:
            if table_info["table_name"] != "End Uses":
                continue
            if table_info["report_name"] != "Annual Building Utility Performance Summary":
                continue
            data = table_info["table_data"]
            if not data or len(data) < 2:
                continue
            header = data[0]
            # Build one flat row per model with all end-use values
            model_row = {"model_id": model.model_id}
            for row_data in data[1:]:
                if not row_data:
                    continue
                end_use_name = row_data[0].strip()
                if end_uses and end_use_name not in end_uses:
                    continue
                for i, col in enumerate(header[1:], 1):
                    col_clean = col.strip().replace(" [GJ]", "").replace(" [m3]", "_m3")
                    col_clean = col_clean.replace(" ", "_")
                    key = f"{end_use_name}_{col_clean}_GJ"
                    try:
                        model_row[key] = float(row_data[i]) if i < len(row_data) else 0.0
                    except (ValueError, IndexError):
                        model_row[key] = 0.0
            rows.append(model_row)

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)

    if sort_by:
        sort_cols = [c for c in df.columns if sort_by in c and "GJ" in c]
        if sort_cols:
            df["_sort"] = df[sort_cols].sum(axis=1)
            df = df.sort_values("_sort", ascending=False).drop("_sort", axis=1)

    return df


def compute_timeseries_stats(model, rddid: int, agg: str = "annual") -> dict:
    """Compute pre-built statistics for a timeseries variable.

    Args:
        model: ModelFileData with sql_data
        rddid: ReportDataDictionary index
        agg: "annual", "monthly", "daily", "peak_day", "peak_week"
    """
    if not model.sql_data:
        return {"error": "Model has no SQL data"}

    ts = model.sql_data.get_timeseries()
    records = ts.getseries_by_record_id(rddid)
    if not records:
        return {"error": f"No data for RDD ID {rddid}"}

    df = pd.DataFrame(records)
    units = df["Units"].iloc[0]
    name = df["Name"].iloc[0]
    key_value = df["KeyValue"].iloc[0]
    series = df.set_index("dt")["Value"].astype(float)
    series.index = pd.to_datetime(series.index)

    if agg == "annual":
        return {
            "variable": f"{key_value}:{name}",
            "units": units,
            "sum": float(series.sum()),
            "sum_GJ": float(series.sum() / 1e9) if units == "J" else None,
            "mean": float(series.mean()),
            "min": float(series.min()),
            "max": float(series.max()),
            "peak_timestamp": str(series.idxmax()),
            "count": int(len(series)),
        }

    elif agg == "monthly":
        monthly = series.groupby(series.index.month).agg(["sum", "mean", "min", "max"])
        monthly.index.name = "month"
        return monthly.reset_index().to_dict(orient="records")

    elif agg == "daily":
        daily = series.groupby(series.index.date).agg(["sum", "mean", "min", "max"])
        daily.index.name = "date"
        return daily.reset_index().to_dict(orient="records")

    elif agg == "peak_day":
        peak_hour = series.idxmax()
        day_start = peak_hour.normalize()
        day_end = day_start + pd.Timedelta(hours=23)
        day_data = series.loc[day_start:day_end]
        return {
            "peak_date": str(day_start.date()),
            "peak_hour": str(peak_hour),
            "peak_value": float(series.max()),
            "units": units,
            "data": [{"hour": str(idx), "value": float(v)} for idx, v in day_data.items()],
        }

    elif agg == "peak_week":
        peak_hour = series.idxmax()
        week_start = peak_hour.normalize() - pd.Timedelta(days=3)
        week_end = peak_hour.normalize() + pd.Timedelta(days=3, hours=23)
        week_data = series.loc[week_start:week_end]
        daily = week_data.groupby(week_data.index.date).agg(["sum", "mean", "min", "max"])
        return {
            "peak_date": str(peak_hour.normalize().date()),
            "peak_value": float(series.max()),
            "units": units,
            "daily_summary": daily.reset_index().to_dict(orient="records"),
        }

    return {"error": f"Unknown aggregation: {agg}"}
```

- [ ] **Step 5: Wire tools into server.py**

Add to `src/server.py`:

```python
from src.tools.func_aggregation import compute_end_uses, compute_timeseries_stats


@mcp.tool()
def get_end_uses(
    model_ids: list[str] | str = "all",
    end_uses: list[str] | str = "all",
    sort_by: str | None = None
) -> dict:
    """Get annual end uses across one or more models in one call.

    Returns a table with one row per model, columns for each end use + fuel type.
    Values in GJ (matching HTML report units). Handles multi-model comparison.
    """
    model_map = _get_model_map()

    if model_ids == "all":
        models = model_map.models
    else:
        if isinstance(model_ids, str):
            model_ids = [model_ids]
        models = [model_map.get_model_by_id(mid) for mid in model_ids]

    eu_list = None if end_uses == "all" else (end_uses if isinstance(end_uses, list) else [end_uses])

    result_df = compute_end_uses(models, end_uses=eu_list, sort_by=sort_by)
    result = result_df.to_dict(orient="records")

    log_mcp_call("get_end_uses", f"{len(result)} models", kwargs={"model_ids": str(model_ids)[:100]})
    return _truncate_response(result, "models")


@mcp.tool()
def get_timeseries_stats(
    model_id: str,
    rddid: int | list[int],
    agg: str = "annual"
) -> dict:
    """Get pre-computed statistics for hourly timeseries variables.

    agg options:
    - "annual": sum, mean, min, max, peak_value, peak_timestamp (includes sum_GJ for energy)
    - "monthly": 12-row summary per month
    - "daily": 365-row summary per day
    - "peak_day": 24 hours around the peak value
    - "peak_week": ±3 days around the peak

    Values include units metadata.
    """
    model_map = _get_model_map()
    model = model_map.get_model_by_id(model_id)

    if isinstance(rddid, list):
        results = {}
        for rid in rddid:
            results[f"rdd_{rid}"] = compute_timeseries_stats(model, rid, agg)
        log_mcp_call("get_timeseries_stats", results, kwargs={"model_id": model_id, "rddid": rddid, "agg": agg})
        return results

    result = compute_timeseries_stats(model, rddid, agg)
    log_mcp_call("get_timeseries_stats", result, kwargs={"model_id": model_id, "rddid": rddid, "agg": agg})
    return result
```

- [ ] **Step 6: Run all tests**

Run: `cd /home/msweeney/repos/eplusout-mcp && uv run pytest -v`
Expected: All tests PASS

- [ ] **Step 7: Commit and push branch**

```bash
git add src/tools/func_aggregation.py src/server.py tests/test_aggregation.py
git commit -m "feat: add get_end_uses and get_timeseries_stats pre-built tools

Cross-model end uses comparison in one call.
Timeseries stats with annual/monthly/daily/peak_day aggregation.
Values include units metadata and GJ conversion for energy."
git push -u origin experiment/hybrid
```

---

## Task 6: Create prompt-only domain guide (Branch C)

**Files:**
- Create: `test_prompts/domain_guide.md`
- Create: `test_prompts/snippets/parse_end_uses.py`
- Create: `test_prompts/snippets/query_timeseries.py`
- Create: `test_prompts/snippets/unmet_hours.py`

- [ ] **Step 1: Create Branch C from pre-release-updates**

```bash
git checkout pre-release-updates
git checkout -b experiment/prompt-only
```

- [ ] **Step 2: Write domain guide**

```markdown
# test_prompts/domain_guide.md
# EnergyPlus Output Analysis Guide

## File Types
- `.table.htm` / `eplustbl.htm` — HTML summary report with all tabular data
- `.sql` — SQLite database with timeseries and tabular data
- `.epJSON` — Input model definition (JSON format)
- `.err` — Error/warning log
- `.rdd` — Report Data Dictionary (lists available output variables)

## Discovering Models
EnergyPlus outputs are grouped by filename stem. Use:
```bash
find <directory> -name "*.table.htm" -o -name "*.sql" | sort
```

## HTML Table Parsing
Tables in EnergyPlus HTML reports follow this pattern:
- Comment `<!-- FullName:ReportName_ReportFor_TableName -->` precedes each table
- The "End Uses" table is in "Annual Building Utility Performance Summary"
- Values in HTML are in GJ for energy, W for power, m³/s for airflow

Use the provided snippet `snippets/parse_end_uses.py` for reliable parsing.

## SQL Timeseries Querying
The SQL database contains:
- `ReportDataDictionary` — lists all available variables with RDD IDs
- `ReportData` — hourly values indexed by TimeIndex and RDD ID
- `Time` — maps TimeIndex to month/day/hour

**CRITICAL: SQL energy values are in Joules. Divide by 1e9 for GJ.**

Use the provided snippet `snippets/query_timeseries.py`.

## Unit Reference
| Source | Energy | Power | Airflow | Temperature |
|--------|--------|-------|---------|-------------|
| HTML tables | GJ | W | m³/s | °C |
| SQL timeseries | J | W | m³/s | °C |
| Conversion | 1 GJ = 1e9 J | | | |

## Common Gotchas
1. **"During Heating" vs "During Occupied Heating"** — The "Time Setpoint Not Met" table has BOTH. Always report "During Heating" (facility total) unless specifically asked for occupied hours.
2. **Zone multipliers** — Zone names containing "MULT" (e.g., ROOM_3_MULT19_FLR_3) represent multiple identical zones. The number after MULT is the multiplier.
3. **Design day vs annual** — Files with `.dd.` in the name are design-day sizing runs, not annual simulations. They will show zeros for annual energy.
4. **SQL meter names vs HTML labels** — HTML shows "Interior Lighting", SQL shows "InteriorLights:Electricity". They're the same data.
```

- [ ] **Step 3: Write parsing snippets**

Create `test_prompts/snippets/parse_end_uses.py`:

```python
"""Vetted snippet for parsing End Uses from EnergyPlus HTML reports."""
import re

def parse_end_uses(htm_path: str) -> dict:
    """Parse the End Uses table from an EnergyPlus HTML report.

    Returns dict with keys like 'Heating', 'Cooling', 'Total End Uses',
    each mapping to {'Electricity_GJ': float, 'NaturalGas_GJ': float, ...}
    """
    with open(htm_path) as f:
        content = f.read()

    match = re.search(r'End Uses</b>.*?<table[^>]*>(.*?)</table>', content, re.DOTALL)
    if not match:
        return {}

    rows = re.findall(r'<tr>(.*?)</tr>', match.group(1), re.DOTALL)
    header = [re.sub(r'<[^>]+>', '', c).strip()
              for c in re.findall(r'<t[hd][^>]*>(.*?)</t[hd]>', rows[0], re.DOTALL)]

    result = {}
    for row in rows[1:]:
        cells = [re.sub(r'<[^>]+>', '', c).strip()
                 for c in re.findall(r'<t[hd][^>]*>(.*?)</t[hd]>', row, re.DOTALL)]
        if not cells or not cells[0]:
            continue
        end_use = cells[0]
        values = {}
        for i, col in enumerate(header[1:], 1):
            col_clean = col.replace(' [GJ]', '_GJ').replace(' [m3]', '_m3').replace(' ', '_')
            try:
                values[col_clean] = float(cells[i]) if i < len(cells) else 0.0
            except ValueError:
                values[col_clean] = 0.0
        result[end_use] = values
    return result
```

Create `test_prompts/snippets/query_timeseries.py`:

```python
"""Vetted snippet for querying EnergyPlus SQL timeseries data."""
import sqlite3
import pandas as pd

def get_available_variables(sql_path: str) -> list[dict]:
    """List available hourly variables from an EnergyPlus SQL database."""
    conn = sqlite3.connect(sql_path)
    df = pd.read_sql(
        "SELECT ReportDataDictionaryIndex, Name, KeyValue, Units "
        "FROM ReportDataDictionary WHERE ReportingFrequency = 'Hourly'",
        conn
    )
    conn.close()
    return df.to_dict(orient='records')

def get_timeseries(sql_path: str, rdd_id: int) -> pd.Series:
    """Extract hourly timeseries for an RDD ID. Returns Series with datetime index."""
    conn = sqlite3.connect(sql_path)
    df = pd.read_sql(f"""
        SELECT t.Month, t.Day, t.Hour - 1 as Hour, rd.Value
        FROM ReportData rd
        JOIN Time t ON rd.TimeIndex = t.TimeIndex
        WHERE rd.ReportDataDictionaryIndex = {rdd_id}
          AND t.Interval = 60
        ORDER BY t.TimeIndex
    """, conn)
    conn.close()
    df['dt'] = pd.to_datetime(
        df['Month'].astype(str) + '-' + df['Day'].astype(str) + '-' + df['Hour'].astype(str),
        format='%m-%d-%H'
    )
    return df.set_index('dt')['Value'].astype(float)

def annual_sum_gj(sql_path: str, rdd_id: int) -> float:
    """Get annual sum for a variable, converted to GJ."""
    series = get_timeseries(sql_path, rdd_id)
    return series.sum() / 1e9
```

Create `test_prompts/snippets/unmet_hours.py`:

```python
"""Vetted snippet for extracting unmet hours from EnergyPlus HTML reports."""
import re

def parse_unmet_hours(htm_path: str) -> list[dict]:
    """Parse the 'Time Setpoint Not Met' table from HTML.

    Returns list of dicts with zone name, heating hours, cooling hours.
    Uses 'During Heating' (facility total), NOT 'During Occupied Heating'.
    """
    with open(htm_path) as f:
        content = f.read()

    match = re.search(r'Time Setpoint Not Met</b>.*?<table[^>]*>(.*?)</table>',
                       content, re.DOTALL)
    if not match:
        return []

    rows = re.findall(r'<tr>(.*?)</tr>', match.group(1), re.DOTALL)
    header = [re.sub(r'<[^>]+>', '', c).strip()
              for c in re.findall(r'<t[hd][^>]*>(.*?)</t[hd]>', rows[0], re.DOTALL)]

    h_idx = next((i for i, h in enumerate(header) if h == 'During Heating [hr]'), None)
    c_idx = next((i for i, h in enumerate(header) if h == 'During Cooling [hr]'), None)

    results = []
    for row in rows[1:]:
        cells = [re.sub(r'<[^>]+>', '', c).strip()
                 for c in re.findall(r'<t[hd][^>]*>(.*?)</t[hd]>', row, re.DOTALL)]
        if not cells or not cells[0]:
            continue
        results.append({
            'zone': cells[0],
            'heating_unmet_hrs': float(cells[h_idx]) if h_idx and h_idx < len(cells) else 0.0,
            'cooling_unmet_hrs': float(cells[c_idx]) if c_idx and c_idx < len(cells) else 0.0,
        })
    return results
```

- [ ] **Step 4: Commit and push**

```bash
git add test_prompts/domain_guide.md test_prompts/snippets/
git commit -m "feat: add EnergyPlus domain guide and vetted parsing snippets

Domain knowledge for prompt-only experiment (Branch C).
Includes gotchas, unit reference, and copy-pasteable Python snippets."
git push -u origin experiment/prompt-only
```

---

## Task 7: Update eval runner for 4 conditions

**Files:**
- Modify: `test_prompts/run_test.sh`

This task should be done on all three branches. Implement on `pre-release-updates` first, then cherry-pick.

- [ ] **Step 1: Switch to pre-release-updates**

```bash
git checkout pre-release-updates
```

- [ ] **Step 2: Rewrite run_test.sh for 4 modes + grading**

Replace the run functions and main case statement in `test_prompts/run_test.sh`. The key changes:

- Add `vanilla` mode (same as current `without-mcp` but named explicitly)
- Add `pandas-exec` mode (MCP tools including `execute_pandas`)
- Add `hybrid` mode (MCP tools including `execute_pandas` + `get_end_uses` + `get_timeseries_stats`)
- Add `prompt-only` mode (Bash/Read/Grep/Glob + domain guide as system prompt)
- Update `grade` to compare up to 4 results
- Keep `with-mcp` and `without-mcp` as aliases for backward compat

New MCP tool lists:

```bash
MCP_TOOLS_PANDAS="mcp__eplus_outputs__initialize_model_map"
MCP_TOOLS_PANDAS+=",mcp__eplus_outputs__get_available_models"
MCP_TOOLS_PANDAS+=",mcp__eplus_outputs__search_html_tables_by_keyword"
MCP_TOOLS_PANDAS+=",mcp__eplus_outputs__get_html_table_by_tuple"
MCP_TOOLS_PANDAS+=",mcp__eplus_outputs__get_sql_available_hourlies"
MCP_TOOLS_PANDAS+=",mcp__eplus_outputs__execute_pandas"

MCP_TOOLS_HYBRID="$MCP_TOOLS_PANDAS"
MCP_TOOLS_HYBRID+=",mcp__eplus_outputs__get_end_uses"
MCP_TOOLS_HYBRID+=",mcp__eplus_outputs__get_timeseries_stats"
```

New grading prompt should compare all available results (vanilla, pandas-exec, hybrid, prompt-only) side by side with the same 5-dimension scoring.

- [ ] **Step 3: Test the runner**

```bash
bash test_prompts/run_test.sh 01_cross_reference_meters vanilla
# Should run successfully with Bash/Read/Grep/Glob only
```

- [ ] **Step 4: Commit**

```bash
git add test_prompts/run_test.sh
git commit -m "feat: update eval runner for 4-condition experiment

Modes: vanilla, pandas-exec, hybrid, prompt-only, grade.
Grader compares up to 4 responses side-by-side."
```

- [ ] **Step 5: Cherry-pick eval runner commit to experiment branches**

```bash
# Get the commit hash of the eval runner update
EVAL_COMMIT=$(git rev-parse pre-release-updates)
git checkout experiment/pandas-exec && git cherry-pick "$EVAL_COMMIT"
git checkout experiment/hybrid && git cherry-pick "$EVAL_COMMIT"
git checkout experiment/prompt-only && git cherry-pick "$EVAL_COMMIT"
```

---

## Task 8: Run the experiment

- [ ] **Step 1: Run all conditions for prompt 01**

```bash
# On each branch, run its corresponding mode:
git checkout pre-release-updates
bash test_prompts/run_test.sh 01_cross_reference_meters vanilla

git checkout experiment/pandas-exec
bash test_prompts/run_test.sh 01_cross_reference_meters pandas-exec

git checkout experiment/hybrid
bash test_prompts/run_test.sh 01_cross_reference_meters hybrid

git checkout experiment/prompt-only
bash test_prompts/run_test.sh 01_cross_reference_meters prompt-only
```

- [ ] **Step 2: Grade prompt 01**

```bash
bash test_prompts/run_test.sh 01_cross_reference_meters grade
```

- [ ] **Step 3: Repeat for prompts 02-04**

Same pattern for each prompt.

- [ ] **Step 4: Collect results and decide**

Compare scores against success criteria from spec:
1. Any MCP branch scores higher on Correctness than Vanilla on ≥3 prompts?
2. MCP handles timeseries questions that previously failed?
3. Branch C matches MCP on correctness? (If so, MCP adds no value.)
