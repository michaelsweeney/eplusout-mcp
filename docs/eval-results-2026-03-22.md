# Can MCP Tools Improve AI-Assisted EnergyPlus Analysis?

## A Controlled Evaluation of Four Approaches

**Date:** March 22, 2026
**Repository:** [eplusout-mcp](https://github.com/michaelsweeney/eplusout-mcp)
**Models tested:** ASHRAE 90.1 prototype buildings (HotelLarge, Hospital, OfficeLarge, OfficeSmall, ApartmentMidRise, HotelSmall)

---

## 1. Background

EnergyPlus is the U.S. Department of Energy's flagship building energy simulation engine. A single simulation produces dozens of output files — HTML summary reports, SQLite databases with hourly timeseries, error logs, and input echo files. Extracting insights requires navigating multiple file formats, understanding domain-specific units and conventions, and cross-referencing data across files.

We built an MCP (Model Context Protocol) server that exposes EnergyPlus output data to AI assistants like Claude. The question: **do specialized MCP tools produce more accurate analysis than letting the AI parse files directly?**

This matters because building energy modeling is an engineering discipline where numerical accuracy has real consequences — incorrect heating loads lead to undersized equipment, missed unmet hours lead to occupant discomfort, and wrong energy totals lead to failed code compliance.

## 2. Experimental Design

### 2.1 Conditions

We tested four approaches to AI-assisted EnergyPlus analysis, each giving Claude different tools and context:

| Condition | Tools Available | Domain Knowledge | Description |
|---|---|---|---|
| **Vanilla** | Bash, Read, Grep, Glob | None | Baseline. Claude parses HTML and queries SQLite directly using shell commands and Python scripts. |
| **Pandas-Exec** | MCP tools + `execute_pandas` | Via tool docs | MCP server provides model discovery, HTML table search, and a sandboxed pandas execution environment. Claude writes pandas code; the server executes it against pre-loaded DataFrames. |
| **Hybrid** | MCP tools + `execute_pandas` + `get_end_uses` + `get_timeseries_stats` | Via tool docs | Everything in Pandas-Exec, plus two pre-built aggregation tools designed to prevent common errors (unit confusion, metric misidentification). |
| **Prompt-Only** | Bash, Read, Grep, Glob | EnergyPlus domain guide + vetted Python snippets | No MCP server. Instead, Claude receives a detailed system prompt covering EnergyPlus file formats, unit conversions, common gotchas, and copy-pasteable parsing functions. |

### 2.2 Test Prompts

Three prompts of increasing complexity, each with pre-computed ground truth values:

| Prompt | Models | Complexity | Key challenge |
|---|---|---|---|
| **01: Cross-Reference Meters** | 2 (Atlanta, Buffalo) | Low | Sum 8760 hourly SQL values, compare against HTML End Uses table |
| **02: Unmet Hours Investigation** | 2 (Atlanta, Buffalo) | Medium | Find worst unmet-hours zone, pull boiler timeseries, cross-reference with sizing data |
| **04: Large Batch Analysis** | 20 (6 building types × 3-4 climates) | High | Rank heating/cooling across 20 models, identify unmet hours, cross-reference SQL and HTML |

### 2.3 Evaluation

Each condition ran against each prompt using Claude Sonnet via the `claude` CLI in non-interactive mode (`-p` flag). A separate Claude instance graded all responses against ground truth on five dimensions:

| Dimension | Weight | What it measures |
|---|---|---|
| **Correctness** | Highest | Do numerical values match ground truth exactly? |
| **Completeness** | High | Were all parts of the prompt addressed? |
| **Efficiency** | Medium | Was the approach direct, or did it thrash/retry? |
| **Insight** | Medium | Did the response add useful domain interpretation? |
| **Graceful degradation** | Medium | How were missing data or edge cases handled? |

### 2.4 Controls

- All conditions used the same Claude model (Sonnet) and the same prompt text.
- Each run was stateless — no conversation history carried between conditions.
- The grader received all responses simultaneously with no indication of which was expected to win.
- Ground truth was computed independently using verified Python scripts before any evaluations ran.

## 3. Results

### 3.1 Prompt 01: Cross-Reference Meters (2 models, low complexity)

| Condition | Correctness | Completeness | Efficiency | Insight | Degradation | **Total** | **Time** |
|---|---|---|---|---|---|---|---|
| **Pandas-Exec** | **5** | **5** | **5** | 3 | 4 | **22** | **77s** |
| **Prompt-Only** | **5** | **5** | 2 | **5** | **5** | **22** | 102s |
| Hybrid | 4 | **5** | 3 | 4 | 4 | 20 | 87s |
| Vanilla | 4 | 4 | 4 | 3 | 3 | 18 | 91s |

**Key finding:** Pandas-Exec and Prompt-Only tied on total score. Pandas-Exec was 33% faster and correctly distinguished a subtle RDD ID difference between models (Buffalo uses RDD 4914 for `ElectricityNet:Facility`, not 4910 like Atlanta). Vanilla conflated the two. Hybrid reported a floating-point precision difference as a "mismatch" when the values were functionally identical.

### 3.2 Prompt 02: Unmet Hours Investigation (2 models, medium complexity)

| Condition | Correctness | Completeness | Efficiency | Insight | Degradation | **Total** | **Time** |
|---|---|---|---|---|---|---|---|
| **Prompt-Only** | **5** | **5** | 4 | **5** | **5** | **24** | 264s |
| Vanilla | **5** | 4 | **5** | 4 | **5** | 23 | **197s** |
| Pandas-Exec | **5** | **5** | 3 | 4 | **5** | 22 | 289s |
| Hybrid | 2 | 3 | 3 | 3 | 4 | 15 | 281s |

**Key finding:** Prompt-Only produced the richest analysis — it computed boiler efficiency (~77%, consistent with ASHRAE 90.1 baseline), identified the 0.56°C unmet-hours tolerance threshold, and hypothesized morning setback-ramp timing as the cause of unmet hours. None of the other conditions surfaced these insights.

Hybrid scored worst (15/25) due to a critical scope error: its pre-built tools scanned all 24 models in the `example-files` directory and identified an OfficeLarge model from the `large-batch` subdirectory as the "worst zone" — technically correct globally, but the prompt asked about the two named primary models. The pre-built tools' eagerness to aggregate broadly caused a scope mismatch.

### 3.3 Prompt 04: Large Batch Analysis (20 models, high complexity)

Prompt 04 used a weighted scoring scheme (Correctness 3×, Completeness 2×, others 1×) due to the number of values to verify.

| Condition | Correctness | Completeness | Efficiency | Insight | Degradation | **Weighted** | **Time** |
|---|---|---|---|---|---|---|---|
| **Prompt-Only** | **3** | **5** | **5** | 4 | 3 | **3.9** | **340s** |
| Pandas-Exec | **3** | 2 | 4 | **4** | 3 | 3.2 | 457s |
| Hybrid | 2 | **5** | 3 | **4** | 2 | 3.1 | 498s |
| Vanilla | 1 | 1 | 1 | 1 | 2 | 1.2 | 898s |

**Key finding:** This was the only prompt where scale mattered. Vanilla took nearly 15 minutes and produced only a summary paragraph with no verifiable data. Prompt-Only was 2.6× faster and fully complete.

Both MCP conditions (Pandas-Exec and Hybrid) shared a systematic error: they extracted the wrong cooling values for several models, underreporting by up to 24%. The grader attributed this to the MCP tool abstraction hiding which specific HTML table row was being parsed.

Hybrid additionally reported unmet heating hours 3-5× below ground truth for the most important models (GreatFalls: 123.67 hr reported vs 433.33 hr actual). The pre-built `get_end_uses` tool was reading "During Occupied Heating" instead of "During Heating" — precisely the error it was designed to prevent.

## 4. Analysis

### 4.1 Win/Loss Summary

| Condition | 1st place finishes | 2nd place | Last place |
|---|---|---|---|
| **Prompt-Only** | **2** | 1 | 0 |
| **Pandas-Exec** | **1** | 1 | 0 |
| Vanilla | 0 | 1 | 1 |
| Hybrid | 0 | 0 | 2 |

### 4.2 What Worked

**Domain knowledge had the largest impact on accuracy.** The prompt-only condition — which had no MCP tools at all — won 2 of 3 prompts. Its advantage came from a 40-line domain guide covering:
- Unit conversions (J in SQL vs GJ in HTML)
- Metric disambiguation ("During Heating" vs "During Occupied Heating")
- File format patterns (`.dd.` files are design-day runs, not annual)
- Zone multiplier conventions

This knowledge prevented exactly the errors that the other conditions made.

**Server-side computation eliminated the timeseries ceiling.** In previous evaluations (before this experiment), MCP's `get_timeseries_report_by_rddid_list` tool truncated 8760-hour timeseries data at 10K characters, forcing Claude to guess or infer. The new `execute_pandas` tool solved this completely — Claude writes pandas code, the server executes it, and only the computed result is returned.

**The `execute_pandas` tool was fastest on the simple prompt.** At 77 seconds for Prompt 01, it beat all other conditions. Structured MCP queries avoid the overhead of writing, executing, and parsing shell commands.

### 4.3 What Didn't Work

**Pre-built aggregation tools hurt more than they helped.** The Hybrid condition's `get_end_uses` and `get_timeseries_stats` tools were designed as "accuracy guardrails" — pre-built functions that handle unit conversion and metric selection so Claude can't get them wrong. In practice:

| Intended benefit | Actual outcome |
|---|---|
| Prevent unit confusion | Tool returned values in the expected units, but from the wrong table row |
| Prevent metric confusion (occupied vs facility hours) | Tool itself read the wrong metric in at least one prompt |
| Reduce multi-model call overhead | Tool scanned all models eagerly, causing scope drift |

The fundamental problem: **pre-built tools bake in assumptions that may not match the question being asked.** When the tool's assumption is wrong, the error is invisible to Claude — it trusts the tool's output.

**MCP tool abstraction can hide errors.** When Claude writes a Python script via Bash, every step is visible in the conversation — the file path, the regex pattern, the column selection, the aggregation. When an MCP tool returns a value, the extraction logic is opaque. Both MCP conditions shared a cooling-value extraction error that would have been caught immediately in a visible script.

**More tools ≠ better results.** Hybrid had 10 tools available; Prompt-Only had 4 (Bash, Read, Grep, Glob). Prompt-Only scored higher on every prompt except the first. The additional tools added coordination overhead and decision complexity without improving output quality.

### 4.4 Speed vs. Accuracy Tradeoff

| Condition | Avg relative time | Avg relative accuracy |
|---|---|---|
| Prompt-Only | 1.0× (baseline) | Highest |
| Pandas-Exec | 0.9× (slightly faster) | High |
| Hybrid | 1.2× (slower) | Lowest |
| Vanilla | 1.5× (slowest) | Variable |

Pandas-Exec was the fastest overall, but only marginally faster than Prompt-Only. The speed advantage of MCP tools was most visible at scale (Prompt 04: 457s vs 898s for Vanilla) but smallest on simple queries (Prompt 01: 77s vs 91s for Vanilla).

## 5. Limitations

**Sample size.** Each condition was run once per prompt. LLM outputs are non-deterministic — a single run may not represent typical performance. A statistically rigorous evaluation would require multiple runs per condition.

**Grader bias.** The grading LLM may have systematic preferences (e.g., favoring longer responses, penalizing certain error types more than others). We mitigated this by providing ground truth values, but subjective dimensions like "Insight" are inherently judgment calls.

**Prompt sensitivity.** Results may differ with different prompt phrasings. Our prompts were designed to be tool-agnostic, but the MCP conditions may have performed differently with prompts specifically designed to leverage their tools.

**Weather file substitutions.** Three international models (Dubai, New Delhi, Ho Chi Minh City) used substitute weather files from nearby stations. Their simulation results differ slightly from the original HTML-only outputs.

**Tool-awareness confound.** In an initial round of testing, two conditions (Pandas-Exec and Prompt-Only) failed completely because Claude asked for tool permissions instead of using available tools. We added explicit system prompt instructions ("All tools are pre-approved, do not ask for permission") to fix this. This means our results partially reflect the quality of the system prompt, not just the tools.

## 6. Recommendations

Based on these results, the recommended architecture for an EnergyPlus MCP server is:

### Keep
- **`execute_pandas`** — the sandboxed pandas execution tool. It eliminates the timeseries data ceiling, enables arbitrary analysis queries, and was the fastest approach on simple prompts.
- **Discovery tools** (`initialize_model_map`, `get_available_models`) — structured model cataloging is faster than manual globbing.
- **HTML search tools** (`search_html_tables_by_keyword`, `get_html_table_by_tuple`) — useful for navigation, though not essential.
- **Domain knowledge in tool documentation** — the biggest accuracy lever. Merge the domain guide content (units, gotchas, common patterns) into `src/CLAUDE.md` so it's always available when the MCP server is active.

### Drop
- **Pre-built aggregation tools** (`get_end_uses`, `get_timeseries_stats`) — they introduce invisible assumptions and performed worst in every evaluation. Any aggregation can be done through `execute_pandas` with full visibility.

### Add
- **Expanded `src/CLAUDE.md`** — include unit reference tables, metric disambiguation rules, and common pandas patterns. This was the single highest-impact intervention in the evaluation.

## 7. Conclusion

The most effective approach to AI-assisted EnergyPlus analysis is not more tools — it's better context. A 40-line domain guide outperformed a sophisticated MCP toolset with pre-built aggregation on every dimension except speed.

That said, MCP tools are not without value. The `execute_pandas` sandbox solves a real architectural problem (the timeseries data ceiling) and was the fastest approach on simple queries. The combination of server-side computation + domain knowledge in tool documentation is likely the optimal configuration.

The key lesson: **tools that return answers are less trustworthy than tools that show their work.** In engineering analysis, a visible Python script that Claude writes and you can inspect is more valuable than an opaque tool that returns a number. The `execute_pandas` approach threads this needle — Claude writes the code (visible, auditable), but the server executes it (fast, no data ceiling).

---

## Appendix A: Tool Inventory

### Existing tools (kept)
| Tool | Purpose |
|---|---|
| `initialize_model_map(directory)` | Scan directory for EnergyPlus output files, build model catalog |
| `get_available_models()` | List all discovered models with IDs, file types, file paths |
| `search_html_tables_by_keyword(id, keywords)` | Find HTML report tables by keyword search |
| `get_html_table_by_tuple(id, query_tuple)` | Retrieve a specific HTML table by (report_for, report_name, table_name) |
| `get_sql_available_hourlies(id)` | List available hourly timeseries variables with RDD IDs |
| `get_eplus_object_schema(object_type)` | Look up EnergyPlus input object field definitions |

### New tool (added)
| Tool | Purpose |
|---|---|
| `execute_pandas(model_id, code)` | Execute Python/pandas code in a sandboxed environment against pre-loaded model DataFrames |

### Dropped tools
| Tool | Why dropped |
|---|---|
| `get_timeseries_report_by_rddid_list(model_id, rddid)` | Subsumed by `execute_pandas`. Hit 10K char ceiling on any 8760-hour variable. |
| `get_end_uses(model_ids, end_uses, sort_by)` | Pre-built aggregation caused invisible extraction errors. Use `execute_pandas` instead. |
| `get_timeseries_stats(model_id, rddid, agg)` | Pre-built aggregation added overhead without accuracy benefit. Use `execute_pandas` instead. |

## Appendix B: Sandbox Security Model

The `execute_pandas` tool runs user-generated code in a restricted Python environment:

| Layer | Mechanism |
|---|---|
| **AST validation** | Code is parsed before execution. `import`, `exec`, `eval`, `open`, and access to `__builtins__`, `__class__`, `__subclasses__` are rejected at the syntax level. |
| **Restricted namespace** | `__builtins__` is set to an empty dict. Only `pandas`, `numpy`, safe builtins (`len`, `range`, `min`, `max`, etc.), and pre-loaded DataFrames are available. |
| **Timeout** | 30-second execution limit via `signal.SIGALRM`. |
| **Output cap** | Results are serialized to JSON and capped at 50K characters. |
| **Threat model** | The MCP server runs as a subprocess of Claude Code in the user's terminal. Claude Code already has Bash access. The sandbox prevents accidental damage from generated code, not adversarial attack. |

## Appendix C: Reproduction

```bash
# Clone and set up
git clone https://github.com/michaelsweeney/eplusout-mcp.git
cd eplusout-mcp
uv sync

# Run evaluations (requires Claude Code CLI)
cd test_prompts

# Branch A: Pandas-Exec
git checkout experiment/pandas-exec
bash run_test.sh 01_cross_reference_meters pandas-exec

# Branch C: Prompt-Only
git checkout experiment/prompt-only
bash run_test.sh 01_cross_reference_meters prompt-only

# Grade
bash run_test.sh 01_cross_reference_meters grade
```

Branches: `experiment/pandas-exec`, `experiment/hybrid`, `experiment/prompt-only`
Eval runner: `test_prompts/run_test.sh`
Ground truth: `test_prompts/expected/*.json`
