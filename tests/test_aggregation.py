import pytest
import pandas as pd
from src.tools.func_aggregation import compute_end_uses, compute_timeseries_stats


class TestEndUses:
    def test_returns_dataframe(self, buffalo_model):
        result = compute_end_uses([buffalo_model])
        assert isinstance(result, pd.DataFrame)

    def test_has_model_id_column(self, buffalo_model):
        result = compute_end_uses([buffalo_model])
        assert "model_id" in result.columns

    def test_heating_value_matches_known(self, buffalo_model):
        result = compute_end_uses([buffalo_model])
        row = result[result["model_id"].str.contains("Buffalo")]
        heat_gas_cols = [c for c in result.columns if "Heating" in c and "Natural_Gas" in c]
        assert len(heat_gas_cols) >= 1, f"No Heating Natural Gas column found. Columns: {list(result.columns)}"
        assert abs(float(row[heat_gas_cols[0]].iloc[0]) - 1484.28) < 0.1

    def test_multiple_models(self, atlanta_model, buffalo_model):
        result = compute_end_uses([atlanta_model, buffalo_model])
        assert len(result) == 2

    def test_sort_by(self, atlanta_model, buffalo_model):
        result = compute_end_uses([atlanta_model, buffalo_model], sort_by="Heating")
        assert "Buffalo" in result.iloc[0]["model_id"]


class TestTimeseriesStats:
    def test_annual_returns_dict(self, buffalo_model):
        result = compute_timeseries_stats(buffalo_model, rddid=179, agg="annual")
        assert "sum" in result
        assert "max" in result
        assert "peak_timestamp" in result

    def test_annual_sum_matches_known(self, buffalo_model):
        result = compute_timeseries_stats(buffalo_model, rddid=179, agg="annual")
        gj = result["sum"] / 1e9
        assert abs(gj - 5105.50) < 0.1

    def test_monthly_returns_12_rows(self, buffalo_model):
        result = compute_timeseries_stats(buffalo_model, rddid=179, agg="monthly")
        assert len(result) == 12

    def test_peak_day_returns_24_hours(self, buffalo_model):
        result = compute_timeseries_stats(buffalo_model, rddid=179, agg="peak_day")
        assert len(result["data"]) == 24

    def test_units_metadata_present(self, buffalo_model):
        result = compute_timeseries_stats(buffalo_model, rddid=179, agg="annual")
        assert "units" in result
