"""Vetted snippet for querying EnergyPlus SQL timeseries data."""
import sqlite3
import pandas as pd

def get_available_variables(sql_path: str) -> list[dict]:
    """List available hourly variables from an EnergyPlus SQL database."""
    conn = sqlite3.connect(sql_path)
    df = pd.read_sql(
        "SELECT ReportDataDictionaryIndex, Name, KeyValue, Units "
        "FROM ReportDataDictionary WHERE ReportingFrequency = 'Hourly'",
        conn
    )
    conn.close()
    return df.to_dict(orient='records')

def get_timeseries(sql_path: str, rdd_id: int) -> pd.Series:
    """Extract hourly timeseries for an RDD ID. Returns Series with datetime index."""
    conn = sqlite3.connect(sql_path)
    df = pd.read_sql(f"""
        SELECT t.Month, t.Day, t.Hour - 1 as Hour, rd.Value
        FROM ReportData rd
        JOIN Time t ON rd.TimeIndex = t.TimeIndex
        WHERE rd.ReportDataDictionaryIndex = {rdd_id}
          AND t.Interval = 60
        ORDER BY t.TimeIndex
    """, conn)
    conn.close()
    df['dt'] = pd.to_datetime(
        df['Month'].astype(str) + '-' + df['Day'].astype(str) + '-' + df['Hour'].astype(str),
        format='%m-%d-%H'
    )
    return df.set_index('dt')['Value'].astype(float)

def annual_sum_gj(sql_path: str, rdd_id: int) -> float:
    """Get annual sum for a variable, converted to GJ."""
    series = get_timeseries(sql_path, rdd_id)
    return series.sum() / 1e9
