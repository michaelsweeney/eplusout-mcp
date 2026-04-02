# EnergyPlus Analysis Tools

Use these instructions and snippets when analyzing EnergyPlus simulation output files locally. No MCP server required — parse files directly using Bash, Python, and SQLite.

## File Types

| Extension | Contents | How to access |
|---|---|---|
| `.table.htm` / `eplustbl.htm` | HTML summary report with all tabular data | Parse with Python `re` or `html.parser` |
| `.sql` | SQLite results database (timeseries + tabular data) | Query with `sqlite3` or `pandas.read_sql` |
| `.epJSON` | Input model definition (JSON) | Read with `json.load` |
| `.err` | Error/warning log | Read directly |
| `.rdd` | Report Data Dictionary (lists available output variables) | Read directly |

## Discovering Models

EnergyPlus outputs are grouped by filename stem. A directory may contain:
```
run1/eplusout.sql + run1/eplusout.epJSON + run1/eplustbl.htm  → one model
run1/model.sql + run1/model.table.htm                        → one model
```

Find all models:
```bash
find <directory> \( -name "*.table.htm" -o -name "eplustbl.htm" -o -name "*.sql" \) | sort
```

## Unit Reference

| Source | Energy | Power | Airflow | Temperature |
|---|---|---|---|---|
| HTML tables | GJ | W | m³/s | °C |
| SQL timeseries | **J** | W | m³/s | °C |
| **Conversion** | **1 GJ = 1e9 J** | | | |

**CRITICAL: SQL energy values are in Joules. Always divide by 1e9 for GJ.**

## Common Gotchas

1. **"During Heating" vs "During Occupied Heating"** — The "Time Setpoint Not Met" table has BOTH columns. Always report **"During Heating [hr]"** (facility total) unless specifically asked for occupied-only hours. Confusing these is the most common analysis error.

2. **Zone multipliers** — Zone names containing "MULT" (e.g., `ROOM_3_MULT19_FLR_3`) represent multiple identical zones. The number after MULT is the multiplier (19 in this case). Multiply zone-level results accordingly for building totals.

3. **Design day vs annual** — Files with `.dd.` in the name are design-day sizing runs, not annual simulations. They will show zeros for annual energy consumption. Exclude them from annual energy analysis.

4. **SQL meter names vs HTML labels** — The same data appears under different names:

| HTML End Use row | SQL Meter name |
|---|---|
| Interior Lighting | `InteriorLights:Electricity` |
| Interior Equipment | `InteriorEquipment:Electricity` |
| Heating | `Heating:Electricity` or `Heating:NaturalGas` |
| Cooling | `Cooling:Electricity` |
| Total | `Electricity:Facility`, `NaturalGas:Facility` |

## Vetted Parsing Snippets

Use the Python snippets in `claude-tools/snippets/` for reliable parsing:

- **`parse_end_uses.py`** — Extract the End Uses table from HTML. Returns dict keyed by end-use name.
- **`query_timeseries.py`** — Query SQL timeseries by RDD ID. Includes `annual_sum_gj()` helper.
- **`unmet_hours.py`** — Extract unmet setpoint hours. Uses "During Heating" (facility total), not occupied.

### Quick examples

```python
# Parse end uses from HTML
exec(open("claude-tools/snippets/parse_end_uses.py").read())
end_uses = parse_end_uses("path/to/model.table.htm")
print(end_uses["Heating"])  # {'Electricity_GJ': 0.0, 'Natural_Gas_GJ': 1484.28, ...}

# Query SQL timeseries
exec(open("claude-tools/snippets/query_timeseries.py").read())
variables = get_available_variables("path/to/model.sql")
total_elec_gj = annual_sum_gj("path/to/model.sql", rdd_id=179)

# Get unmet hours
exec(open("claude-tools/snippets/unmet_hours.py").read())
unmet = parse_unmet_hours("path/to/model.table.htm")
facility = [z for z in unmet if z["zone"] == "Facility"][0]
```

## HTML Table Parsing Details

Tables in EnergyPlus HTML reports are preceded by comments:
```html
<!-- FullName:ReportName_ReportFor_TableName -->
```

Key tables for energy analysis:
- **End Uses**: `Annual Building Utility Performance Summary` → `End Uses`
- **Unmet Hours**: `Annual Building Utility Performance Summary` → `Time Setpoint Not Met`
- **Zone Heating Sizing**: `HVAC Sizing Summary` → `Zone Sensible Heating`
- **Zone Cooling Sizing**: `HVAC Sizing Summary` → `Zone Sensible Cooling`

## SQL Database Schema

Key tables in the SQLite database:

```sql
-- List available hourly output variables
SELECT ReportDataDictionaryIndex, Name, KeyValue, Units
FROM ReportDataDictionary
WHERE ReportingFrequency = 'Hourly';

-- Get hourly timeseries for a variable (by RDD ID)
SELECT t.Month, t.Day, t.Hour - 1 as Hour, rd.Value
FROM ReportData rd
JOIN Time t ON rd.TimeIndex = t.TimeIndex
WHERE rd.ReportDataDictionaryIndex = ?
  AND t.Interval = 60
ORDER BY t.TimeIndex;

-- Get annual sum in GJ
SELECT SUM(Value) / 1e9 as total_gj
FROM ReportData
WHERE ReportDataDictionaryIndex = ?;
```

## EnergyPlus Reference Documentation

- **I/O Reference**: `https://bigladdersoftware.com/epx/docs/24-1/input-output-reference/`
- **Engineering Reference**: `https://bigladdersoftware.com/epx/docs/24-1/engineering-reference/`
- **URL pattern**: Replace `24-1` with version (e.g., `25-2`, `23-2`, `9-6`)
