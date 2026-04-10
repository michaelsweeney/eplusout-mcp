# Evaluation Methodology Analysis

**Date**: 2026-04-09
**Scope**: Full 4-prompt x 4-mode x 3-model evaluation matrix

## 1. Grading Variance

### The Problem

The same model output receives different scores depending on whether it's graded per-mode (comparing across modes within one model) or per-model (comparing across models within one mode). This isn't just noise — the scoring contexts change what the grader considers "good."

**Concrete examples:**

| Output | Per-mode grade (grade_sonnet) | Cross-model grade | Delta |
|--------|-------------------------------|-------------------|-------|
| 01_vanilla_sonnet | Correctness: 4/5 | Correctness: 5/5 | +1 |
| 02_vanilla_sonnet | Correctness: 5/5 | (via grade_sonnet context) | — |
| 03_vanilla_sonnet | Correctness: 3/5 (wrong zone) | Correctness: 4/5 | +1 |
| 04_vanilla_sonnet | Correctness: 1/5 (no data) | Correctness: 1/5 (sonnet) vs 3/5 (per-mode) | +2 |

The per-mode grader is harsher because it's comparing against a mode that got the answer right — the delta between "correct" and "wrong" is visible in the same context. The cross-model grader may be more forgiving when all three models struggled.

### Root Cause

The LLM grader's scoring is anchored by the comparison set. With 4 responses in per-mode grading, the best response sets the ceiling. With 3 responses in cross-model grading, a different ceiling may exist. This is a well-known problem with LLM-as-judge: scores are relative, not absolute, even when the rubric is designed to be absolute.

### Severity: **Medium-High**

This makes it impossible to directly compare scores across grading contexts. A "4/5" in per-mode grading is not the same as a "4/5" in cross-model grading.

---

## 2. LLM-as-Grader Bias

### Systematic Issues Observed

**a) Confidence bias:** The grader consistently penalizes confident wrong answers more than hedged wrong answers, but inconsistently penalizes silent failures. Opus outputs that "look authoritative" (clean tables, good prose) with wrong numbers sometimes get lower scores than incomplete outputs that didn't try.

- Prompt 03, vanilla cross-model: Opus produces no analysis (session failure) → 1/5 across the board. Haiku produces wrong units and wrong assertions → 2/5 correctness. The grader treated "nothing" as worse than "wrong." But prompt 04 vanilla cross-model: Haiku claims zero unmet hours → 1/5 graceful degradation. Here the grader treated "confidently wrong" as worse than "nothing."

**b) Narrative quality inflation:** Responses with good prose and structure tend to get higher Insight scores even when the insight is built on wrong data. Opus on prompt 04 pandas-exec cross-model: 4/5 Insight despite having systematically wrong cooling values — because the *interpretations* sounded plausible.

**c) The grader doesn't verify independently.** The expected answers JSON is treated as gospel, but the grader doesn't check whether the expected answers are themselves correct. It grades responses *against the JSON*, not against the actual simulation data.

### Severity: **High**

The grading rubric says "Correctness: Do reported values match expected answers exactly?" — this conflates "matches ground truth" with "is actually correct." If the expected answers have an error, every response that got the right real-world answer would be penalized.

---

## 3. Expected Answers Quality

### Issues Found

**a) Prompt 03 scope ambiguity:** The expected answers scope "worst zone" to the two named primary models (Atlanta/Buffalo), but the prompt says "for the model with the most unmet heating hours" across all 20 models. Response C (Hybrid) found GreatFalls OfficeLarge as the genuine worst across all 24 discovered models — this is arguably more correct than the expected answer, but it was penalized because the expected JSON only covers the two named models.

**b) Prompt 04 cooling values:** Multiple responses across different models and modes produced HoChiMinh cooling of ~5,296 GJ, while ground truth says 6,575 GJ. This is suspicious — when 3+ independent runs converge on the same "wrong" value, the expected answer may be the one that's wrong, or at minimum the extraction is ambiguous (e.g., whether "Heat Rejection" belongs in "Cooling").

**c) Prompt 03 tie handling:** The expected answers list ties (e.g., HotelSmall_Chicago = OfficeLarge_Chicago = RetailStandalone_Buffalo at 1484.28 GJ) but the grading doesn't explicitly handle tie-reporting. A response that picks one member of a tie group rather than listing all gets penalized for incompleteness despite being numerically correct.

**d) Prompt 02 worst zone specificity:** `ROOM_4_MULT19_FLR_3` is the "hours" worst zone, while `ROOM_2_FLR_6` may be the "degree-hours" worst zone. The expected answer only lists hours, but the HTML tables contain both metrics. Multiple responses picked the wrong one — this is a table-reading ambiguity, not a reasoning failure.

### Severity: **High**

Expected answers are the foundation of the grading system. Ambiguities in scope, metric definition, and tie handling propagate through every grade.

---

## 4. Prompt Design Bias

### Mode-Favoring Patterns

**a) Prompt-only mode gets unfair domain context advantage:**
The domain guide injected via `--append-system-prompt` gives prompt-only mode knowledge about EnergyPlus table structure, metric definitions, and common pitfalls. This is domain *knowledge*, not just a prompt — it's the equivalent of giving one student the textbook during an exam while others get nothing.

Result: prompt-only consistently wins or ties on Insight and Graceful Degradation because it knows what to look for. This isn't a mode evaluation — it's a knowledge injection evaluation.

**b) Vanilla mode is punished for not knowing what it doesn't know:**
Vanilla gets told "you do NOT have EnergyPlus MCP tools" and to use bash/sqlite3/grep — but no guidance on EnergyPlus data structure. On simple prompts (01, 02) this is fine. On complex multi-model prompts (03, 04) it leads to table-reading errors that are really *domain knowledge* errors, not tool errors.

**c) MCP modes are punished for scope expansion:**
MCP tools make it easy to discover all models, which leads responses to analyze more than what was asked. On prompt 02, the Hybrid mode found GreatFalls OfficeLarge as the genuine worst zone across all 24 models — correct, but penalized because the expected answer scopes to named models only. The tools enabled a better analysis that the grading system marked as wrong.

**d) Complex prompts (03, 04) amplify failure modes:**
- 20 models x 8 questions = many chances for a single parsing error to cascade
- MCP overhead becomes meaningful at scale (457s vs 182s on prompt 04)
- Haiku runs out of context/patience on long tasks and starts skipping steps

The prompt difficulty spectrum (01: simple → 04: complex) is good experimental design, but the grading doesn't weight for it. A 5/5 on prompt 01 is trivially easier to achieve than a 5/5 on prompt 04.

### Severity: **Medium**

The mode comparison is confounded by knowledge injection (prompt-only) and scope ambiguity (MCP modes). The prompts test different things at different difficulty levels but are graded on the same scale.

---

## 5. Opus Catastrophic Failures

### Failure Taxonomy

| Prompt | Mode | Opus Score | Failure Type |
|--------|------|------------|-------------|
| 01 | vanilla (cross-model) | 16/25 | Wrong values (Buffalo heating 636.37 vs 0.00) |
| 03 | vanilla (cross-model) | 5/25 | Session failure — no analysis delivered |
| 04 | vanilla (per-mode) | 6/25 (1,1,1,1,2) | Output is a meta-summary with no data |
| 03 | mcp-pandas-exec-plus (per-mode) | 7/25 | One-paragraph caveat, no analysis |

**Pattern:** Opus failures cluster in vanilla and hybrid modes on complex prompts. The MCP-pandas-exec mode with Opus scored 23/25 on prompt 01, suggesting the tool access helps Opus stay on track.

**Session failures vs. capability failures:** At least 2 of the 4 Opus disasters (prompt 03 vanilla, prompt 04 vanilla) appear to be session/tool management failures, not reasoning failures. The outputs suggest the agent got confused about task state (referencing "background tasks" or "three independent parsing runs") rather than producing wrong analysis.

**Implication:** Opus's raw analytical capability may be higher than its scores suggest, but its agentic reliability (session management, tool calling, task completion) is lower. For a benchmark that tests agentic+analytical combined, this is a valid finding — but it means the scores conflate two independent dimensions.

### Severity: **Medium**

The Opus failures are real and important for agentic use cases, but they don't tell us about Opus's analytical ceiling when it actually completes the task.

---

## 6. Summary of Methodology Flaws

| Flaw | Severity | Fix Difficulty | Impact on Conclusions |
|------|----------|----------------|----------------------|
| Grading variance across contexts | Medium-High | Medium (normalize or use single grading pass) | Can't compare per-mode vs cross-model scores |
| LLM grader relativity | High | Hard (would need multiple independent graders or rubric calibration) | Scores are ordinal within context, not cardinal |
| Expected answers ambiguity | High | Medium (audit expected JSON against raw data, clarify scope) | Some "wrong" responses may be right |
| Domain knowledge confound | Medium | Easy (give all modes the same domain context, or none) | Prompt-only advantage is knowledge, not mode |
| Prompt difficulty not weighted | Medium | Easy (report scores per-prompt, don't aggregate) | A 5/5 on prompt 01 != 5/5 on prompt 04 |
| Opus session failures conflated with capability | Medium | Hard (re-run failures, separate session metrics) | Opus's analytical ceiling is underreported |

---

## 7. What We Can Still Conclude Despite the Flaws

Even with the methodology issues above, several findings are robust:

1. **Haiku → Sonnet is a consistent, large accuracy jump.** This holds across every prompt, every mode, both grading contexts. The delta is 5-15 points on a 25-point scale. This is the most reliable finding in the dataset.

2. **MCP tools help on simple prompts, hurt on complex ones.** On prompts 01-02, MCP modes match or beat vanilla. On prompts 03-04, MCP modes introduce new failure modes (scope expansion, data scrambling). This pattern survives the grading variance issue.

3. **Prompt-only is surprisingly competitive — but it's the knowledge, not the mode.** Every time prompt-only wins, the grader cites domain-specific insight as the reason. This tells us domain guides are valuable, not that "no tools" is better.

4. **Sonnet is the most reliable model for this task class.** It has no catastrophic failures, consistent mid-high scores, and the best correctness-to-time ratio. This holds even accounting for grading variance.

5. **The most dangerous failure mode is confident wrong numbers, not missing data.** Haiku's "zero unmet hours" and B's model-value scrambling are worse than Opus's session failures, because they're harder to detect downstream.
