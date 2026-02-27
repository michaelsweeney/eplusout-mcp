# Code Review Summary: Extraneous & Redundant Code

**Date:** February 26, 2026
**Repository:** mcp-eplus-outputs
**Scope:** Security risks, dead code, code quality issues

---

## EXTRANEOUS & REDUNDANT CODE IDENTIFIED

### 1. Commented-Out Code Blocks

#### src/server.py (Lines 163-173)
```python
# result = table
# log_mcp_call(
#     'get_html_table_by_tuple',
#     result,
#     kwargs={
#         'id': id,
#         'query_tuple': query_tuple
#     }
# )
#
# return table
```
**Status:** Dead code left after refactoring
**Action:** REMOVE

---

### 2. Duplicate Imports

#### src/tools/func_html.py (Lines 2 and 4)
```python
from typing import List, Optional, Dict, Tuple  # Line 2
...
from typing import List, Dict  # Line 4 - DUPLICATE!
```
**Action:** Remove line 4

#### src/utils/helpers.py
```python
import os  # Line 2
...
import os  # Line 5 - DUPLICATE!
```
**Action:** Remove duplicate import

---

### 3. Unused Imports

#### src/tools/func_epjson.py
- `HTMLParser` from html.parser - Never used
- `List, Optional, Dict, Tuple` from typing - Never used (only `json` is used)
- `re` module - Never imported or used

**Action:** Clean up to just: `import json`

#### src/utils/helpers.py
- `time` module imported but never used in code
- `Literal` from typing - Imported but not used

**Action:** Remove unused imports

#### src/tools/func_html.py
- Duplicate typing imports (see above)

---

### 4. Broken/Unused Functions

#### src/tools/func_sql.py - `_exec_query()` (Lines 88-98)
```python
def _exec_query(self, query):
    conn = sqlite3.connect(self.sql_file)
    cursor = conn.cursor()
    cursor.execute()  # BUG: Missing query parameter!
    rows = cursor.fetchall()
    conn.close()
    return rows
```
**Status:**
- Function has a critical bug (execute() called with no arguments)
- Function is never called anywhere in codebase
- Will always raise TypeError

**Action:** REMOVE - Function is broken and unused

---

### 5. Deprecated Methods

#### src/tools/func_sql.py - `old_getseries()` (Lines 461-498)
```python
def old_getseries(self, df: pd.DataFrame):
    """Get series of data from the datafame - OLD VERSION"""
    # ... implementation ...
```
**Status:**
- Clearly marked as "OLD" version
- Indicates dead code that should have been removed
- Not called anywhere

**Action:** REMOVE

---

### 6. Unreachable Code

#### src/tools/func_sql.py - `availseries()` (Lines 379-382)
```python
def availseries(self):
    df = ...
    return df.to_dict(orient='records')  # Line 381

    return df.T.to_dict()  # Line 382 - UNREACHABLE!
```
**Status:** Unreachable return statement after first return

**Action:** REMOVE line 382

---

### 7. Wrong Class Instantiation

#### src/tools/func_sql.py - `get_tables()` (Line 123)
```python
def get_tables(self):
    if self.sql_tables is None:
        self.sql_tables = SqlTimeseries(sql_file=self.file_path)  # BUG: Wrong class!
    return self.sql_tables
```
**Status:**
- Creates `SqlTimeseries` instead of `SqlTables`
- This is a critical bug, not just extraneous code
- Will cause runtime errors when get_tables() is called

**Action:** FIX - Change to `SqlTables(sql_file=self.file_path)`

---

### 8. Print Statements (Should Use Logging)

#### src/model_data.py
- Line 49: `print(f"Scanning for models in {self.directory}")`
- Line 50: `print(f"Found {len(self.models)} models")`
- Line 315: `print(f"Saved model map to {cache_file}")`
- Line 680: `print(f"Looking for model {id} in catalog")`
- Line 683: `print(f"Model {id} not found in catalog")`

#### src/tools/func_sql.py
- Line 417: `print(f'warning - multiple found for {labelquery}')`
- Line 419: `print(f'none found for {labelquery}')`

**Status:** Using print() instead of logging module (poor practice for production code)

**Action:** Replace all print() with logging calls at appropriate levels (INFO, WARNING, ERROR)

---

### 9. Bare Exception Handling

#### src/tools/func_html.py (Lines 30, 206)
```python
except Exception as e:
    print(f"Error reading file: {e}")
```
**Status:**
- Catches ALL exceptions (too broad)
- Uses print() instead of logging
- Masks important exceptions like KeyboardInterrupt, SystemExit

**Action:**
- Catch specific exceptions: `except (FileNotFoundError, IOError, OSError) as e:`
- Use logging instead of print()

---

### 10. Dead/Incomplete Logging Implementation

#### src/logger.py
**Status:** Entire file is commented out - essentially a dead file

**Action:** Either implement and use properly, or remove entirely

---

### 11. Parameter Mismatch Bug (Not Dead Code, But Critical)

#### src/monitor.py (Lines 50-58 vs 143-151)
```python
# Function signature (lines 50-58):
def log_mcp_call(
    function_name: str,
    result: Any,
    kwargs: dict = {},
    args: tuple = ()
    # Missing: duration, success, error_message
):
    pass

# But decorator tries to call it with (lines 143-151):
log_mcp_call(
    function_name=function_name,
    args=args,
    kwargs=kwargs,
    result=result,
    duration=duration,           # NOT IN SIGNATURE!
    success=success,             # NOT IN SIGNATURE!
    error_message=error_message  # NOT IN SIGNATURE!
)
```
**Status:** Function signature doesn't match call site - will crash at runtime

**Action:** FIX - Either add missing parameters to function signature, or update call site

---

## SUMMARY OF ITEMS TO REMOVE/FIX

### Remove Entirely (3 items)
1. `_exec_query()` function in func_sql.py:88-98
2. `old_getseries()` function in func_sql.py:461-498
3. Unreachable return statement in func_sql.py:382
4. Entire logger.py file (dead implementation)

### Fix/Replace (4 items)
1. Commented-out code block in server.py:163-173
2. Duplicate imports (func_html.py, helpers.py)
3. All print() statements → use logging module
4. Broad exception handlers → catch specific exceptions

### Critical Bugs to Fix (2 items)
1. Wrong class in get_tables() - Line 123 in func_sql.py
2. Parameter mismatch in log_mcp_call() - monitor.py

### Cleanup (1 category)
- Remove 8+ unused imports across multiple files

---

## ESTIMATED CLEANUP EFFORT

| Category | Count | Time |
|----------|-------|------|
| Remove dead code | 4 | 15 min |
| Fix critical bugs | 2 | 30 min |
| Replace print() with logging | 7+ | 45 min |
| Remove duplicate/unused imports | 8+ | 20 min |
| Fix exception handling | 2 | 15 min |
| **Total** | **23+** | **~2 hours** |

---

## IMPACT ANALYSIS

### High Impact (Will Affect Functionality)
- Wrong class instantiation in get_tables() - CRITICAL
- Parameter mismatch in logging decorator - CRITICAL
- Broken _exec_query() function - If ever used, will fail

### Medium Impact (Code Quality)
- Commented-out code - Confusing to maintainers
- Dead functions (old_getseries) - Unnecessary code bulk
- Bare exception handling - Can mask real errors
- Print statements - Can't filter/control output

### Low Impact (Cleanup)
- Duplicate imports - Harmless but redundant
- Unused imports - Noise in code
- Unreachable code - Dead but harmless

---

## RECOMMENDATIONS

### Immediate (Next PR)
1. Fix critical bugs (wrong class, parameter mismatch)
2. Remove _exec_query() function
3. Uncomment or remove dead code block in server.py

### Short Term (Next Sprint)
1. Remove old_getseries() and other deprecated methods
2. Replace all print() with logging
3. Clean up imports
4. Fix exception handling

### Medium Term
1. Add comprehensive unit tests
2. Set up pre-commit hooks to catch dead code
3. Add type checking (mypy) to catch bugs earlier
4. Configure logging properly across application

---

## CODEBASE HEALTH METRICS

| Metric | Status | Notes |
|--------|--------|-------|
| Dead Code | ⚠️ MODERATE | 4 functions/blocks to remove |
| Code Duplication | ✅ LOW | Minimal duplication found |
| Unused Imports | ⚠️ MODERATE | 8+ imports to clean up |
| Error Handling | ❌ POOR | Bare exceptions, bare passes |
| Logging | ❌ POOR | Only print() used, no logging module |
| Type Hints | ✅ GOOD | Present in most functions |
| Documentation | ✅ GOOD | Comprehensive docstrings |
| Test Coverage | ❌ NONE | No tests present |

**Overall Codebase Quality:** MEDIUM (solid architecture, but needs cleanup and fixes)
