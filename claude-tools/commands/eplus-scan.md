Scan a directory for EnergyPlus simulation output files and build a model catalog.

## Arguments

$ARGUMENTS is the directory path to scan. If empty, use the current working directory.

## Instructions

1. Find all EnergyPlus output files recursively in the target directory:
   ```bash
   find "$DIR" \( -name "*.table.htm" -o -name "eplustbl.htm" -o -name "*.sql" -o -name "*.epJSON" -o -name "*.err" \) | sort
   ```

2. Group files by directory + filename stem. Files with the same stem in the same directory are one model:
   - `run1/eplusout.sql` + `run1/eplustbl.htm` → model `run1/eplusout`
   - `results/MyBuilding.table.htm` + `results/MyBuilding.sql` → model `results/MyBuilding`
   - For `.table.htm` files, the stem is the part before `.table.htm` (e.g., `Model.table.htm` → stem `Model`)
   - For `eplustbl.htm`, the stem is `eplusout` (EnergyPlus default naming)

3. For files with `.dd.` in the name, mark them as design-day runs (sizing only, not annual simulation).

4. Present results as a table:

   ```
   | # | Model ID | HTML | SQL | epJSON | Err | Type |
   |---|----------|------|-----|--------|-----|------|
   | 1 | run1/eplusout | ✓ | ✓ | ✓ | ✓ | Annual |
   | 2 | run1/eplusout.dd | ✓ | ✓ | | | Design-Day |
   ```

5. Print summary: total models, how many have SQL (timeseries available), how many are design-day vs annual.

6. If any `.err` files exist, quickly scan them for Fatal or Severe errors and flag affected models.

## Example output

```
Found 4 models in ./output/:

| # | Model ID | HTML | SQL | epJSON | Type | Errors |
|---|----------|------|-----|--------|------|--------|
| 1 | HotelLarge_Atlanta | ✓ | ✓ | ✓ | Annual | clean |
| 2 | HotelLarge_Atlanta.dd | ✓ | ✓ | | Design-Day | clean |
| 3 | HotelLarge_Buffalo | ✓ | ✓ | ✓ | Annual | clean |
| 4 | HotelLarge_Buffalo.dd | ✓ | ✓ | | Design-Day | clean |

Summary: 4 models (2 annual, 2 design-day), 4 with SQL, 2 with epJSON
```
