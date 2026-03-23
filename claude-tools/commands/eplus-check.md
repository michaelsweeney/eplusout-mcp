Run a health check on one or more EnergyPlus models — errors, warnings, unmet hours, and sizing alerts.

## Arguments

$ARGUMENTS is either:
- A path to a specific model's `.err`, `.table.htm`, or `.sql` file
- A directory containing one or more models (scans all)
- Empty: scan current working directory

## Instructions

### 1. Find models

If a directory is given, discover models the same way as `/eplus-scan`. If a specific file is given, identify its model by stem.

### 2. Error file check

For each model with an `.err` file:

```bash
# Count by severity
grep -c "^\s*\*\*  Severe" "$err_file"
grep -c "^\s*\*\* Warning" "$err_file"
grep -c "^\s*\*\*  Fatal" "$err_file"
```

If Fatal > 0, flag as **FAILED** — the simulation did not complete.

If Severe > 0, show the severe error messages (they may indicate invalid inputs or convergence failures).

If Warning > 50, note the count but don't list them all — just flag "high warning count."

### 3. Unmet hours check

For each model with an `.table.htm` file, parse the "Time Setpoint Not Met" table. Use the vetted snippet from `claude-tools/snippets/unmet_hours.py`.

**IMPORTANT:** Use the **"During Heating [hr]"** and **"During Cooling [hr]"** columns (facility total), NOT the "During Occupied" columns.

Report:
- Facility heating unmet hours
- Facility cooling unmet hours
- Worst zone for heating (name + hours)
- Worst zone for cooling (name + hours)

Flag thresholds:
- **PASS** (green): ≤ 300 unmet hours (ASHRAE 90.1 threshold)
- **WARNING** (yellow): 300–600 unmet hours
- **FAIL** (red): > 600 unmet hours

### 4. Energy sanity check

From the End Uses table (use `claude-tools/snippets/parse_end_uses.py`):
- Total site energy (electricity + gas) in GJ
- Heating and cooling end uses
- Flag if heating > 0 AND cooling > 0 for the same fuel (unusual, may indicate simultaneous heating/cooling)

### 5. Sizing check

From the "Zone Sensible Heating" and "Zone Sensible Cooling" tables (if available):
- Check if any zone has "User Design Load" significantly different from "Calculated Design Load" (ratio > 1.5 or < 0.67) — indicates manual sizing overrides
- Check for zones with very small loads (< 100 W) that might indicate unconditioned zones incorrectly included

### 6. Present results

For a single model:
```
## Model: HotelLarge_Buffalo

### Errors
- Fatal: 0, Severe: 0, Warnings: 47
- Status: CLEAN

### Unmet Hours
- Heating: 20.67 hr (PASS — under 300 hr threshold)
  - Worst zone: ROOM_4_MULT19_FLR_3 (14.67 hr)
- Cooling: 8.33 hr (PASS)
  - Worst zone: ROOM_2_FLR_3 (4.50 hr)

### Energy
- Total electricity: 5,105.50 GJ
- Total natural gas: 6,658.12 GJ
- Heating: 1,484.28 GJ (gas)
- Cooling: 543.50 GJ (electric)

### Sizing
- All zones within expected range
```

For multiple models, use a summary table first, then details for any flagged models:

```
| Model | Errors | Unmet Heat | Unmet Cool | Status |
|-------|--------|------------|------------|--------|
| HotelLarge_Atlanta | clean | 6.83 hr | 77.00 hr | PASS |
| HotelLarge_Buffalo | clean | 20.67 hr | 8.33 hr | PASS |
| OfficeLarge_GreatFalls | clean | 433.33 hr | 501.67 hr | FAIL |

⚠ OfficeLarge_GreatFalls exceeds 300 hr unmet threshold — see details below.
```

Then expand details only for models with issues.
