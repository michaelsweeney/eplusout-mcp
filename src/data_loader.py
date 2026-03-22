import pandas as pd
import logging
from collections import OrderedDict
from src.tools.func_sql import SqlTimeseries
from src.tools.func_html import get_all_table_data

logger = logging.getLogger(__name__)


def load_sql_timeseries(sql_path: str) -> pd.DataFrame:
    """Load all hourly timeseries from a SQL file into a single DataFrame.

    Returns DataFrame with:
    - DatetimeIndex (8760 rows for annual, fewer for design-day)
    - One column per RDD variable, named "{KeyValue}:{Name} [{Units}]"
    """
    ts = SqlTimeseries(sql_file=sql_path)
    avail = ts.availseries()

    if not avail:
        return pd.DataFrame()

    dfs = []
    for var in avail:
        rdd_id = var["ReportDataDictionaryIndex"]
        records = ts.getseries_by_record_id(rdd_id)
        if not records:
            continue
        df = pd.DataFrame(records)
        key = df["KeyValue"].iloc[0]
        name = df["Name"].iloc[0]
        units = df["Units"].iloc[0]
        col_name = f"{key}:{name} [{units}]"
        series = df.set_index("dt")["Value"].rename(col_name)
        dfs.append(series)

    if not dfs:
        return pd.DataFrame()

    result = pd.concat(dfs, axis=1)
    result.index = pd.to_datetime(result.index)
    result.index.name = "datetime"
    return result


def load_html_tables(html_path: str) -> dict[tuple, pd.DataFrame]:
    """Load all HTML tables into a dict of DataFrames.

    Returns dict keyed by (report_for, report_name, table_name) tuples.
    Each DataFrame has proper column headers.
    """
    raw_tables = get_all_table_data(html_path)
    result = {}

    for table_info in raw_tables:
        key = (
            table_info["report_for"],
            table_info["report_name"],
            table_info["table_name"],
        )
        raw_data = table_info["table_data"]
        if not raw_data or len(raw_data) < 2:
            result[key] = pd.DataFrame()
            continue

        df = pd.DataFrame(raw_data[1:], columns=raw_data[0])
        result[key] = df

    return result


class DataCache:
    """LRU cache for loaded DataFrames. Evicts oldest when max_size exceeded."""

    def __init__(self, max_size: int = 5):
        self.max_size = max_size
        self._sql_cache: OrderedDict[str, pd.DataFrame] = OrderedDict()
        self._html_cache: OrderedDict[str, dict] = OrderedDict()

    def get_sql_ts(self, model_id: str, sql_path: str) -> pd.DataFrame:
        if model_id in self._sql_cache:
            self._sql_cache.move_to_end(model_id)
            return self._sql_cache[model_id]
        df = load_sql_timeseries(sql_path)
        self._sql_cache[model_id] = df
        self._evict_if_needed()
        return df

    def get_html_tables(self, model_id: str, html_path: str) -> dict:
        if model_id in self._html_cache:
            self._html_cache.move_to_end(model_id)
            return self._html_cache[model_id]
        tables = load_html_tables(html_path)
        self._html_cache[model_id] = tables
        self._evict_if_needed()
        return tables

    def _evict_if_needed(self):
        while len(self._sql_cache) > self.max_size:
            evicted_key, _ = self._sql_cache.popitem(last=False)
            logger.debug(f"Evicted SQL cache: {evicted_key}")
        while len(self._html_cache) > self.max_size:
            evicted_key, _ = self._html_cache.popitem(last=False)
            logger.debug(f"Evicted HTML cache: {evicted_key}")

    def clear(self):
        self._sql_cache.clear()
        self._html_cache.clear()
