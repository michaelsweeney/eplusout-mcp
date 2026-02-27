"""Tests for HTML table retrieval and search."""

import pandas as pd
from src.dataloader import execute_pandas_query


def test_report_names_count(atlanta_model):
    names = atlanta_model.html_data.get_report_names()
    assert len(names) == 692


def test_report_names_are_tuples(atlanta_model):
    names = atlanta_model.html_data.get_report_names()
    for n in names:
        assert isinstance(n, tuple)
        assert len(n) == 3


def test_get_table_by_known_tuple(atlanta_model):
    result = atlanta_model.html_data.get_table_by_tuple(
        ("Entire Facility", "Annual Building Utility Performance Summary", "Site and Source Energy")
    )
    assert isinstance(result, list)
    assert len(result) == 4
    assert "Total Energy [GJ]" in result[0]


def test_site_and_source_energy_values(atlanta_model):
    result = atlanta_model.html_data.get_table_by_tuple(
        ("Entire Facility", "Annual Building Utility Performance Summary", "Site and Source Energy")
    )
    first = result[0]
    assert first[""] == "Total Site Energy"
    assert float(first["Total Energy [GJ]"]) > 0


def test_nonexistent_tuple_returns_empty(atlanta_model):
    result = atlanta_model.html_data.get_table_by_tuple(
        ("Nonexistent", "Nonexistent", "Nonexistent")
    )
    assert result == []


def test_keyword_search_cooling(atlanta_model):
    names = atlanta_model.html_data.get_report_names()
    cooling = [n for n in names if "cooling" in str(n).lower()]
    assert len(cooling) == 85


def test_pandas_on_html_table(atlanta_model):
    result = atlanta_model.html_data.get_table_by_tuple(
        ("Entire Facility", "Annual Building Utility Performance Summary", "Site and Source Energy")
    )
    df = pd.DataFrame(result)
    query_result = execute_pandas_query(df, "len(df)")
    assert "4" in query_result
