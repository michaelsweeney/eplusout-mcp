# MCP Tool Redesign: Pandas Execution + Accuracy-First Architecture

## Problem

The current MCP server provides 6 I/O wrapper tools (model discovery, HTML table retrieval, SQL timeseries extraction). A/B evaluation across 4 prompts (2-model, 20-model, cross-reference, unmet hours investigation) shows MCP consistently losing or tying against raw Bash/Python access.

**Root causes identified from evals:**

1. **Timeseries ceiling.** `get_timeseries_report_by_rddid_list` truncates at 10K chars. An 8760-hour variable is ~350KB. Claude hits the wall, gives up, and infers from HTML instead of computing from SQL. This directly caused MCP to score lower on correctness (prompts 02 and 04).

2. **One-model-at-a-time bottleneck.** `get_html_table_by_tuple` retrieves one table from one model per call. Comparing 20 models requires 20+ sequential MCP calls. Raw Python does it in one loop.

3. **Tools return data, not answers.** Claude still does all the math — unit conversions, aggregations, metric selection. When Claude confuses "During Occupied Heating" with "During Heating" (prompt 04), the tools provide no guardrail.

4. **No computation layer.** The most valuable thing an engineer wants — "compute X from my simulation data" — requires Claude to write Python via Bash anyway. The MCP tools can't help with novel analysis questions.

**Eval scores (MCP vs Raw):**

| Prompt | MCP | Raw | Winner |
|--------|-----|-----|--------|
| 01: Cross-reference meters (2 models) | 21 | 22 | Raw |
| 02: Unmet hours investigation (2 models) | 4.2 | 4.8 | Raw |
| 04: Large batch (20 models, HTML+SQL) | 12 | 20 | Raw |

## Goal

Make MCP tools genuinely valuable for building energy engineers asking diverse, complex questions of EnergyPlus output files. Mathematical accuracy is the top priority — this is an engineering tool where wrong numbers can lead to wrong design decisions.

## Design Constraints

1. **Accuracy over efficiency.** Tools should guarantee correct computation. Silent unit errors or metric confusion are unacceptable.
2. **Unlimited access.** Claude should never hit a data ceiling that forces it to guess or infer.
3. **Diverse questions.** Engineers ask everything from "compare annual heating across 5 climates" to "show me the 24-hour load profile on the peak cooling day." Pre-building tools for every permutation is not viable.
4. **Security.** Code execution must be sandboxed — no filesystem, network, or system access beyond the loaded EnergyPlus data.

## Experiment Structure

### 4 conditions, same prompts, same ground truth

| Condition | MCP? | Domain knowledge? | What it tests |
|-----------|------|--------------------|---------------|
| **Vanilla** (existing baseline) | No | No | Raw capability with generic tools |
| **Branch A: `pandas-exec`** | Yes | Via tools | Does server-side computation improve accuracy? |
| **Branch B: `hybrid`** | Yes | Via tools + pre-built | Do pre-built guardrails improve accuracy for common questions? |
| **Branch C: `prompt-only`** | No | Via CLAUDE.md + snippets | Is MCP needed, or is domain-aware prompting sufficient? |

### Branch details

#### Branch A: `experiment/pandas-exec`

Add one new tool to the existing server:

```python
@mcp.tool()
def execute_pandas(model_id: str, code: str) -> dict:
    """Execute Python/pandas code against a model's pre-loaded data.

    Available variables in the execution environment:
    - sql_ts: DataFrame of hourly timeseries (datetime index, columns per RDD variable)
    - html_tables: dict of {(report_for, report_name, table_name): DataFrame}
    - model_info: dict with model metadata (id, file_paths, file_types)
    - pd: pandas module
    - np: numpy module

    The last expression in the code is returned as the result.
    No filesystem, network, or import access. 30-second timeout.
    """
```

Keep existing tools: `initialize_model_map`, `get_available_models`, `search_html_tables_by_keyword`, `get_html_table_by_tuple`.

Remove: `get_timeseries_report_by_rddid_list` (subsumed by execute_pandas).

#### Branch B: `experiment/hybrid`

Everything in Branch A, plus 2 pre-built tools that address specific eval failure modes:

**Tool: `get_end_uses`**

```python
@mcp.tool()
def get_end_uses(
    model_ids: list[str] | str = "all",
    end_uses: list[str] | str = "all",
    sort_by: str | None = None
) -> dict:
    """Get annual end uses across one or more models.

    Returns a table with one row per model, columns for each end use + fuel type.
    Values in GJ (matching HTML report units). Handles multi-model comparison in one call.
    """
```

Solves: the 20-call bottleneck for cross-model comparison.

**Tool: `get_timeseries_stats`**

```python
@mcp.tool()
def get_timeseries_stats(
    model_id: str,
    rddid: int | list[int],
    agg: str = "annual"
) -> dict:
    """Get pre-computed statistics for hourly timeseries variables.

    agg options:
    - "annual": sum, mean, min, max, peak_value, peak_timestamp per variable
    - "monthly": 12-row summary with same stats per month
    - "daily": 365-row summary
    - "peak_day": 24 hours around the hour with maximum value
    - "peak_week": ±3 days around the peak

    Values returned with units metadata. Conversions (J→GJ) noted in response.
    """
```

Solves: the timeseries size ceiling without requiring Claude to write pandas code.

These 2 tools exist as **accuracy guardrails** for the 80% case. For novel questions, Claude uses `execute_pandas`.

#### Branch C: `experiment/prompt-only`

No MCP server changes. Instead, create domain knowledge files:

**File: `.claude/commands/eplus-analyze.md` or CLAUDE.md section**

Contents:
- EnergyPlus output file discovery (glob patterns, naming conventions, .table.htm vs .sql)
- HTML table parsing (vetted Python snippet using `re` for End Uses, Unmet Hours, Zone Sensible Heating)
- SQLite querying (vetted snippet for timeseries extraction, RDD lookup, annual sums)
- Unit reference table (J in SQL, GJ in HTML, W for design loads, m³/s for airflow)
- Common gotchas checklist:
  - "During Heating" vs "During Occupied Heating" — always report facility total unless asked otherwise
  - Zone multipliers — check for MULT in zone names, multiply loads accordingly
  - Design day data vs annual data — .dd files are sizing runs, not annual
  - SQL meter names vs HTML row labels — mapping reference

**File: `snippets/parse_end_uses.py`** — vetted function to extract End Uses from HTML
**File: `snippets/query_timeseries.py`** — vetted function to query SQL and compute stats
**File: `snippets/unmet_hours.py`** — vetted function to extract and summarize unmet hours

## Sandbox Security Design

### Restricted execution environment for `execute_pandas`

**Allowed in namespace:**
```python
SANDBOX_GLOBALS = {
    "__builtins__": {},  # empty — no default builtins
    # Data libraries
    "pd": pandas,
    "np": numpy,
    # Pre-loaded data (set per call)
    "sql_ts": None,       # DataFrame
    "html_tables": None,  # dict of DataFrames
    "model_info": None,   # dict
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
    "True": True,
    "False": False,
    "None": None,
}
```

**Blocked — enforced via AST inspection before execution:**
- `Import` and `ImportFrom` nodes
- Calls to: `open`, `exec`, `eval`, `compile`, `__import__`, `getattr`, `setattr`, `delattr`
- Attribute access to: `__builtins__`, `__class__`, `__subclasses__`, `__globals__`, `__code__`
- Names: `os`, `sys`, `subprocess`, `shutil`, `pathlib`, `socket`, `requests`, `urllib`

**Runtime guardrails:**
- 30-second timeout via `signal.alarm()` (Unix) or `threading.Timer` (cross-platform)
- Output serialized to JSON; capped at 50K chars (larger than current 10K limit, but bounded)
- If execution raises an exception, return the traceback as the result (not silently swallowed)

**Threat model:** The MCP server runs as a subprocess of Claude Code in the user's terminal. Claude Code already has Bash access to the same machine. The sandbox prevents *accidental* damage from generated code, not adversarial attack. This matches the security posture of Jupyter restricted kernels and Code Interpreter tools.

## Data Loading

### `sql_ts` DataFrame construction

When `execute_pandas` is called:

1. Load the model's SQL database
2. Query `ReportDataDictionary` for all hourly variables
3. For each variable, query `ReportData` joined with `Time` table
4. Construct a DataFrame: datetime index, one column per variable
5. Column names: `"{KeyValue}:{Name} [{Units}]"` (e.g., `"None:Electricity:Facility [J]"`)
6. Cache the DataFrame for subsequent calls on the same model

Column naming includes units so Claude can see what it's working with.

### `html_tables` dict construction

1. Parse all tables from the model's HTML report
2. Store as `{(report_for, report_name, table_name): DataFrame}`
3. Each DataFrame has proper column headers (first row promoted to header, deduped)
4. Cache for subsequent calls

### Caching strategy

- DataFrames cached in memory per model ID
- Cache cleared when `initialize_model_map` is called with a new directory
- Memory concern: 20 models × ~50MB SQL each = ~1GB. Mitigate with LRU eviction (keep last 5 models loaded)

## Eval Methodology

### Test runner updates

Update `run_test.sh` to support 4 modes:

```bash
./run_test.sh <prompt> vanilla        # Bash/Read/Grep/Glob only (existing without-mcp)
./run_test.sh <prompt> pandas-exec    # Branch A MCP tools
./run_test.sh <prompt> hybrid         # Branch B MCP tools
./run_test.sh <prompt> prompt-only    # Branch C domain docs, no MCP
./run_test.sh <prompt> grade          # Grade all available results
```

Each mode sets appropriate `--allowedTools` and `--append-system-prompt`.

### Grading updates

Update the grading prompt to compare up to 4 responses side-by-side. Score each on:
- **Correctness** (5 pts) — values match ground truth exactly
- **Completeness** (5 pts) — all prompt steps addressed
- **Efficiency** (5 pts) — direct approach, no thrashing
- **Insight** (5 pts) — useful interpretation beyond raw numbers
- **Graceful degradation** (5 pts) — handles missing data, explains limitations

### Prompts

Use existing prompts 01-04. No changes needed — the prompts are tool-agnostic.

## Implementation Order

1. **Branch A (`experiment/pandas-exec`):** Implement `execute_pandas` with sandbox, data loading, and caching. Update tool docs. ~1 day.
2. **Branch B (`experiment/hybrid`):** Branch from A. Add `get_end_uses` and `get_timeseries_stats`. ~0.5 day.
3. **Branch C (`experiment/prompt-only`):** Branch from `pre-release-updates`. Create CLAUDE.md content and snippets. No server changes. ~0.5 day.
4. **Eval runner updates:** Update `run_test.sh` for 4 modes and grading. ~0.5 day.
5. **Run evals:** All 4 conditions × 4 prompts = 16 runs + 4 grade reports. ~2-3 hours wall time.

## Success Criteria

The redesign is worth shipping if:

1. **Any MCP branch (A or B) scores higher on Correctness than Vanilla on at least 3 of 4 prompts.** Accuracy is the primary metric.
2. **The MCP branch handles the timeseries questions that currently fail** (prompt 02 boiler data, prompt 04 SQL cross-reference).
3. **Branch C (prompt-only) does NOT match MCP on correctness** — if it does, MCP adds no value and the answer is better documentation, not better tools.

If Branch B outperforms A, ship the hybrid. If A matches B, ship pandas-exec only (simpler). If C matches everything, reconsider whether an MCP server is the right product.
