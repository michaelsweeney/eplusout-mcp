# Testing Notes

## Running Tests

```bash
uv sync --group dev
uv run pytest tests/ -v
```

## Test Structure

| File | Covers |
|------|--------|
| `test_model_discovery.py` | `catalog_path()`, `ModelMap`, model search, attributes |
| `test_html_tables.py` | HTML report names, table retrieval, keyword search |
| `test_sql_timeseries.py` | `SqlTimeseries.availseries()`, `getseries_by_record_id()` |
| `test_epjson.py` | `read_epjson()`, object types, building properties |
| `test_pandas_execution.py` | Sandbox safety, `_format_result()` truncation |
| `test_utility_tools.py` | `get_associated_files_by_type()` for .err files |

All tests use session-scoped fixtures from `conftest.py` to avoid re-parsing the large HTML files per test.

## Known Weaknesses

### Hardcoded assertion values
Counts like `692` report names, `129` epJSON object types, `85` cooling tables, and `22` zones are derived from the current example files. If those files are updated, these assertions will break. Each value should ideally have a comment noting its origin.

### No `SqlTables` coverage
Only `SqlTimeseries` is tested. The `SqlTables` class (tabular summary extraction, `avail_tabular()`, `get_tabular()`, `search_tabular()`) has zero test coverage.

### No negative/edge-case SQL tests
Missing tests for invalid RDD IDs (e.g., `getseries_by_record_id(999999)`), negative IDs, or non-integer inputs.

### Weak timeseries pandas assertion
`test_pandas_on_timeseries` does not verify the actual computed mean value — the assertion is too loose to catch real regressions.

### Session-scoped fixtures can hide mutation bugs
`HtmlFileData` and `EpJsonFileData` cache parsed data internally. All tests share the same cached objects, so a test that accidentally mutates cached data could cause ordering-dependent failures.

### Untested code paths
- `get_table_by_tuple(..., asjson=False)` — raw table data return path
- `get_table_by_tuple` when multiple tables match the same tuple
- `ModelMap.get_epjson_by_id()` and `get_html_by_id()`
- `get_file_info()` stem-stripping logic for `.table.htm` files
- `get_associated_files_by_type(..., file_type='csv')`
- `execute_multiline_pandas_query` security beyond `__import__` (e.g., `eval()`, `globals()`)

### Filesystem dependency
All tests depend on the physical `example-files/` directory. If a file is missing or corrupted, failures will be confusing rather than producing a clear "fixture missing" message. There is no validation at fixture setup time.

### Working directory sensitivity
Tests rely on `Path(__file__).parent.parent / "example-files"` in `conftest.py` (absolute path), but any test that constructs paths differently could break when pytest is invoked from a different directory.
