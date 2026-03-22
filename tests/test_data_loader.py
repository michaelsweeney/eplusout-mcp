import pytest
import pandas as pd
from pathlib import Path
from src.data_loader import load_sql_timeseries, load_html_tables, DataCache


@pytest.fixture(scope="module")
def buffalo_sql_path():
    return str(Path(__file__).parent.parent / "example-files" / "ASHRAE901_HotelLarge_STD2013_Buffalo.sql")

@pytest.fixture(scope="module")
def buffalo_html_path():
    return str(Path(__file__).parent.parent / "example-files" / "ASHRAE901_HotelLarge_STD2013_Buffalo.table.htm")


class TestSqlTimeseriesLoading:
    def test_returns_dataframe(self, buffalo_sql_path):
        df = load_sql_timeseries(buffalo_sql_path)
        assert isinstance(df, pd.DataFrame)

    def test_has_datetime_index(self, buffalo_sql_path):
        df = load_sql_timeseries(buffalo_sql_path)
        assert isinstance(df.index, pd.DatetimeIndex)

    def test_has_8760_rows(self, buffalo_sql_path):
        df = load_sql_timeseries(buffalo_sql_path)
        assert len(df) == 8760

    def test_column_names_include_units(self, buffalo_sql_path):
        df = load_sql_timeseries(buffalo_sql_path)
        for col in df.columns:
            assert "[" in col and "]" in col, f"Column '{col}' missing units"

    def test_electricity_facility_sum_matches_known(self, buffalo_sql_path):
        df = load_sql_timeseries(buffalo_sql_path)
        elec_cols = [c for c in df.columns if "Electricity:Facility" in c]
        assert len(elec_cols) >= 1
        total_gj = df[elec_cols[0]].sum() / 1e9
        assert abs(total_gj - 5105.50) < 0.1


class TestHtmlTablesLoading:
    def test_returns_dict(self, buffalo_html_path):
        tables = load_html_tables(buffalo_html_path)
        assert isinstance(tables, dict)

    def test_keys_are_tuples(self, buffalo_html_path):
        tables = load_html_tables(buffalo_html_path)
        for key in tables:
            assert isinstance(key, tuple)
            assert len(key) == 3

    def test_values_are_dataframes(self, buffalo_html_path):
        tables = load_html_tables(buffalo_html_path)
        for df in tables.values():
            assert isinstance(df, pd.DataFrame)

    def test_end_uses_table_exists(self, buffalo_html_path):
        tables = load_html_tables(buffalo_html_path)
        end_uses_keys = [k for k in tables if "End Uses" in k[2]]
        assert len(end_uses_keys) >= 1


class TestDataCache:
    def test_caches_results(self, buffalo_sql_path):
        cache = DataCache(max_size=3)
        df1 = cache.get_sql_ts("test_id", buffalo_sql_path)
        df2 = cache.get_sql_ts("test_id", buffalo_sql_path)
        assert df1 is df2

    def test_evicts_oldest(self):
        cache = DataCache(max_size=2)
        cache._sql_cache["a"] = pd.DataFrame()
        cache._sql_cache["b"] = pd.DataFrame()
        cache._sql_cache["c"] = pd.DataFrame()
        cache._evict_if_needed()
        assert "a" not in cache._sql_cache
