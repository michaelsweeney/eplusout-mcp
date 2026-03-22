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

# For pandas-exec mode: discovery + HTML + execute_pandas
MCP_TOOLS_PANDAS="mcp__eplus_outputs__initialize_model_map"
MCP_TOOLS_PANDAS+=",mcp__eplus_outputs__get_available_models"
MCP_TOOLS_PANDAS+=",mcp__eplus_outputs__search_html_tables_by_keyword"
MCP_TOOLS_PANDAS+=",mcp__eplus_outputs__get_html_table_by_tuple"
MCP_TOOLS_PANDAS+=",mcp__eplus_outputs__get_sql_available_hourlies"
MCP_TOOLS_PANDAS+=",mcp__eplus_outputs__execute_pandas"

# For hybrid mode: pandas-exec tools + pre-built aggregation tools
MCP_TOOLS_HYBRID="$MCP_TOOLS_PANDAS"
MCP_TOOLS_HYBRID+=",mcp__eplus_outputs__get_end_uses"
MCP_TOOLS_HYBRID+=",mcp__eplus_outputs__get_timeseries_stats"

# ─── Usage ───────────────────────────────────────────────────────────────────
usage() {
    cat <<EOF
Usage: $0 <prompt_name> <mode>

Modes:
  vanilla        Bash/Read/Grep/Glob only, no MCP, no domain knowledge
  pandas-exec    MCP tools (discovery + HTML + execute_pandas) + Bash/Read/Grep/Glob
  hybrid         MCP tools (pandas-exec + get_end_uses + get_timeseries_stats) + Bash/Read/Grep/Glob
  prompt-only    Bash/Read/Grep/Glob only, no MCP, but with EnergyPlus domain guide as system prompt
  all            Run all 4 modes sequentially
  grade          Grade all available results against expected answers

  Backward-compat aliases:
  with-mcp       Alias for pandas-exec
  without-mcp    Alias for vanilla
  both           Alias for: vanilla then pandas-exec

Options (via env vars):
  MODEL=sonnet   Claude model to use (sonnet, opus, haiku)

Available prompts:
$(ls "$PROMPTS_DIR"/*.md 2>/dev/null | xargs -I{} basename {} .md | sed 's/^/  /')

Examples:
  $0 01_cross_reference_meters all
  $0 02_unmet_hours_investigation hybrid
  MODEL=opus $0 01_cross_reference_meters pandas-exec
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

run_vanilla() {
    local outfile="$RESULTS_DIR/${PROMPT_NAME}_vanilla_${MODEL}.md"
    local timefile="$RESULTS_DIR/${PROMPT_NAME}_vanilla_${MODEL}.time"
    echo "╔══════════════════════════════════════════════════╗"
    echo "║  VANILLA (no MCP, no domain guide) │ model=$MODEL"
    echo "╚══════════════════════════════════════════════════╝"
    echo ""

    TIMEFORMAT='%R'
    { time ( cd "$REPO_DIR" && claude -p "$(cat "$PROMPT_FILE")" \
        --model "$MODEL" \
        --allowedTools "Bash,Read,Grep,Glob" \
        --append-system-prompt "You do NOT have EnergyPlus MCP tools. Parse HTML files and query SQLite databases directly using Bash, Read, Grep, and Glob. Use python3 or sqlite3 CLI for database queries. Use python3 or grep/sed for HTML parsing." \
        --output-format text \
        > "$outfile" 2>&1 ) || true ; } 2> "$timefile"

    echo "  Output:    $outfile"
    echo "  Wall time: $(cat "$timefile")s"
    [[ ! -s "$outfile" ]] && echo "  WARNING: output file is empty — claude may have crashed"
    echo ""
}

run_pandas_exec() {
    local outfile="$RESULTS_DIR/${PROMPT_NAME}_pandas-exec_${MODEL}.md"
    local timefile="$RESULTS_DIR/${PROMPT_NAME}_pandas-exec_${MODEL}.time"
    echo "╔══════════════════════════════════════════════════╗"
    echo "║  PANDAS-EXEC (MCP + execute_pandas) │ model=$MODEL"
    echo "╚══════════════════════════════════════════════════╝"
    echo ""

    TIMEFORMAT='%R'
    { time ( cd "$REPO_DIR" && claude -p "$(cat "$PROMPT_FILE")" \
        --model "$MODEL" \
        --allowedTools "$MCP_TOOLS_PANDAS,Bash,Read,Grep,Glob" \
        --append-system-prompt "You have EnergyPlus MCP tools available including execute_pandas for running pandas code against model data. Use these tools directly — do NOT ask for permission, do NOT ask the user to approve tools. All tools listed in --allowedTools are pre-approved. If an MCP tool call fails, fall back to Bash/Read/Grep/Glob." \
        --output-format text \
        > "$outfile" 2>&1 ) || true ; } 2> "$timefile"

    echo "  Output:    $outfile"
    echo "  Wall time: $(cat "$timefile")s"
    [[ ! -s "$outfile" ]] && echo "  WARNING: output file is empty — claude may have crashed"
    echo ""
}

run_hybrid() {
    local outfile="$RESULTS_DIR/${PROMPT_NAME}_hybrid_${MODEL}.md"
    local timefile="$RESULTS_DIR/${PROMPT_NAME}_hybrid_${MODEL}.time"
    echo "╔══════════════════════════════════════════════════╗"
    echo "║  HYBRID (MCP + aggregation tools) │ model=$MODEL"
    echo "╚══════════════════════════════════════════════════╝"
    echo ""

    TIMEFORMAT='%R'
    { time ( cd "$REPO_DIR" && claude -p "$(cat "$PROMPT_FILE")" \
        --model "$MODEL" \
        --allowedTools "$MCP_TOOLS_HYBRID,Bash,Read,Grep,Glob" \
        --append-system-prompt "You have EnergyPlus MCP tools available including execute_pandas, get_end_uses, and get_timeseries_stats. Use these tools directly — do NOT ask for permission, do NOT ask the user to approve tools. All tools listed in --allowedTools are pre-approved. If an MCP tool call fails, fall back to Bash/Read/Grep/Glob." \
        --output-format text \
        > "$outfile" 2>&1 ) || true ; } 2> "$timefile"

    echo "  Output:    $outfile"
    echo "  Wall time: $(cat "$timefile")s"
    [[ ! -s "$outfile" ]] && echo "  WARNING: output file is empty — claude may have crashed"
    echo ""
}

run_prompt_only() {
    local outfile="$RESULTS_DIR/${PROMPT_NAME}_prompt-only_${MODEL}.md"
    local timefile="$RESULTS_DIR/${PROMPT_NAME}_prompt-only_${MODEL}.time"
    echo "╔══════════════════════════════════════════════════╗"
    echo "║  PROMPT-ONLY (no MCP, with domain guide) │ model=$MODEL"
    echo "╚══════════════════════════════════════════════════╝"
    echo ""

    local domain_guide="$SCRIPT_DIR/domain_guide.md"
    [[ ! -f "$domain_guide" ]] && echo "Error: domain guide not found: $domain_guide" && exit 1

    TIMEFORMAT='%R'
    { time ( cd "$REPO_DIR" && claude -p "$(cat "$PROMPT_FILE")" \
        --model "$MODEL" \
        --allowedTools "Bash,Read,Grep,Glob" \
        --append-system-prompt "You do NOT have EnergyPlus MCP tools. Parse HTML files and query SQLite databases directly using Bash, Read, Grep, and Glob. Use python3 or sqlite3 CLI for database queries. Use python3 or grep/sed for HTML parsing. Do NOT ask for MCP tool permissions — you don't have them. Here is a domain guide to help:

$(cat "$domain_guide")" \
        --output-format text \
        > "$outfile" 2>&1 ) || true ; } 2> "$timefile"

    echo "  Output:    $outfile"
    echo "  Wall time: $(cat "$timefile")s"
    [[ ! -s "$outfile" ]] && echo "  WARNING: output file is empty — claude may have crashed"
    echo ""
}

grade() {
    local vanilla_file="$RESULTS_DIR/${PROMPT_NAME}_vanilla_${MODEL}.md"
    local pandas_file="$RESULTS_DIR/${PROMPT_NAME}_pandas-exec_${MODEL}.md"
    local hybrid_file="$RESULTS_DIR/${PROMPT_NAME}_hybrid_${MODEL}.md"
    local prompt_only_file="$RESULTS_DIR/${PROMPT_NAME}_prompt-only_${MODEL}.md"
    local vanilla_time="$RESULTS_DIR/${PROMPT_NAME}_vanilla_${MODEL}.time"
    local pandas_time="$RESULTS_DIR/${PROMPT_NAME}_pandas-exec_${MODEL}.time"
    local hybrid_time="$RESULTS_DIR/${PROMPT_NAME}_hybrid_${MODEL}.time"
    local prompt_only_time="$RESULTS_DIR/${PROMPT_NAME}_prompt-only_${MODEL}.time"
    local grade_out="$RESULTS_DIR/${PROMPT_NAME}_grade_${MODEL}.md"

    [[ ! -f "$EXPECTED_FILE" ]] && echo "Error: expected answers not found: $EXPECTED_FILE" && exit 1

    # At least one result must exist and be non-empty
    local any_found=0
    for f in "$vanilla_file" "$pandas_file" "$hybrid_file" "$prompt_only_file"; do
        [[ -s "$f" ]] && any_found=1
    done
    if [[ $any_found -eq 0 ]]; then
        echo "Error: no results to grade. Run one or more modes first."
        exit 1
    fi

    # Build response header lines (only for files that exist and are non-empty)
    local response_header=""
    [[ -s "$vanilla_file" ]] && response_header+="- Response A (\"Vanilla\"): Bash/Read/Grep/Glob only. Wall time: $(cat "$vanilla_time" 2>/dev/null || echo "N/A")s"$'\n'
    [[ -s "$pandas_file" ]] && response_header+="- Response B (\"Pandas-Exec\"): MCP tools with pandas execution. Wall time: $(cat "$pandas_time" 2>/dev/null || echo "N/A")s"$'\n'
    [[ -s "$hybrid_file" ]] && response_header+="- Response C (\"Hybrid\"): MCP tools with pandas execution + pre-built aggregation. Wall time: $(cat "$hybrid_time" 2>/dev/null || echo "N/A")s"$'\n'
    [[ -s "$prompt_only_file" ]] && response_header+="- Response D (\"Prompt-Only\"): Bash/Read/Grep/Glob with EnergyPlus domain guide. Wall time: $(cat "$prompt_only_time" 2>/dev/null || echo "N/A")s"$'\n'

    # Build response body sections (only for files that exist and are non-empty)
    local response_bodies=""
    if [[ -s "$vanilla_file" ]]; then
        response_bodies+=$'\n## Response A — Vanilla (no MCP, no domain guide)\n'
        response_bodies+="$(cat "$vanilla_file")"$'\n'
    fi
    if [[ -s "$pandas_file" ]]; then
        response_bodies+=$'\n## Response B — Pandas-Exec (MCP + execute_pandas)\n'
        response_bodies+="$(cat "$pandas_file")"$'\n'
    fi
    if [[ -s "$hybrid_file" ]]; then
        response_bodies+=$'\n## Response C — Hybrid (MCP + pre-built aggregation tools)\n'
        response_bodies+="$(cat "$hybrid_file")"$'\n'
    fi
    if [[ -s "$prompt_only_file" ]]; then
        response_bodies+=$'\n## Response D — Prompt-Only (no MCP, with domain guide)\n'
        response_bodies+="$(cat "$prompt_only_file")"$'\n'
    fi

    local grade_prompt
    grade_prompt="$(cat <<GRADEEOF
You are grading up to 4 AI responses to the same EnergyPlus analysis prompt.
Each was given the same task but different toolsets:
${response_header}
## Expected Answers (ground truth)
\`\`\`json
$(cat "$EXPECTED_FILE")
\`\`\`

## The Original Prompt
$(cat "$PROMPT_FILE")
${response_bodies}
## Grading Instructions

Score each available response on these dimensions (1-5 scale, 5 = best):

| Dimension | What to evaluate |
|-----------|-----------------|
| **Correctness** | Do reported values match expected answers exactly? (most important) |
| **Completeness** | Were all parts of the prompt addressed? |
| **Efficiency** | Was the approach direct, or did it thrash/retry/take unnecessary steps? |
| **Insight** | Did the response add useful interpretation beyond raw numbers? |
| **Graceful degradation** | When data was missing, did it explain what was needed and why? |

For each dimension, give a score and a one-line justification for each response that exists.

Then provide:
1. A summary comparison table (only columns for responses that were run)
2. An overall verdict: which approach performed best and why
3. Observations on what helped — did MCP tools reduce errors? Did the domain guide help? Did pre-built aggregation tools make a difference?
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
    vanilla)        run_vanilla ;;
    pandas-exec)    run_pandas_exec ;;
    hybrid)         run_hybrid ;;
    prompt-only)    run_prompt_only ;;
    all)            run_vanilla; run_pandas_exec; run_hybrid; run_prompt_only ;;
    grade)          grade ;;
    # Backward-compat aliases
    with-mcp)       run_pandas_exec ;;
    without-mcp)    run_vanilla ;;
    both)           run_vanilla; run_pandas_exec ;;
    *)              usage ;;
esac

echo ""
echo "Done. Results in $RESULTS_DIR/"
