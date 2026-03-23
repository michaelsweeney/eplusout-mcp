# EnergyPlus Output Tools for Claude

AI-assisted analysis of EnergyPlus building energy simulation results. Two approaches, one repo:

| Approach | Best for | What you need |
|---|---|---|
| **[Prompt Tools](#prompt-tools-local)** | Local files on your machine | Claude Code |
| **[MCP Server](#mcp-server-remote)** | Remote files, hosted services, shared data | Claude Desktop or Claude Code + server |

Both share the same domain knowledge — EnergyPlus file formats, unit conventions, parsing logic, and common gotchas.

## Prompt Tools (Local)

**No server required.** Claude Code parses EnergyPlus output files directly using Bash, Python, and SQLite, guided by domain knowledge and vetted snippets.

### Setup

Copy or symlink the `claude-tools/` directory into your project:

```bash
# Option 1: Symlink into a project's .claude directory
ln -s /path/to/eplusout-mcp/claude-tools /path/to/your-project/.claude/eplus

# Option 2: Symlink globally for all projects
ln -s /path/to/eplusout-mcp/claude-tools ~/.claude/eplus
```

Or just open Claude Code from this repo's root — it will pick up `claude-tools/CLAUDE.md` automatically.

### What's included

```
claude-tools/
├── CLAUDE.md              # Domain guide: file formats, units, gotchas, SQL schema
├── commands/
│   ├── eplus-scan.md      # /eplus-scan — discover models in a directory
│   └── eplus-check.md     # /eplus-check — health check (errors, unmet hours, sizing)
└── snippets/
    ├── parse_end_uses.py   # Parse HTML End Uses table
    ├── query_timeseries.py # Query SQL hourly timeseries
    └── unmet_hours.py      # Extract unmet setpoint hours
```

### Slash Commands

| Command | What it does |
|---|---|
| `/eplus-scan <directory>` | Discover models, list file types, flag design-day runs, check for fatal errors |
| `/eplus-check <directory or model>` | Health check — error log review, unmet hours vs ASHRAE 300-hr threshold, energy sanity, sizing alerts |

### Usage

Scan a directory to see what you're working with:

> `/eplus-scan ./output/`

Check model health:

> `/eplus-check ./output/`

Then ask questions naturally:

> "Compare heating loads across all models and identify any with unmet hours."

Claude will use the parsing snippets and domain knowledge from `CLAUDE.md` (unit conversions, metric disambiguation, etc.).

### When to use this

- EnergyPlus output files are on your local machine
- You want full visibility into the analysis (every Python script is in the conversation)
- You're doing ad-hoc analysis or exploring results interactively

---

## MCP Server (Remote)

A [Model Context Protocol](https://modelcontextprotocol.io/) server that provides structured access to EnergyPlus output data. Includes a sandboxed pandas execution environment for server-side computation.

### When to use this

- Output files are on a remote server, cloud storage, or shared drive
- You're building a hosted service where users don't have direct file access
- You need server-side computation (e.g., aggregating 8760-hour timeseries without transferring all the data)

### Prerequisites

- [uv](https://docs.astral.sh/uv/getting-started/installation/) (Python package manager)
- [Claude Desktop](https://claude.ai/download) or [Claude Code](https://docs.anthropic.com/en/docs/claude-code)

### Install

```bash
git clone https://github.com/michaelsweeney/eplusout-mcp.git
cd eplusout-mcp
uv sync
```

### Configure Claude Desktop

Open your Claude Desktop config file:

| OS | Config file location |
|---|---|
| macOS | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Windows | `%APPDATA%\Claude\claude_desktop_config.json` |
| Linux | `~/.config/Claude/claude_desktop_config.json` |

Add the server entry:

```json
{
  "mcpServers": {
    "eplus_outputs": {
      "command": "uv",
      "args": ["--directory", "/path/to/eplusout-mcp", "run", "main.py"]
    }
  }
}
```

### Configure Claude Code

```bash
claude mcp add eplus_outputs -- uv --directory /path/to/eplusout-mcp run main.py
```

### Available Tools

#### Discovery
| Tool | Purpose |
|---|---|
| `initialize_model_map(directory)` | Scan directory for EnergyPlus files, build model catalog |
| `get_available_models()` | List all models with IDs, file types, file paths |

#### HTML Reports
| Tool | Purpose |
|---|---|
| `search_html_tables_by_keyword(id, keywords)` | Find tables by keyword |
| `get_html_table_by_tuple(id, query_tuple)` | Retrieve a specific table |

#### Timeseries
| Tool | Purpose |
|---|---|
| `get_sql_available_hourlies(id)` | List available hourly variables with RDD IDs |
| `execute_pandas(model_id, code)` | Run pandas code against pre-loaded DataFrames |

#### Schema
| Tool | Purpose |
|---|---|
| `get_eplus_object_schema(object_type)` | Look up EnergyPlus object field definitions |

### The `execute_pandas` Tool

The core analysis tool. Claude writes Python/pandas code; the server executes it in a sandboxed environment against pre-loaded DataFrames.

**Available variables in the sandbox:**
- `sql_ts` — DataFrame with hourly timeseries (datetime index, columns named `"{KeyValue}:{Name} [{Units}]"`)
- `html_tables` — Dict of `{(report_for, report_name, table_name): DataFrame}`
- `model_info` — Dict with model metadata
- `pd` — pandas, `np` — numpy

**Security:** No filesystem, network, or import access. AST-validated before execution. 30-second timeout. [Details →](docs/eval-results-2026-03-22.md#appendix-b-sandbox-security-model)

**Example:**
```python
# Annual electricity in GJ
sql_ts["None:Electricity:Facility [J]"].sum() / 1e9

# Peak cooling day — 24-hour profile
col = [c for c in sql_ts.columns if "Cooling" in c][0]
peak = sql_ts[col].idxmax()
sql_ts.loc[peak.normalize():peak.normalize() + pd.Timedelta(hours=23), col]
```

### Workflow

```
1. initialize_model_map(directory)        → scan for models
2. get_available_models()                 → get model IDs
3. search_html_tables_by_keyword(...)     → find relevant tables
4. execute_pandas(model_id, code)         → analyze data
```

---

## File Structure

```
eplusout-mcp/
├── claude-tools/           # Prompt-based tools (local use)
│   ├── CLAUDE.md           # Domain guide
│   └── snippets/           # Vetted Python parsing functions
├── src/                    # MCP server (hosted/remote use)
│   ├── server.py           # MCP tool definitions
│   ├── sandbox.py          # Sandboxed code execution
│   ├── data_loader.py      # DataFrame construction + caching
│   ├── model_data.py       # Model discovery
│   ├── monitor.py          # Logging
│   ├── CLAUDE.md           # MCP tool documentation (served as resource)
│   └── tools/              # File format handlers
├── tests/                  # Pytest test suite
├── example-files/          # Sample EnergyPlus outputs
├── docs/                   # Evaluation reports and specs
├── schema/                 # EnergyPlus JSON schema files
└── test_prompts/           # Eval framework for comparing approaches
```

## EnergyPlus File Types

Each simulation produces output files grouped by filename stem:

| Extension | Contents | Access method |
|---|---|---|
| `.epJSON` | Input model definition (geometry, HVAC, schedules) | Read directly (JSON) |
| `.sql` | SQLite results database (hourly timeseries, tabular data) | `execute_pandas` or `sqlite3` |
| `.table.htm` | HTML summary reports (end uses, sizing, unmet hours) | `search_html_tables_by_keyword` or parse with Python |
| `.err` | Error/warning log | Read directly |
| `.rdd` | Report Data Dictionary (lists available output variables) | Read directly |

## Testing

```bash
uv run pytest
```

## Evaluation

We ran a [controlled evaluation](docs/eval-results-2026-03-22.md) comparing four approaches: MCP with pandas execution, MCP with pre-built aggregation, prompt-only with domain guide, and vanilla (no tools, no guide). Key finding: **domain knowledge had the largest impact on accuracy; server-side computation via `execute_pandas` was fastest.**

## License

MIT
