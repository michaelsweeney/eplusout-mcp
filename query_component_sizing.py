import sqlite3
import pandas as pd

sql_path = r'C:\code\ai-mcp\mcp-eplus-outputs - filename-agnostic\eplus_files\diff_filenames\ASHRAE901_HotelLarge_STD2025_Buffalo_SkipEC_gshp.dd.sql'

conn = sqlite3.connect(sql_path)
cursor = conn.cursor()

# List all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("Available tables:")
for table in tables:
    print(f"  - {table[0]}")

print("\n" + "="*80 + "\n")

# Look for component sizing tables
component_tables = [t[0] for t in tables if 'component' in t[0].lower() or 'sizing' in t[0].lower()]
print(f"Component/Sizing related tables: {component_tables}")

print("\n" + "="*80 + "\n")

# Query ComponentSizes table
try:
    query = "SELECT * FROM ComponentSizes"
    df = pd.read_sql_query(query, conn)
    print(f"ComponentSizes table found with {len(df)} rows\n")
    
    # Display all columns
    pd.set_option('display.max_columns', None)
    pd.set_option('display.max_rows', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_colwidth', None)
    
    print(df.to_string(index=False))
except Exception as e:
    print(f"Error querying ComponentSizes: {e}")

conn.close()
