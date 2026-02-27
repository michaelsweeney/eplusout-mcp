# Security Review - EnergyPlus MCP Server

## Executive Summary

This review identifies 6 security issues ranging from **HIGH** to **LOW** severity. All issues can be fixed with minimal code changes while preserving existing functionality. Quick fixes are provided for each issue.

---

## 1. SQL INJECTION (HIGH SEVERITY)

### Location
- `src/tools/func_sql.py:192` - TabularData query
- `src/tools/func_sql.py:424` - ReportData query

### Issue
String formatting is used to build SQL queries instead of parameterized queries:

```python
# Line 192 - VULNERABLE
tablestr = self._exec_pandas_query(
    "SELECT * FROM 'TabularData' WHERE TableNameIndex = {0} AND ReportForStringIndex = {1} AND ReportNameIndex = {2}".format(tablenameidx, reportforidx, reportnameidx))

# Line 424 - VULNERABLE
listquery = f'SELECT "Value","ReportDataDictionaryIndex","TimeIndex" FROM "ReportData" WHERE "ReportDataDictionaryIndex" == {rddid}'
```

### Risk
While current values come from internal string cache lookups (reducing immediate risk), this pattern is brittle and vulnerable if the data source changes or is compromised.

### Quick Fix
Use parameterized queries (pandas `read_sql` with parameters):

```python
# Line 192 - FIXED
tablestr = self._exec_pandas_query(
    "SELECT * FROM 'TabularData' WHERE TableNameIndex = ? AND ReportForStringIndex = ? AND ReportNameIndex = ?",
    params=(tablenameidx, reportforidx, reportnameidx))

# Note: pandas.read_sql with params parameter
conn = self._get_connection()
tablestr = pd.read_sql(query, conn, params=(tablenameidx, reportforidx, reportnameidx))

# Line 424 - FIXED (already safer with integer check)
# Add type validation for rddid first (see Issue #3)
listquery = 'SELECT "Value","ReportDataDictionaryIndex","TimeIndex" FROM "ReportData" WHERE "ReportDataDictionaryIndex" = ?'
df_query = self._df_query(listquery, params=(rddid,))
```

---

## 2. PATH TRAVERSAL VULNERABILITY (MEDIUM SEVERITY)

### Location
- `src/server.py:33` - `_set_current_directory()`
- `src/server.py:54` - `initialize_model_map()`

### Issue
Directory paths are not validated for path traversal attacks:

```python
# Line 33 - VULNERABLE
_current_directory = str(Path(directory).absolute())
```

An attacker could pass paths like `../../../etc/passwd` which would be made absolute but not validated.

### Risk
Allows reading arbitrary directories outside the intended model directory.

### Quick Fix
Add directory validation:

```python
# FIXED
def _validate_directory(directory: str) -> str:
    """
    Validate and sanitize directory path.
    Ensures path is within allowed base directory.
    """
    target_path = Path(directory).absolute()
    base_path = Path(EPLUS_RUNS_DIRECTORY).absolute()

    # Ensure target is within or equal to base
    try:
        target_path.relative_to(base_path)
    except ValueError:
        raise ValueError(
            f"Directory must be within {base_path}, got {target_path}"
        )

    return str(target_path)

def _set_current_directory(directory: str) -> None:
    """Set the directory to be used by all model tools."""
    global _current_directory
    _current_directory = _validate_directory(directory)
```

Add to both `initialize_model_map()` and `get_available_models()` calls.

---

## 3. UNVALIDATED RDD INPUT (MEDIUM SEVERITY)

### Location
- `src/tools/func_sql.py:413, 424` - RDD ID used in SQL without type checking
- `src/server.py:509` - RDD ID loop without validation

### Issue
RDD IDs are passed directly into SQL queries without integer type validation:

```python
# Line 413 - VULNERABLE
labelquery = self._exec_query(f"SELECT * FROM ReportDataDictionary WHERE ReportDataDictionaryIndex == {rddid}")

# Line 424 - VULNERABLE
listquery = f'SELECT "Value","ReportDataDictionaryIndex","TimeIndex" FROM "ReportData" WHERE "ReportDataDictionaryIndex" == {rddid}'
```

### Risk
While Python type hints are present, there's no runtime validation. Invalid input could cause SQL errors or unexpected behavior.

### Quick Fix
Add input validation in `getseries_by_record_id()`:

```python
# FIXED - Add type validation
def getseries_by_record_id(self, rddid: int):
    """
    Given an RDD ID, return the corresponding time series as a DataFrame with a datetime index.
    """
    # Validate input type and range
    if not isinstance(rddid, int):
        raise TypeError(f"RDD ID must be an integer, got {type(rddid).__name__}")

    if rddid <= 0:
        raise ValueError(f"RDD ID must be positive, got {rddid}")

    # Use parameterized query
    labelquery = self._exec_query(
        "SELECT * FROM ReportDataDictionary WHERE ReportDataDictionaryIndex = ?",
        params=(rddid,)
    )
    # ... rest of function
```

Also validate in `src/server.py:509`:

```python
# In get_timeseries_report_by_rddid_list()
for rdd in rddid:
    if not isinstance(rdd, int) or rdd <= 0:
        raise ValueError(f"Invalid RDD ID: {rdd}")
    rdf = model.sql_data.get_timeseries().getseries_by_record_id(rdd)
```

---

## 4. UNSAFE FILE OPERATIONS (MEDIUM SEVERITY)

### Location
- `src/tools/func_html.py:25` - `read_html_lines()`
- `src/tools/func_epjson.py:16` - `read_epjson()`

### Issue
Files are opened based on paths without validation that they belong to the model:

```python
# func_html.py:25 - VULNERABLE
with open(html_file_path, 'r', encoding='utf-8') as file:

# func_epjson.py:16 - VULNERABLE
with open(epjsonfile, 'r') as f:
```

### Risk
If `html_file_path` or `epjsonfile` contain user-controlled paths, arbitrary files could be read.

### Quick Fix
Validate file paths are within the model's expected directory:

```python
# FIXED - Add path validation helper
from pathlib import Path

def _validate_model_file_path(file_path: str, model_directory: str) -> str:
    """
    Validate that file_path is within the model directory.
    Prevents reading arbitrary files via path traversal.
    """
    file_path = Path(file_path).absolute()
    model_dir = Path(model_directory).absolute()

    try:
        file_path.relative_to(model_dir)
    except ValueError:
        raise ValueError(f"File {file_path} is not within model directory {model_dir}")

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    return str(file_path)

# Update func_html.py
def read_html_lines(html_file_path: str) -> list[str]:
    """Read all lines from an HTML file and return them as a list of strings."""
    try:
        # Validate file is accessible (path validation happens in model_data.py)
        with open(html_file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
    except FileNotFoundError:
        print(f"Error: File '{html_file_path}' not found.")
        return []
    except Exception as e:
        # Don't expose full path or exception details
        print(f"Error reading file: Permission denied or invalid path")
        return []
    return lines

# Update func_epjson.py
def read_epjson(epjsonfile: str) -> dict:
    """Read and parse epJSON file."""
    try:
        with open(epjsonfile, 'r') as f:
            epjd = json.load(f)
        return epjd
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in epJSON file: {str(e)[:50]}")
    except Exception as e:
        raise IOError(f"Cannot read epJSON file: Permission denied or file not found")
```

---

## 5. ERROR INFORMATION DISCLOSURE (LOW SEVERITY)

### Location
- `src/dataloader.py:128, 243` - Exception messages returned to user
- `src/tools/func_sql.py` - Error handling in queries
- `src/server.py:564` - Exception details in responses

### Issue
Full exception messages are returned in responses, potentially leaking system information:

```python
# Line 128 - VERBOSE ERROR
except Exception as e:
    return f"Query execution error: {str(e)}"

# Line 564 - RETURNS EXCEPTION TEXT
except Exception as e:
    return f"Error reading usage instructions: {str(e)}"
```

### Risk
Error messages can reveal file paths, library versions, internal structure, or SQL schema.

### Quick Fix
Log full errors internally, return generic messages to users:

```python
# FIXED - dataloader.py
import logging

logger = logging.getLogger(__name__)

def execute_pandas_query(df: pd.DataFrame, query: str) -> str:
    """Execute a single-line pandas query..."""
    try:
        # ... existing code ...
        result = eval(query, safe_globals)
        return _format_result(result)
    except SyntaxError:
        return "Query syntax error. Check your expression and try again."
    except NameError as e:
        # Don't expose which name isn't available
        return "Undefined variable or function in query."
    except Exception as e:
        logger.error(f"Pandas query execution failed: {type(e).__name__}: {str(e)}")
        return "Query execution failed. Please check your query syntax."

# FIXED - server.py:564
@mcp.tool()
def get_usage_instructions() -> str:
    """Get comprehensive usage instructions..."""
    try:
        with open('src/CLAUDE.md', 'r') as f:
            result = f.read()
            log_mcp_call('get_usage_instructions', result, kwargs={})
            return result
    except FileNotFoundError:
        return "Usage instructions not available."
    except Exception as e:
        logger.error(f"Error reading usage instructions: {type(e).__name__}")
        return "Unable to load usage instructions. Please try again later."
```

---

## 6. ATTRIBUTE ACCESS IN EVAL/EXEC (MEDIUM SEVERITY)

### Location
- `src/dataloader.py:122, 233` - eval() and exec() usage

### Issue
While `__builtins__` is restricted, Python objects can use attribute access to access dangerous methods:

```python
# POTENTIALLY VULNERABLE
result = eval(query, safe_globals)
# Attacker could use: df.__class__.__bases__[0].__subclasses__()
```

### Risk
Skilled attackers might escape the restricted environment through object introspection.

### Quick Fix
Add attribute access restriction using `RestrictedPython` library or implement checks:

**Option 1: Use RestrictedPython (requires new dependency)**
```bash
pip install RestrictedPython
```

```python
# FIXED - Option 1: Using RestrictedPython
from restricted import compile_restricted
import types

def execute_pandas_query(df: pd.DataFrame, query: str) -> str:
    """Execute a single-line pandas query in a secure environment."""
    try:
        # Compile code with restrictions
        code = compile_restricted(query, '<string>', 'eval')
        if code.errors:
            return f"Syntax error in query: {code.errors}"

        safe_globals = {
            'df': df, 'pd': pd, 'np': np,
            'len': len, 'str': str, 'int': int, 'float': float,
            'list': list, 'dict': dict, 'sum': sum, 'max': max, 'min': min,
            '__builtins__': {}
        }

        result = eval(code.code, safe_globals)
        return _format_result(result)
    except Exception as e:
        logger.error(f"Query execution error: {type(e).__name__}")
        return "Query execution failed."
```

**Option 2: Manual attribute whitelist (without new dependency)**
```python
# FIXED - Option 2: Whitelist safe attributes
import ast

def _is_safe_expression(query: str) -> bool:
    """Check if expression only uses whitelisted attributes."""
    try:
        tree = ast.parse(query, mode='eval')
    except SyntaxError:
        return False

    UNSAFE_ATTRIBUTES = {'__', '_ipython_', 'im_func', 'func_code'}

    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute):
            if node.attr.startswith('_'):  # Block private attributes
                return False
    return True

def execute_pandas_query(df: pd.DataFrame, query: str) -> str:
    """Execute a single-line pandas query in a secure environment."""
    if not _is_safe_expression(query):
        return "Query contains restricted attributes (e.g., private/dunder methods)."

    try:
        safe_globals = {
            'df': df, 'pd': pd, 'np': np,
            'len': len, 'str': str, 'int': int, 'float': float,
            'list': list, 'dict': dict, 'sum': sum, 'max': max, 'min': min,
            '__builtins__': {}
        }
        result = eval(query, safe_globals)
        return _format_result(result)
    except Exception as e:
        logger.error(f"Query execution error: {type(e).__name__}")
        return "Query execution failed."
```

**Recommendation**: Use Option 2 (manual whitelist) to avoid adding new dependencies. It's sufficient for this use case.

---

## Summary Table

| # | Issue | Severity | Location | Fix Type | Effort |
|---|-------|----------|----------|----------|--------|
| 1 | SQL Injection | HIGH | func_sql.py:192, 424 | Use parameterized queries | 15 min |
| 2 | Path Traversal | MEDIUM | server.py:33, 54 | Add path validation | 20 min |
| 3 | Unvalidated RDD Input | MEDIUM | func_sql.py, server.py | Add type/range checks | 10 min |
| 4 | Unsafe File Operations | MEDIUM | func_html.py, func_epjson.py | Validate file paths | 15 min |
| 5 | Error Disclosure | LOW | dataloader.py, server.py | Generic error messages | 10 min |
| 6 | Attribute Access in eval | MEDIUM | dataloader.py | Whitelist safe attributes | 15 min |

**Total Estimated Time: ~85 minutes**

---

## Implementation Priority

1. **Immediate (HIGH)**: #1 (SQL Injection) - Highest risk
2. **High**: #2 (Path Traversal), #3 (Unvalidated Input)
3. **Medium**: #4 (Unsafe Files), #6 (eval Attributes)
4. **Low**: #5 (Error Disclosure) - Quality improvement

---

## Testing Recommendations

After implementing fixes:

1. **SQL Injection**: Test with special characters in table names (already cached, but test edge cases)
2. **Path Traversal**: Test with `../`, `..\\`, absolute paths outside eplus_files/
3. **RDD Validation**: Test with negative numbers, non-integers, very large numbers
4. **File Operations**: Test with paths outside model directory
5. **Error Messages**: Verify no sensitive info in error responses
6. **eval() Restrictions**: Try attribute access patterns like `df.__class__`, `pd.__import__`

---

## Existing Protections (Preserved)

✅ Restricted builtins in eval/exec (preserved)
✅ File type restrictions (.epJSON, .sql, .htm only)
✅ Read-only operations (no data modification)
✅ Model caching prevents filesystem scanning on each call
✅ Existing input validation in epJSON searches

