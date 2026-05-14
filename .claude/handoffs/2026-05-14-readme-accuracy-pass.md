# Codex Handoff

**Date:** 2026-05-14
**Topic:** readme-accuracy-pass

## Goal

Produce a clean, accurate public README for the v0.1.0-beta release of eplusout-mcp. README must reflect what is actually on `main`, not what was prototyped on the experiment branches.

## Question for Codex

Do a critical pass on README.md. Flag:

1. Any inaccuracy or drift between the README's claims and what's actually on `main` (especially the Available Tools, Workflow, and File Structure sections — these were just rewritten and may still have errors).
2. The Pattern 1 / Pattern 2 split — are the boundaries clean? Is anything in the wrong section? Does the framing hold up?
3. Eval section framing — the eval used four conditions, three of which live on archived experiment tags. Does the README handle that distinction cleanly, or does it still imply experiment features are part of main?
4. Clarity, redundancy, or anything that would confuse a first-time reader landing from a GitHub link.

Provide concrete, line-referenced suggestions. Do NOT edit the file — the human will apply changes selectively.

## Context

### Files in play
- `README.md` — the file under review
- `src/server.py` — ground truth for MCP tools actually on main (7 `@mcp.tool()`-decorated functions; no `execute_pandas`)
- `src/CLAUDE.md` — MCP tool docs served as resource
- `src/tools/` — file format handlers (`func_sql.py`, `func_html.py`, `func_epjson.py`)
- `claude-tools/` — Pattern 1 components (`CLAUDE.md`, `commands/`, `snippets/`)
- `docs/eval-results-2026-03-22.md` — the eval writeup the README links to
- `test_prompts/` — eval framework directory

### Decisions already made
- Section names "Pattern 1: Prompt Tools (Local)" and "Pattern 2: MCP Server (Remote)" are final — don't relitigate naming.
- `execute_pandas`, `sandbox.py`, `data_loader.py` are deliberately NOT on main; they live on experiment tags (`exp/pandas-exec-v1`, `exp/hybrid-v1`). README should reflect this; do not propose merging them.
- The four eval conditions: Vanilla (main), Prompt-only (`exp/prompt-only-v1`), Pandas-exec (`exp/pandas-exec-v1`), Hybrid (`exp/hybrid-v1`).
- Version tag `v0.1.0-beta` is already cut on main.

### Things already tried
- Just did a manual accuracy pass (commits `c4a2549`, `9c3162f`, `83ffc10` on main). The README was previously describing `execute_pandas` as if it were on main; I removed those references and added callouts to the experiment tags. Looking for what I missed.

## Scope guardrails

- **Touch:** nothing — review only, recommendations in chat.
- **Don't touch:** any file in the repo.
- **Read-only?** yes

## Verification

Suggestions are actionable when they include line numbers, a quote of the current text, and the specific change to make. Any claim that "main has/doesn't have X" should be cross-referenced against `src/` — not inferred from the README's own wording.
