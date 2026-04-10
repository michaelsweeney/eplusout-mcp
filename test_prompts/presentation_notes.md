# SimBuild Presentation Notes — Retrospective

**Date**: 2026-04-10
**Context**: Paper is locked. Presentation should cover what we did, then spend time on a retrospective of what changed and what we learned.

## Narrative Arc

1. **"We built an MCP server for EnergyPlus results analysis"** — the paper
2. **"Claude Code changed the game"** — agents can now do raw file access as well as our tools
3. **"MCP's real value isn't wrapping file access — it's composing simulation workflows"** — the vision
4. **"MCP is a distribution mechanism for domain expertise, not a capability improvement"** — the honest takeaway

## Key Eval Findings

- **Full matrix**: 4 prompts × 4 modes × 3 models = 48 runs, all completed
- **Ghost tools**: `execute_pandas`, `get_end_uses`, `get_timeseries_stats` were referenced in the eval but never merged to main — MCP modes degraded to basic discovery + HTML tools
- **Result**: MCP is best-case marginally better than prompt-only, and often worse
- **Domain knowledge (prompt-only) was the real lever**, not tool wrappers
- **Pre-built aggregation tools hurt more than helped** — opaque tools introduced invisible extraction errors

## Why MCP Tools Didn't Add Value (for results analysis)

The MCP tools being tested were thin wrappers around file access:
- Discovery tools (`initialize_model_map`, `get_available_models`) → same as `ls` + `find`
- HTML tools (`search_html_tables_by_keyword`, `get_html_table_by_tuple`) → same as `grep` + `python3 bs4`
- `execute_pandas` (never merged) → same as `python3 -c "..."` via Bash — data never enters conversation context either way

Claude Code with Bash/Read/Grep/Glob can do everything these tools do, often more flexibly.

## The `execute_pandas` Question

`execute_pandas` was the highest-value tool candidate — server-side pandas execution. But Claude Code can write and run Python scripts directly via Bash with the same architectural benefit (data stays server-side, only results return). Any online server could expose a generic sandboxed query environment via API and Claude Code could use it just as effectively.

## Where MCP IS Genuinely Valuable

### What prompts fundamentally cannot do:
1. **Shared mutable state** — a server tracking queued/running/complete simulations across multiple users/sessions
2. **Compute the agent doesn't have** — if EnergyPlus isn't installed locally, no prompting helps. The MCP server *is* the compute.
3. **Guardrailed mutations** — curated modification tools (debatable — eval showed pre-built tools also introduce errors)

### The real pitch: MCP as distribution mechanism
- For a single expert user with Claude Code + EnergyPlus installed → prompts win on flexibility
- For an organization deploying to 50 engineers who don't write their own domain guides → MCP wins on packaging
- **MCP packages domain expertise into a reusable server** instead of requiring every user to write their own prompt

## Ecosystem Composition — The Compelling Vision

Three MCP servers from different organizations, composing a full workflow:

| Layer | Server | Maintainer | Role |
|-------|--------|------------|------|
| Design operations | OpenStudio MCP | NREL / community | Measures, ASHRAE 90.1 baselines, high-level model transforms |
| Simulation execution | EnergyPlus-MCP | LBNL-ETA | Load/validate/modify IDF, run simulations, HVAC topology |
| Results analysis + QC | eplusout-mcp | Ours | Cross-model comparison, timeseries extraction, QC checks |

**Example composed workflow:**
1. [OpenStudio MCP] Generate Appendix G baseline using System 7
2. [OpenStudio MCP] Apply proposed design measures
3. [EnergyPlus MCP] Run both baseline + proposed simulations
4. [Results MCP] Compare end uses, check heating/cooling deltas
5. [Results MCP] QC — flag anomalous values before reporting

This is genuinely hard without a standardized protocol — three servers from different orgs, different tech stacks, composing seamlessly because MCP standardizes tool discovery and invocation.

### LBNL EnergyPlus-MCP vs Our Server

| | LBNL EnergyPlus-MCP | Our eplusout-mcp |
|---|---|---|
| **Domain** | Model authoring + simulation execution | Results analysis |
| **File types** | IDF (input), EPW (weather) | .htm, .sql, .epJSON (outputs) |
| **Can run EnergyPlus?** | Yes | No |
| **Can modify models?** | Yes (35 tools) | No (read-only) |
| **Can analyze results?** | Basic (plots) | Deep (timeseries, HTML, cross-model) |

They work on the INPUT side; we work on the OUTPUT side. Complementary, not competing.

## QC Angle

- Scientific domain — accuracy is critical
- **Fundamental tension**: tools that hide complexity are anti-QC
- A visible Python script that Claude writes is more auditable than an opaque tool returning `{"qc_status": "pass"}`
- The eval's pre-built `get_end_uses` tool read "During Occupied Heating" instead of "During Heating" — exactly the kind of invisible error QC should catch, not introduce
- **For QC, auditability beats convenience** — you want to see the check, not trust the tool

## Pie-in-the-Sky: Simulation-in-the-Loop Design

The most compelling MCP use case is NOT reading results — it's **running simulations iteratively**:
- Claude modifies model → triggers simulation via MCP → analyzes results → iterates
- Parametric optimization, weather sensitivity, retrofit sequencing
- Requires compute orchestration (HPC job queuing, parallel runs, result indexing)
- This is impossible with just file access — the MCP server IS the infrastructure

## Devil's Advocate: Can't This All Be Prompts?

Almost all of it can. One long system prompt with domain guides for EnergyPlus, OpenStudio, and results parsing. Claude writes scripts to do everything.

**What you lose**: packaging, standardization, shared state, compute access.
**What you keep**: flexibility, auditability, no tool overhead.

MCP's value over long prompts is **deployment convenience and ecosystem standardization**, not capability. It's the difference between requiring every user to be an expert vs packaging expertise into a reusable server.
