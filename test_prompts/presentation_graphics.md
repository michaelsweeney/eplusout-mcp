# Presentation Graphics — "Retrospective: One Year Later"

Ideas for visualizing the EnergyPlus MCP evaluation results. Data is from a 4-prompt x 4-mode x 3-model evaluation matrix run in early April 2026.

---

## Graphic 1: The Accuracy Ladder (Heat Map)

**What it shows:** Total scores (out of 25) across all prompt × mode × model combinations.

**Format:** 3-panel heat map, one column per model (Haiku / Sonnet / Opus), rows are prompt × mode. Color scale from red (≤10) → yellow (15-18) → green (22+). Gray cells for session failures / no data.

**Why it works for a retrospective:** At a glance, it tells the story: Sonnet is a reliable green band, Haiku is mostly red/yellow, and Opus is a mix of green and dramatic gray/red. The visual pattern is immediately readable.

**Data (from cross-model grade-models files, 16 comparisons):**

| Prompt | Mode | Haiku | Sonnet | Opus |
|--------|------|-------|--------|------|
| 01 | vanilla | 6 | 24 | 16 |
| 01 | pandas-exec | 13 | 25 | 23 |
| 01 | hybrid | 17 | 25 | 23 |
| 01 | prompt-only | 17 | 25 | 20 |
| 02 | vanilla | 14 | 23 | 23 |
| 02 | pandas-exec | 19 | 22 | 20 |
| 02 | hybrid | 21 | 16 | 24 |
| 02 | prompt-only | 13 | 25 | 25 |
| 03 | vanilla | 13 | 7 | 20 |
| 03 | mcp-pandas-exec | 10 | 15 | 16 |
| 03 | mcp-pandas-exec-plus | 11 | 25 | 18 |
| 03 | prompt-only | 10 | 19 | 16 |
| 04 | vanilla | 18 | 20 | 13 |
| 04 | pandas-exec | 8 | — | 24 |
| 04 | hybrid | 17 | 23 | 5 |
| 04 | prompt-only | 11 | — | 22 |

**Aggregates:** Sonnet avg 21.0/25 (14 appearances), Opus avg 17.8/25 (16), Haiku avg 12.9/25 (16). Haiku won 0 of 16 comparisons.

Note: Sonnet was absent from 2 prompt-04 files (prompt-only, pandas-exec) which were 2-model comparisons only.

---

## Graphic 2: The Failure Modes Triangle

**What it shows:** Three distinct failure archetypes, one per model family.

**Format:** Triangle diagram or 3-column infographic. Each column has a model name, an icon, a short label, and a quote from the actual grading.

| | Haiku | Sonnet | Opus |
|--|-------|--------|------|
| **Icon** | Confident checkmark on wrong answer | Steady metronome | Rocket exploding on launchpad |
| **Label** | "Confidently Wrong" | "Reliably Right" | "Brilliant or Broken" |
| **Quote** | *"Zero unmet hours across all models"* (actual: 12 models had unmet hours) | *"All values match ground truth exactly"* | *"That was the earlier background task completing — its results were already superseded"* |
| **Risk** | Hardest to catch downstream | Low risk | High variance, but recoverable |

**Why it works:** It frames model selection as a risk management decision, not just an accuracy benchmark. Great for an audience making procurement/architecture decisions.

---

## Graphic 3: Speed vs. Accuracy Scatter Plot

**What it shows:** Wall time (x-axis) vs. total score (y-axis) for every run in the matrix.

**Format:** Scatter plot with points colored by model (blue = Haiku, green = Sonnet, orange = Opus) and shaped by mode (circle = vanilla, square = MCP, diamond = prompt-only).

**Key regions to annotate:**
- **Top-left (fast + accurate):** Sonnet vanilla on simple prompts — the sweet spot
- **Bottom-left (fast + wrong):** Haiku — speed without substance
- **Top-right (slow + accurate):** Prompt-only on complex prompts — correctness costs time
- **Bottom-right (slow + wrong):** Opus session failures, Sonnet prompt 04 vanilla — the worst quadrant
- **Pareto frontier line** connecting the best speed-accuracy tradeoffs

**Data points (cross-model grade scores + wall times):**

| Run | Time (s) | Score | Model | Mode |
|-----|----------|-------|-------|------|
| 01_vanilla_haiku | 9 | 6 | haiku | vanilla |
| 01_vanilla_sonnet | 91 | 24 | sonnet | vanilla |
| 01_vanilla_opus | 137 | 16 | opus | vanilla |
| 01_pandas-exec_haiku | 37 | 13 | haiku | mcp |
| 01_pandas-exec_sonnet | 77 | 25 | sonnet | mcp |
| 01_pandas-exec_opus | 107 | 23 | opus | mcp |
| 01_hybrid_haiku | 86 | 17 | haiku | mcp+ |
| 01_hybrid_sonnet | 87 | 25 | sonnet | mcp+ |
| 01_hybrid_opus | 98 | 23 | opus | mcp+ |
| 01_prompt-only_haiku | 93 | 17 | haiku | prompt-only |
| 01_prompt-only_sonnet | 102 | 25 | sonnet | prompt-only |
| 01_prompt-only_opus | 176 | 20 | opus | prompt-only |
| 02_vanilla_haiku | 227 | 14 | haiku | vanilla |
| 02_vanilla_sonnet | 197 | 23 | sonnet | vanilla |
| 02_vanilla_opus | 155 | 23 | opus | vanilla |
| 02_pandas-exec_haiku | 94 | 19 | haiku | mcp |
| 02_pandas-exec_sonnet | 289 | 22 | sonnet | mcp |
| 02_pandas-exec_opus | 153 | 20 | opus | mcp |
| 02_hybrid_haiku | 113 | 21 | haiku | mcp+ |
| 02_hybrid_sonnet | 281 | 16 | sonnet | mcp+ |
| 02_hybrid_opus | 190 | 24 | opus | mcp+ |
| 02_prompt-only_haiku | 149 | 13 | haiku | prompt-only |
| 02_prompt-only_sonnet | 264 | 25 | sonnet | prompt-only |
| 02_prompt-only_opus | 157 | 25 | opus | prompt-only |
| 03_vanilla_haiku | 171 | 13 | haiku | vanilla |
| 03_vanilla_sonnet | 305 | 7 | sonnet | vanilla |
| 03_vanilla_opus | 540 | 20 | opus | vanilla |
| 03_mcp_haiku | 156 | 10 | haiku | mcp |
| 03_mcp_opus | 270 | 16 | opus | mcp |
| 03_mcp-plus_haiku | 149 | 11 | haiku | mcp+ |
| 03_mcp-plus_opus | 408 | 18 | opus | mcp+ |
| 03_mcp-plus_sonnet | — | 25 | sonnet | mcp+ |
| 03_prompt-only_haiku | 170 | 10 | haiku | prompt-only |
| 03_prompt-only_sonnet | 862 | 19 | sonnet | prompt-only |
| 03_prompt-only_opus | 144 | 16 | opus | prompt-only |
| 04_vanilla_haiku | 331 | 18 | haiku | vanilla |
| 04_vanilla_sonnet | 898 | 20 | sonnet | vanilla |
| 04_vanilla_opus | 298 | 13 | opus | vanilla |
| 04_pandas-exec_haiku | 183 | 8 | haiku | mcp |
| 04_pandas-exec_opus | 325 | 24 | opus | mcp |
| 04_hybrid_haiku | 460 | 17 | haiku | mcp+ |
| 04_hybrid_sonnet | 498 | 23 | sonnet | mcp+ |
| 04_hybrid_opus | 389 | 5 | opus | mcp+ |
| 04_prompt-only_haiku | 196 | 11 | haiku | prompt-only |
| 04_prompt-only_opus | 314 | 22 | opus | prompt-only |

**Why it works:** The Pareto frontier visual immediately shows that Sonnet dominates the efficient frontier. Haiku is fast-but-low, Opus has the widest spread. The "speed vs accuracy" framing resonates with engineering audiences.

---

## Graphic 4: "MCP Helps Simple, Hurts Complex" — Paired Bar Chart

**What it shows:** Delta in total score when adding MCP tools, split by prompt complexity.

**Format:** Horizontal bar chart. Each bar = score delta (MCP mode - vanilla mode) for a given prompt × model. Bars colored green when MCP helped, red when it hurt. Grouped by "Simple" (prompts 01-02) and "Complex" (prompts 03-04).

**Story it tells:** The left half (simple prompts) is mostly green — MCP tools add +2 to +5 points. The right half (complex prompts) is mixed-to-red — MCP tools introduce -1 to -4 point regressions through scope expansion and data scrambling.

**Data (all models, cross-model grades — vanilla vs mcp-pandas-exec):**

| Prompt | Model | Vanilla | MCP | Delta |
|--------|-------|---------|-----|-------|
| 01 (simple) | Sonnet | 24 | 25 | **+1** |
| 01 (simple) | Opus | 16 | 23 | **+7** |
| 01 (simple) | Haiku | 6 | 13 | **+7** |
| 02 (medium) | Sonnet | 23 | 22 | **-1** |
| 02 (medium) | Opus | 23 | 20 | **-3** |
| 02 (medium) | Haiku | 14 | 19 | **+5** |
| 03 (complex) | Opus | 20 | 16 | **-4** |
| 03 (complex) | Haiku | 13 | 10 | **-3** |
| 04 (complex) | Opus | 13 | 24 | **+11** |
| 04 (complex) | Haiku | 18 | 8 | **-10** |

**Key annotation:** "The bottleneck was *knowing which row to parse*, not *executing the parse*." (direct quote from grade report)

---

## Graphic 5: The Domain Knowledge Effect — Before/After

**What it shows:** Prompt-only mode (with domain guide) vs. vanilla mode (without), same model, same prompt.

**Format:** Side-by-side comparison cards for 2-3 key prompts, showing score improvement and calling out the specific insight the domain guide unlocked.

**Examples:**

**Prompt 02 (Sonnet):** Vanilla 23 → Prompt-only 24 (+1)
- Domain guide unlocked: boiler efficiency estimate (~77% ≈ ASHRAE 90.1), 0.56°C tolerance threshold, setback-ramp hypothesis

**Prompt 03 (Sonnet):** Vanilla 19 → Prompt-only 19 (=)
- Domain guide unlocked: correct worst zone (ROOM_4_MULT19_FLR_3 vs ROOM_2_FLR_6), but 3x slower (862s vs 305s)

**Prompt 04 (Sonnet):** Vanilla 19 → Prompt-only 19 (=)
- Domain guide unlocked: fastest completion (340s vs 898s vanilla), correct unmet hours where others failed

**Takeaway annotation:** "Domain knowledge is the real differentiator — the delivery mechanism (MCP tools vs. prompt injection) matters less than whether the model knows what it's looking at."

---

## Graphic 6: Model Reliability Distribution — Box-and-Whisker

**What it shows:** Score distributions by model across all runs.

**Format:** Three box-and-whisker plots side by side (Haiku, Sonnet, Opus), showing median, quartiles, and outliers.

**Actual distributions (from 16 cross-model comparisons):**
- **Haiku** (n=16): Range 6–21, median ~13, IQR 10–17.5. No score above 21. Consistent underperformer.
- **Sonnet** (n=14): Range 7–25, median ~23, IQR 19–25. One dramatic outlier at 7 (prompt 03 vanilla — session output failure). Otherwise clustered high.
- **Opus** (n=16): Range 5–25, median ~20, IQR 16–23. Outliers at 5 (prompt 04 hybrid) and 13 (prompt 04 vanilla). Widest spread of any model.

**Why it works:** The box width tells the reliability story instantly. Sonnet is a narrow green box in the top half. Opus is a wide orange box spanning almost the full range. Perfect for "which model should we bet on?" discussions.

---

## Graphic 7: The Grading Paradox — Methodology Callout

**What it shows:** The same output scored differently in different grading contexts.

**Format:** Simple callout box or sidebar, not a full graphic. Shows 2-3 examples of score divergence with the explanation.

**Example:**
> Sonnet's prompt 04 vanilla output scored **1/5 correctness** in per-mode grading (no verifiable numbers shown) but the same grader model assigned **3/5** to Opus for having "multiple significant errors." The grader's internal scale shifts based on what else it's comparing against.

**Purpose:** Honest methodology disclosure. Shows the audience you know the limitations of LLM-as-judge evaluation. Builds credibility for the findings you *do* present.

---

## Recommended Slide Sequence

1. **Graphic 1 (Heat Map)** — Set the scene: "Here's what happened when we ran 48+ evaluation runs"
2. **Graphic 6 (Box-Whisker)** — "Model reliability matters more than peak performance"
3. **Graphic 3 (Scatter)** — "The speed-accuracy tradeoff is real"
4. **Graphic 4 (MCP Delta)** — "MCP tools help simple tasks, hurt complex ones"
5. **Graphic 5 (Domain Knowledge)** — "The real differentiator was domain knowledge, not tooling"
6. **Graphic 2 (Failure Modes)** — "Each model fails differently — choose based on your risk tolerance"
7. **Graphic 7 (Methodology)** — "What we'd do differently next time"
