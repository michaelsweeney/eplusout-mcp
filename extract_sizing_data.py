import sqlite3
import re
from pathlib import Path

# File paths
base_path = Path(r"C:\code\ai-mcp\mcp-eplus-outputs - filename-agnostic\eplus_files\diff_filenames")
epjson_file = base_path / "ASHRAE901_HotelLarge_STD2025_Buffalo_SkipEC_gshp.dd.epJSON"
sql_file = base_path / "ASHRAE901_HotelLarge_STD2025_Buffalo_SkipEC_gshp.dd.sql"
html_file = base_path / "ASHRAE901_HotelLarge_STD2025_Buffalo_SkipEC_gshp.dd.table.htm"

print("=" * 80)
print("MODEL INFORMATION")
print("=" * 80)
print(f"epJSON File: {epjson_file.name}")
print(f"SQL File: {sql_file.name}")
print(f"HTML File: {html_file.name}")
print()

# Read HTML file and extract Component Sizing Summary
print("=" * 80)
print("COMPONENT SIZING SUMMARIES")
print("=" * 80)

with open(html_file, 'r', encoding='utf-8') as f:
    html_content = f.read()

# Find all Component Sizing Summary sections
pattern = r'<p>Report:<b>\s*Component Sizing Summary\s*</b></p>.*?(?=<hr>|<p>Report:<b>|$)'
matches = list(re.finditer(pattern, html_content, re.DOTALL))

if matches:
    print(f"Found {len(matches)} Component Sizing Summary section(s)\n")
    
    # Extract each section
    for i, match in enumerate(matches, 1):
        section = match.group()
        
        # Extract tables from the section
        tables = re.findall(r'<table border="1".*?</table>', section, re.DOTALL)
        
        print(f"Section {i}:")
        print("-" * 80)
        
        for table in tables:
            # Extract table headers and rows
            rows = re.findall(r'<tr>(.*?)</tr>', table, re.DOTALL)
            
            for row in rows:
                cells = re.findall(r'<td.*?>(.*?)</td>', row, re.DOTALL)
                if cells:
                    # Clean HTML tags and whitespace
                    cleaned_cells = [re.sub(r'<.*?>', '', cell).strip() for cell in cells]
                    print("  |  ".join(cleaned_cells))
            print()
        print()
else:
    print("No Component Sizing Summary sections found in HTML file.")
    # Search for alternative patterns
    if "Sizing" in html_content:
        sizing_reports = re.findall(r'<p>Report:<b>(.*?Sizing.*?)</b></p>', html_content)
        if sizing_reports:
            print(f"\nFound {len(sizing_reports)} sizing-related reports:")
            for report in sizing_reports:
                print(f"  - {report}")

print()

# Query SQL database for hourly reports
print("=" * 80)
print("HOURLY REPORTS IN SQL DATABASE")
print("=" * 80)

try:
    conn = sqlite3.connect(str(sql_file))
    cursor = conn.cursor()
    
    # First check the schema
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"Available tables: {[t[0] for t in tables]}\n")
    
    # Get column info for ReportDataDictionary
    cursor.execute("PRAGMA table_info(ReportDataDictionary)")
    columns = cursor.fetchall()
    print(f"ReportDataDictionary columns: {[col[1] for col in columns]}\n")
    
    # Get all hourly reports
    query = """
    SELECT DISTINCT Name, KeyValue
    FROM ReportDataDictionary
    WHERE ReportingFrequency = 'Hourly'
    ORDER BY Name, KeyValue
    """
    
    cursor.execute(query)
    hourly_reports = cursor.fetchall()
    
    if hourly_reports:
        print(f"Found {len(hourly_reports)} hourly report variable(s):\n")
        
        # Group by report name
        from collections import defaultdict
        reports_by_name = defaultdict(list)
        for report_name, key_value in hourly_reports:
            reports_by_name[report_name].append(key_value)
        
        for i, (report_name, key_values) in enumerate(sorted(reports_by_name.items()), 1):
            print(f"{i}. {report_name}")
            print(f"   Number of instances: {len(key_values)}")
            if len(key_values) <= 5:
                for kv in key_values:
                    print(f"     - {kv}")
            else:
                for kv in key_values[:3]:
                    print(f"     - {kv}")
                print(f"     ... and {len(key_values) - 3} more")
            print()
    else:
        print("No hourly reports found in the SQL database.")
        
        # Check what reporting frequencies are available
        cursor.execute("SELECT DISTINCT ReportingFrequency FROM ReportDataDictionary")
        frequencies = cursor.fetchall()
        print(f"\nAvailable reporting frequencies: {', '.join([f[0] for f in frequencies])}")
    
    conn.close()
    
except Exception as e:
    print(f"Error reading SQL database: {e}")

print()
print("=" * 80)
print("EXTRACTION COMPLETE")
print("=" * 80)
