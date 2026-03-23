# MCP Tool Evaluation Prompts

Compare how Claude performs EnergyPlus analysis **with** vs **without** the MCP eplus_outputs tools.

## Setup

Requires [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) with the `eplus_outputs` MCP server configured.

For prompt 03 (multi-model), generate the test models first:

```bash
./setup_models.sh
```

## Usage

```bash
# Run a single prompt with MCP tools
./run_test.sh 01_cross_reference_meters with-mcp

# Run without MCP tools (Bash/Read/Grep/Glob only)
./run_test.sh 01_cross_reference_meters without-mcp

# Run both back-to-back
./run_test.sh 01_cross_reference_meters both

# Grade the results against ground truth
./run_test.sh 01_cross_reference_meters grade

# Use a different model
MODEL=opus ./run_test.sh 02_unmet_hours_investigation both
```

## Prompts

| Prompt | Models | Tools tested | Cross-reference? |
|--------|--------|-------------|-----------------|
| `01_cross_reference_meters` | 2 | All 6 | SQL annual sums vs HTML End Uses totals |
| `02_unmet_hours_investigation` | 2 | All 6 | Unmet hours (HTML) + boiler timeseries (SQL) + zone sizing (HTML) |
| `03_multi_model_comparison` | 20 | All 6 | Heating/cooling ranking + unmet hours + SQL timeseries across many models |

## Structure

```
test_prompts/
├── prompts/           # Prompt text (input to Claude)
├── expected/          # Ground truth JSON (for grading)
├── results/           # Captured outputs and grade reports (gitignored)
├── models/            # 20 test models for prompt 03 (gitignored, use setup_models.sh)
├── run_test.sh        # Test runner
├── setup_models.sh    # Generate test models from available source simulations
└── README.md
```

## What gets compared

The grader scores each response on:
- **Correctness** — do values match ground truth?
- **Completeness** — were all prompt steps addressed?
- **Efficiency** — direct approach vs thrashing/retries?
- **Insight** — useful interpretation beyond raw numbers?
- **Graceful degradation** — how missing data was handled
