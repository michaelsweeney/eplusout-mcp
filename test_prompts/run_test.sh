#!/usr/bin/env bash
set -euo pipefail

# ─── Config ──────────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PROMPTS_DIR="$SCRIPT_DIR/prompts"
EXPECTED_DIR="$SCRIPT_DIR/expected"
RESULTS_DIR="$SCRIPT_DIR/results"
MODEL="${MODEL:-sonnet}"

# MCP tools — must match the tool names Claude Code registers for this server
MCP_TOOLS="mcp__eplus_outputs__initialize_model_map"
MCP_TOOLS+=",mcp__eplus_outputs__get_available_models"
MCP_TOOLS+=",mcp__eplus_outputs__search_html_tables_by_keyword"
MCP_TOOLS+=",mcp__eplus_outputs__get_html_table_by_tuple"
MCP_TOOLS+=",mcp__eplus_outputs__get_sql_available_hourlies"
MCP_TOOLS+=",mcp__eplus_outputs__get_timeseries_report_by_rddid_list"

# ─── Usage ───────────────────────────────────────────────────────────────────
usage() {
    cat <<EOF
Usage: $0 <prompt_name> <mode>

Modes:
  with-mcp       Run with MCP eplus_outputs tools + Bash/Read/Grep/Glob
  without-mcp    Run with only Bash/Read/Grep/Glob (must parse files raw)
  both           Run both modes sequentially
  grade          Grade existing results against expected answers

Options (via env vars):
  MODEL=sonnet   Claude model to use (sonnet, opus, haiku)

Available prompts:
$(ls "$PROMPTS_DIR"/*.md 2>/dev/null | xargs -I{} basename {} .md | sed 's/^/  /')

Examples:
  $0 01_cross_reference_meters both
  $0 02_unmet_hours_investigation with-mcp
  MODEL=opus $0 01_cross_reference_meters both
  $0 01_cross_reference_meters grade
EOF
    exit 1
}

[[ $# -lt 2 ]] && usage

PROMPT_NAME="$1"
MODE="$2"
PROMPT_FILE="$PROMPTS_DIR/${PROMPT_NAME}.md"
EXPECTED_FILE="$EXPECTED_DIR/${PROMPT_NAME}.json"

[[ ! -f "$PROMPT_FILE" ]] && echo "Error: prompt not found: $PROMPT_FILE" && exit 1

mkdir -p "$RESULTS_DIR"

# ─── Run functions ───────────────────────────────────────────────────────────
run_with_mcp() {
    local outfile="$RESULTS_DIR/${PROMPT_NAME}_mcp_${MODEL}.md"
    local timefile="$RESULTS_DIR/${PROMPT_NAME}_mcp_${MODEL}.time"
    echo "╔══════════════════════════════════════════════════╗"
    echo "║  WITH MCP tools │ model=$MODEL"
    echo "╚══════════════════════════════════════════════════╝"
    echo ""

    TIMEFORMAT='%R'
    { time claude -p "$(cat "$PROMPT_FILE")" \
        --model "$MODEL" \
        --allowedTools "$MCP_TOOLS,Bash,Read,Grep,Glob" \
        --output-format text \
        --cwd "$REPO_DIR" \
        > "$outfile" 2>&1 ; } 2> "$timefile"

    echo "  Output:    $outfile"
    echo "  Wall time: $(cat "$timefile")s"
    echo ""
}

run_without_mcp() {
    local outfile="$RESULTS_DIR/${PROMPT_NAME}_raw_${MODEL}.md"
    local timefile="$RESULTS_DIR/${PROMPT_NAME}_raw_${MODEL}.time"
    echo "╔══════════════════════════════════════════════════╗"
    echo "║  WITHOUT MCP tools │ model=$MODEL"
    echo "╚══════════════════════════════════════════════════╝"
    echo ""

    TIMEFORMAT='%R'
    { time claude -p "$(cat "$PROMPT_FILE")" \
        --model "$MODEL" \
        --allowedTools "Bash,Read,Grep,Glob" \
        --output-format text \
        --cwd "$REPO_DIR" \
        > "$outfile" 2>&1 ; } 2> "$timefile"

    echo "  Output:    $outfile"
    echo "  Wall time: $(cat "$timefile")s"
    echo ""
}

grade() {
    local mcp_file="$RESULTS_DIR/${PROMPT_NAME}_mcp_${MODEL}.md"
    local raw_file="$RESULTS_DIR/${PROMPT_NAME}_raw_${MODEL}.md"
    local mcp_time="$RESULTS_DIR/${PROMPT_NAME}_mcp_${MODEL}.time"
    local raw_time="$RESULTS_DIR/${PROMPT_NAME}_raw_${MODEL}.time"
    local grade_out="$RESULTS_DIR/${PROMPT_NAME}_grade_${MODEL}.md"

    [[ ! -f "$EXPECTED_FILE" ]] && echo "Error: expected answers not found: $EXPECTED_FILE" && exit 1

    # At least one result must exist
    if [[ ! -f "$mcp_file" ]] && [[ ! -f "$raw_file" ]]; then
        echo "Error: no results to grade. Run 'with-mcp' or 'without-mcp' first."
        exit 1
    fi

    local mcp_content raw_content mcp_wall raw_wall
    mcp_content="$(cat "$mcp_file" 2>/dev/null || echo "[not yet run]")"
    raw_content="$(cat "$raw_file" 2>/dev/null || echo "[not yet run]")"
    mcp_wall="$(cat "$mcp_time" 2>/dev/null || echo "N/A")"
    raw_wall="$(cat "$raw_time" 2>/dev/null || echo "N/A")"

    local grade_prompt
    grade_prompt="$(cat <<GRADEEOF
You are grading two AI responses to the same EnergyPlus analysis prompt.
Both were given the same task but different toolsets:
- Response A ("MCP") had specialized EnergyPlus MCP tools + Bash/Read/Grep/Glob. Wall time: ${mcp_wall}s
- Response B ("Raw") had only Bash, Read, Grep, and Glob. Wall time: ${raw_wall}s

## Expected Answers (ground truth)
\`\`\`json
$(cat "$EXPECTED_FILE")
\`\`\`

## The Original Prompt
$(cat "$PROMPT_FILE")

## Response A — WITH MCP tools
${mcp_content}

## Response B — WITHOUT MCP tools
${raw_content}

## Grading Instructions

Score each response on these dimensions (1-5 scale, 5 = best):

| Dimension | What to evaluate |
|-----------|-----------------|
| **Correctness** | Do reported values match expected answers exactly? (most important) |
| **Completeness** | Were all parts of the prompt addressed? |
| **Efficiency** | Was the approach direct, or did it thrash/retry/take unnecessary steps? |
| **Insight** | Did the response add useful interpretation beyond raw numbers? |
| **Graceful degradation** | When data was missing, did it explain what was needed and why? |

For each dimension, give a score and a one-line justification for each response.

Then provide:
1. A summary comparison table
2. An overall verdict: which approach was better and why
3. Any observations about what the MCP tools helped with (or didn't)
GRADEEOF
)"

    echo "╔══════════════════════════════════════════════════╗"
    echo "║  GRADING │ model=$MODEL"
    echo "╚══════════════════════════════════════════════════╝"
    echo ""

    claude -p "$grade_prompt" \
        --model "$MODEL" \
        --output-format text \
        > "$grade_out" 2>&1

    echo "  Grade report: $grade_out"
    echo ""
    cat "$grade_out"
}

# ─── Main ────────────────────────────────────────────────────────────────────
case "$MODE" in
    with-mcp)     run_with_mcp ;;
    without-mcp)  run_without_mcp ;;
    both)         run_with_mcp; run_without_mcp ;;
    grade)        grade ;;
    *)            usage ;;
esac

echo ""
echo "Done. Results in $RESULTS_DIR/"
