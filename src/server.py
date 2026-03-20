from pathlib import Path
import pandas as pd
import logging
import json

from typing import Any
from mcp.server.fastmcp import FastMCP
from src.monitor import log_mcp_call
from src.model_data import initialize_model_map_from_directory

logger = logging.getLogger(__name__)

mcp = FastMCP("eplus_outputs")

DEFAULT_DIRECTORY = 'example-files'
MAX_RESPONSE_CHARS = 10000


def _truncate_response(result, label: str = "result"):
    """Truncate a response if it exceeds MAX_RESPONSE_CHARS."""
    text = json.dumps(result, default=str) if not isinstance(result, str) else result

    if len(text) <= MAX_RESPONSE_CHARS:
        return result

    if isinstance(result, list):
        total = len(result)
        for i in range(total, 0, -1):
            subset = json.dumps(result[:i], default=str)
            if len(subset) <= MAX_RESPONSE_CHARS - 200:
                return {
                    "truncated": True,
                    "showing": i,
                    "total_rows": total,
                    "message": f"Response truncated: showing {i} of {total} rows. Request a more specific query to see all data.",
                    label: result[:i]
                }
        return {
            "truncated": True,
            "total_rows": total,
            "message": f"Response too large ({total} rows). Request a more specific query."
        }

    return {
        "truncated": True,
        "total_chars": len(text),
        "message": f"Response too large ({len(text)} chars). Request a more specific query."
    }


# Global state
_model_map = None


def _get_model_map():
    """Get the current model map, raising if not initialized."""
    if _model_map is None:
        raise ValueError(
            "Model map not initialized. Call initialize_model_map(directory) first."
        )
    return _model_map


@mcp.tool()
def initialize_model_map(directory: str = DEFAULT_DIRECTORY) -> str:
    """Scan a directory for EnergyPlus model files (.epJSON, .sql, .htm) and build a model catalog. Call this first."""

    global _model_map
    target_path = Path(directory).resolve()
    if not target_path.exists():
        raise ValueError(f"Directory does not exist: {target_path}")
    if not target_path.is_dir():
        raise ValueError(f"Path is not a directory: {target_path}")

    _model_map = initialize_model_map_from_directory(directory)
    model_count = len(_model_map.models)
    result = f"Model map initialized successfully for directory: {directory} ({model_count} models found)"
    log_mcp_call('initialize_model_map', result, kwargs={'directory': directory})
    return result


@mcp.tool()
def get_available_models() -> list:
    """List all discovered models with IDs, file types, and file paths for direct access."""

    model_map = _get_model_map()
    result = [x.get_basic_attributes() for x in model_map.models]
    log_mcp_call('get_available_models', result)
    return result


@mcp.tool()
def search_html_tables_by_keyword(id: str, keywords: str | list[str], case_sensitive: bool = False) -> dict:
    """Search for HTML report tables matching keywords in table/report names. Returns list of (report_for, report_name, table_name) tuples for use with get_html_table_by_tuple."""

    if isinstance(keywords, str):
        keywords = [keywords]

    model_map = _get_model_map()
    model = model_map.get_model_by_id(id)
    report_data = model.html_data.get_report_names()

    matching_tables = []

    if isinstance(report_data, list):
        for table_info in report_data:
            if isinstance(table_info, tuple):
                combined_text = ' '.join(str(field) for field in table_info)
                search_text = combined_text if case_sensitive else combined_text.lower()
                search_keywords = keywords if case_sensitive else [kw.lower() for kw in keywords]

                if any(keyword in search_text for keyword in search_keywords):
                    matching_tables.append(table_info)

    result = {
        "total_matches": len(matching_tables),
        "matching_tables": matching_tables,
    }

    log_mcp_call(
        'search_html_tables_by_keyword', result,
        kwargs={'id': id, 'keywords': keywords, 'case_sensitive': case_sensitive}
    )
    return result


@mcp.tool()
def get_html_table_by_tuple(id: str, query_tuple: tuple) -> list[dict]:
    """Retrieve a specific HTML table using a (report_for, report_name, table_name) tuple from search results."""

    model_map = _get_model_map()
    model = model_map.get_model_by_id(id)
    table = model.html_data.get_table_by_tuple(query_tuple, asjson=True)

    log_mcp_call(
        'get_html_table_by_tuple', table,
        kwargs={'id': id, 'query_tuple': query_tuple}
    )
    return _truncate_response(table, "rows")


@mcp.tool()
def get_sql_available_hourlies(id: str) -> list | dict:
    """List available hourly timeseries variables with RDD IDs for use with get_timeseries_report_by_rddid_list."""

    model_map = _get_model_map()
    model = model_map.get_model_by_id(id)
    result = model.sql_data.get_timeseries().availseries()

    log_mcp_call('get_sql_available_hourlies', result, kwargs={'id': id})
    return _truncate_response(result, "variables")


@mcp.tool()
def get_timeseries_report_by_rddid_list(model_id: str, rddid: int | list[int]) -> Any:
    """Extract hourly timeseries data by RDD ID(s). Returns columnar data with datetime index."""

    if isinstance(rddid, int):
        rddid = [rddid]

    model_map = _get_model_map()
    model = model_map.get_model_by_id(model_id)

    dflist = []
    for rdd in rddid:
        if not isinstance(rdd, int) or rdd <= 0:
            raise ValueError(f"Invalid RDD ID: {rdd}. Must be a positive integer.")
        r = model.sql_data.get_timeseries().getseries_by_record_id(rdd)
        tr = r[0]
        r_lbl = f'{tr["KeyValue"]}-{tr["Name"]}-{tr["TimestepType"]}-{tr["Units"]}'
        dfr = pd.DataFrame(r).set_index('dt')
        dfr = dfr.rename({"Value": r_lbl}, axis=1)
        dflist.append(dfr[r_lbl])

    dff = pd.concat(dflist, axis=1)
    split = dff.reset_index().to_dict(orient='split')
    result = {"columns": split["columns"], "data": split["data"]}

    log_mcp_call(
        'get_timeseries_report_by_rddid_list', f'{len(result)} records',
        kwargs={'model_id': model_id, 'rddid': rddid}
    )
    return _truncate_response(result, "records")
