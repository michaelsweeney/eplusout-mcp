# EnergyPlus Output Tools for Agentic Development

AI-assisted analysis of EnergyPlus building energy simulation results. This was initially developed as an MCP Server, but a prompt tool environemnt was added in light of recent advances in Claude Code -- and to serve as a second methodology to benchmark and test against.

| Approach | Best for | What you need |
|---|---|---|
| **[Prompt Tools](#prompt-tools-local)** | Local files on your machine | An AI coding agent (e.g., Claude Code) |
| **[MCP Server](#mcp-server-remote)** | Remote files, hosted services, shared data | Any MCP-compatible client + server |

Both share the same domain knowledge — EnergyPlus file formats, unit conventions, parsing logic, and common gotchas.

## Prompt Tools (Local)

**No server required.** Your AI agent parses EnergyPlus output files directly using Bash, Python, and SQLite, guided by domain knowledge and vetted snippets.

### Setup

Copy or symlink the `claude-tools/` directory into your project:

```bash
# Option 1: Symlink into a project's .claude directory
ln -s /path/to/eplusout-mcp/claude-tools /path/to/your-project/.claude/eplus

# Option 2: Symlink globally for all projects
ln -s /path/to/eplusout-mcp/claude-tools ~/.claude/eplus
```

Or just open your AI coding agent from this repo's root — it will pick up `claude-tools/CLAUDE.md` automatically.

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

The agent will use the parsing snippets and domain knowledge from `CLAUDE.md` (unit conversions, metric disambiguation, etc.).

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
- An MCP-compatible client (e.g., [Claude Desktop](https://claude.ai/download), [Claude Code](https://docs.anthropic.com/en/docs/claude-code), or any [MCP client](https://modelcontextprotocol.io/clients))

### Install

```bash
git clone https://github.com/michaelsweeney/eplusout-mcp.git
cd eplusout-mcp
uv sync
```

### Configure Your MCP Client

The server runs via `uv run main.py`. Configure it in your MCP client of choice:

**Claude Desktop** — Open your config file (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS, `%APPDATA%\Claude\claude_desktop_config.json` on Windows, `~/.config/Claude/claude_desktop_config.json` on Linux):

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

**Claude Code:**

```bash
claude mcp add eplus_outputs -- uv --directory /path/to/eplusout-mcp run main.py
```

**Other MCP clients** — Point your client at the command `uv --directory /path/to/eplusout-mcp run main.py` using stdio transport.

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

The core analysis tool. The AI agent writes Python/pandas code; the server executes it in a sandboxed environment against pre-loaded DataFrames.

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
| `.csv` | Timestep-level output variables (if requested in IDF) | Read with pandas |
| `.eio` | Simulation initialization summary | Read directly |
| `.mdd` | Meter Data Dictionary (available meter variables) | Read directly |

EnergyPlus can produce additional output files depending on simulation settings (`.dxf` geometry, `.ssz`/`.zsz` sizing details, `.mtd` meter details, etc.). Support for new file types can be added by creating a parser in `src/tools/` for the MCP server pathway or a snippet in `claude-tools/snippets/` for the prompt-based pathway.

## Testing

```bash
uv run pytest
```

## Evaluation

We ran a [controlled evaluation](docs/eval-results-2026-03-22.md) comparing four approaches across 3 prompts of increasing complexity (2-model cross-reference, unmet hours investigation, 20-model batch analysis).

### Results summary

| Approach | Avg score | Best at |
|---|---|---|
| **Prompt-only** (domain guide + Bash/Python) | Highest | Accuracy, insight, completeness |
| **Pandas-exec** (MCP + `execute_pandas`) | Close second | Speed, structured data access |
| **Vanilla** (no tools, no guide) | Variable | Simple queries |
| **Hybrid** (MCP + pre-built aggregation) | Lowest | — |

**The prompt-based approach matched or outperformed MCP on accuracy in every evaluation.** Domain knowledge — knowing which HTML row to parse, which unmet-hours column to use, how to convert units — had a larger impact on correctness than the tool mechanism.

### When MCP adds value

Despite the prompt approach's strong showing on local file analysis, the MCP server has distinct advantages in other contexts:

| Advantage | Why it matters |
|---|---|
| **Remote data access** | When simulation files live on a server, cloud storage, or shared drive that the agent can't reach via Bash. MCP is the only path to the data. |
| **Server-side computation** | The `execute_pandas` sandbox runs pandas code without transferring 8760-hour datasets to the conversation. Essential for large models or slow connections. |
| **Controlled execution environment** | Organizations can deploy the MCP server with specific data access policies, audit logging, and sandboxing — rather than giving the agent direct filesystem access. |
| **Multi-user / hosted workflows** | A single MCP server can serve multiple users analyzing the same simulation library, without each user needing local copies. |
| **Consistent tool interface** | MCP tools provide a stable API regardless of how files are organized on disk. File naming conventions, directory structures, and OS differences are handled by the server. |

### Recommendation

- **Local analysis?** Start with `claude-tools/` (prompt approach). It's simpler, fully transparent, and produces the most accurate results.
- **Building a service or working with remote data?** Use the MCP server with `execute_pandas`. Merge the domain guide content into `src/CLAUDE.md` for best results.

Full methodology, per-prompt breakdowns, and raw scores: [docs/eval-results-2026-03-22.md](docs/eval-results-2026-03-22.md)

## License

MIT
