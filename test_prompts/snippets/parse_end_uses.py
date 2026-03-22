"""Vetted snippet for parsing End Uses from EnergyPlus HTML reports."""
import re

def parse_end_uses(htm_path: str) -> dict:
    """Parse the End Uses table from an EnergyPlus HTML report.

    Returns dict with keys like 'Heating', 'Cooling', 'Total End Uses',
    each mapping to {'Electricity_GJ': float, 'NaturalGas_GJ': float, ...}
    """
    with open(htm_path) as f:
        content = f.read()

    match = re.search(r'End Uses</b>.*?<table[^>]*>(.*?)</table>', content, re.DOTALL)
    if not match:
        return {}

    rows = re.findall(r'<tr>(.*?)</tr>', match.group(1), re.DOTALL)
    header = [re.sub(r'<[^>]+>', '', c).strip()
              for c in re.findall(r'<t[hd][^>]*>(.*?)</t[hd]>', rows[0], re.DOTALL)]

    result = {}
    for row in rows[1:]:
        cells = [re.sub(r'<[^>]+>', '', c).strip()
                 for c in re.findall(r'<t[hd][^>]*>(.*?)</t[hd]>', row, re.DOTALL)]
        if not cells or not cells[0]:
            continue
        end_use = cells[0]
        values = {}
        for i, col in enumerate(header[1:], 1):
            col_clean = col.replace(' [GJ]', '_GJ').replace(' [m3]', '_m3').replace(' ', '_')
            try:
                values[col_clean] = float(cells[i]) if i < len(cells) else 0.0
            except ValueError:
                values[col_clean] = 0.0
        result[end_use] = values
    return result
