"""Vetted snippet for extracting unmet hours from EnergyPlus HTML reports."""
import re

def parse_unmet_hours(htm_path: str) -> list[dict]:
    """Parse the 'Time Setpoint Not Met' table from HTML.

    Returns list of dicts with zone name, heating hours, cooling hours.
    Uses 'During Heating' (facility total), NOT 'During Occupied Heating'.
    """
    with open(htm_path) as f:
        content = f.read()

    match = re.search(r'Time Setpoint Not Met</b>.*?<table[^>]*>(.*?)</table>',
                       content, re.DOTALL)
    if not match:
        return []

    rows = re.findall(r'<tr>(.*?)</tr>', match.group(1), re.DOTALL)
    header = [re.sub(r'<[^>]+>', '', c).strip()
              for c in re.findall(r'<t[hd][^>]*>(.*?)</t[hd]>', rows[0], re.DOTALL)]

    h_idx = next((i for i, h in enumerate(header) if h == 'During Heating [hr]'), None)
    c_idx = next((i for i, h in enumerate(header) if h == 'During Cooling [hr]'), None)

    results = []
    for row in rows[1:]:
        cells = [re.sub(r'<[^>]+>', '', c).strip()
                 for c in re.findall(r'<t[hd][^>]*>(.*?)</t[hd]>', row, re.DOTALL)]
        if not cells or not cells[0]:
            continue
        results.append({
            'zone': cells[0],
            'heating_unmet_hrs': float(cells[h_idx]) if h_idx and h_idx < len(cells) else 0.0,
            'cooling_unmet_hrs': float(cells[c_idx]) if c_idx and c_idx < len(cells) else 0.0,
        })
    return results
