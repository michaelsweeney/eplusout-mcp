# EnergyPlus Output Analysis Guide

## File Types
- `.table.htm` / `eplustbl.htm` — HTML summary report with all tabular data
- `.sql` — SQLite database with timeseries and tabular data
- `.epJSON` — Input model definition (JSON format)
- `.err` — Error/warning log
- `.rdd` — Report Data Dictionary (lists available output variables)

## Discovering Models
EnergyPlus outputs are grouped by filename stem. Use:
```bash
find <directory> -name "*.table.htm" -o -name "*.sql" | sort
```

## HTML Table Parsing
Tables in EnergyPlus HTML reports follow this pattern:
- Comment `<!-- FullName:ReportName_ReportFor_TableName -->` precedes each table
- The "End Uses" table is in "Annual Building Utility Performance Summary"
- Values in HTML are in GJ for energy, W for power, m³/s for airflow

Use the provided snippet `snippets/parse_end_uses.py` for reliable parsing.

## SQL Timeseries Querying
The SQL database contains:
- `ReportDataDictionary` — lists all available variables with RDD IDs
- `ReportData` — hourly values indexed by TimeIndex and RDD ID
- `Time` — maps TimeIndex to month/day/hour

**CRITICAL: SQL energy values are in Joules. Divide by 1e9 for GJ.**

Use the provided snippet `snippets/query_timeseries.py`.

## Unit Reference
| Source | Energy | Power | Airflow | Temperature |
|--------|--------|-------|---------|-------------|
| HTML tables | GJ | W | m³/s | °C |
| SQL timeseries | J | W | m³/s | °C |
| Conversion | 1 GJ = 1e9 J | | | |

## Common Gotchas
1. **"During Heating" vs "During Occupied Heating"** — The "Time Setpoint Not Met" table has BOTH. Always report "During Heating" (facility total) unless specifically asked for occupied hours.
2. **Zone multipliers** — Zone names containing "MULT" (e.g., ROOM_3_MULT19_FLR_3) represent multiple identical zones. The number after MULT is the multiplier.
3. **Design day vs annual** — Files with `.dd.` in the name are design-day sizing runs, not annual simulations. They will show zeros for annual energy.
4. **SQL meter names vs HTML labels** — HTML shows "Interior Lighting", SQL shows "InteriorLights:Electricity". They're the same data.
