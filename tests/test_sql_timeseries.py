"""Tests for SQL timeseries data extraction."""

import pandas as pd
from src.dataloader import execute_pandas_query


def test_availseries_count(atlanta_model):
    ts = atlanta_model.sql_data.get_timeseries()
    avail = ts.availseries()
    assert len(avail) == 4


def test_availseries_structure(atlanta_model):
    ts = atlanta_model.sql_data.get_timeseries()
    avail = ts.availseries()
    expected_keys = {
        "ReportDataDictionaryIndex", "IsMeter", "Type", "IndexGroup",
        "TimestepType", "KeyValue", "Name", "ReportingFrequency",
        "ScheduleName", "Units"
    }
    assert set(avail[0].keys()) == expected_keys


def test_known_rdd_179_returns_8760(atlanta_model):
    ts = atlanta_model.sql_data.get_timeseries()
    series = ts.getseries_by_record_id(179)
    assert len(series) == 8760


def test_timeseries_record_keys(atlanta_model):
    ts = atlanta_model.sql_data.get_timeseries()
    series = ts.getseries_by_record_id(179)
    expected_keys = {
        "dt", "KeyValue", "Name", "TimestepType", "IndexGroup",
        "ScheduleName", "Units", "IsMeter", "ReportingFrequency",
        "Type", "Value"
    }
    assert set(series[0].keys()) == expected_keys


def test_timeseries_metadata(atlanta_model):
    ts = atlanta_model.sql_data.get_timeseries()
    series = ts.getseries_by_record_id(179)
    first = series[0]
    assert first["Name"] == "Electricity:Facility"
    assert first["Units"] == "J"


def test_dd_model_has_48_records(atlanta_dd_model):
    ts = atlanta_dd_model.sql_data.get_timeseries()
    avail = ts.availseries()
    rdd = avail[0]["ReportDataDictionaryIndex"]
    series = ts.getseries_by_record_id(rdd)
    assert len(series) == 48


def test_pandas_on_timeseries(atlanta_model):
    ts = atlanta_model.sql_data.get_timeseries()
    series = ts.getseries_by_record_id(179)
    df = pd.DataFrame(series)
    result = execute_pandas_query(df, "df['Value'].mean()")
    assert "Value" not in result or float(result) > 0
