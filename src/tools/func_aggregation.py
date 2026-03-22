import pandas as pd
import logging

logger = logging.getLogger(__name__)


def compute_end_uses(models: list, end_uses: list[str] | None = None, sort_by: str | None = None) -> pd.DataFrame:
    """Extract End Uses from HTML for multiple models. Returns DataFrame with values in GJ.

    Returns one row per model with all end-use values flattened into columns.
    Column naming: "{EndUse}_{FuelType}_GJ" e.g. "Heating_Natural_Gas_GJ"
    """
    rows = []
    for model in models:
        if not model.html_data:
            continue
        raw_tables = model.html_data.get_data()
        for table_info in raw_tables:
            if table_info["table_name"] != "End Uses":
                continue
            if table_info["report_name"] != "Annual Building Utility Performance Summary":
                continue
            data = table_info["table_data"]
            if not data or len(data) < 2:
                continue
            header = data[0]
            model_row = {"model_id": model.model_id}
            for row_data in data[1:]:
                if not row_data:
                    continue
                end_use_name = row_data[0].strip()
                if end_uses and end_use_name not in end_uses:
                    continue
                for i, col in enumerate(header[1:], 1):
                    col_clean = col.strip().replace(" [GJ]", "").replace(" [m3]", "_m3")
                    col_clean = col_clean.replace(" ", "_")
                    key = f"{end_use_name}_{col_clean}_GJ"
                    try:
                        model_row[key] = float(row_data[i]) if i < len(row_data) else 0.0
                    except (ValueError, IndexError):
                        model_row[key] = 0.0
            rows.append(model_row)

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)

    if sort_by:
        sort_cols = [c for c in df.columns if sort_by in c and "GJ" in c]
        if sort_cols:
            df["_sort"] = df[sort_cols].sum(axis=1)
            df = df.sort_values("_sort", ascending=False).drop("_sort", axis=1)

    return df


def compute_timeseries_stats(model, rddid: int, agg: str = "annual") -> dict:
    """Compute pre-built statistics for a timeseries variable."""
    if not model.sql_data:
        return {"error": "Model has no SQL data"}

    ts = model.sql_data.get_timeseries()
    records = ts.getseries_by_record_id(rddid)
    if not records:
        return {"error": f"No data for RDD ID {rddid}"}

    df = pd.DataFrame(records)
    units = df["Units"].iloc[0]
    name = df["Name"].iloc[0]
    key_value = df["KeyValue"].iloc[0]
    series = df.set_index("dt")["Value"].astype(float)
    series.index = pd.to_datetime(series.index)

    if agg == "annual":
        return {
            "variable": f"{key_value}:{name}",
            "units": units,
            "sum": float(series.sum()),
            "sum_GJ": float(series.sum() / 1e9) if units == "J" else None,
            "mean": float(series.mean()),
            "min": float(series.min()),
            "max": float(series.max()),
            "peak_timestamp": str(series.idxmax()),
            "count": int(len(series)),
        }
    elif agg == "monthly":
        monthly = series.groupby(series.index.month).agg(["sum", "mean", "min", "max"])
        monthly.index.name = "month"
        return monthly.reset_index().to_dict(orient="records")
    elif agg == "daily":
        daily = series.groupby(series.index.date).agg(["sum", "mean", "min", "max"])
        daily.index.name = "date"
        return daily.reset_index().to_dict(orient="records")
    elif agg == "peak_day":
        peak_hour = series.idxmax()
        day_start = peak_hour.normalize()
        day_end = day_start + pd.Timedelta(hours=23)
        day_data = series.loc[day_start:day_end]
        return {
            "peak_date": str(day_start.date()),
            "peak_hour": str(peak_hour),
            "peak_value": float(series.max()),
            "units": units,
            "data": [{"hour": str(idx), "value": float(v)} for idx, v in day_data.items()],
        }
    elif agg == "peak_week":
        peak_hour = series.idxmax()
        week_start = peak_hour.normalize() - pd.Timedelta(days=3)
        week_end = peak_hour.normalize() + pd.Timedelta(days=3, hours=23)
        week_data = series.loc[week_start:week_end]
        daily = week_data.groupby(week_data.index.date).agg(["sum", "mean", "min", "max"])
        return {
            "peak_date": str(peak_hour.normalize().date()),
            "peak_value": float(series.max()),
            "units": units,
            "daily_summary": daily.reset_index().to_dict(orient="records"),
        }

    return {"error": f"Unknown aggregation: {agg}"}
