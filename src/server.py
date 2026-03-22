from pathlib import Path
import pandas as pd
import logging
import json

from typing import Any
from mcp.server.fastmcp import FastMCP
from src.monitor import log_mcp_call
from src.model_data import initialize_model_map_from_directory
from src.sandbox import validate_code, execute_sandboxed, SandboxViolation
from src.data_loader import DataCache

logger = logging.getLogger(__name__)

mcp = FastMCP("eplus_outputs")

DEFAULT_DIRECTORY = 'example-files'
SCHEMA_DIR = Path(__file__).parent.parent / "schema"
MAX_RESPONSE_CHARS = 50000
DOCS_PATH = Path(__file__).parent / "CLAUDE.md"


@mcp.resource("eplus://docs")
def get_docs() -> str:
    """EnergyPlus MCP server usage instructions and reference links."""
    with open(DOCS_PATH) as f:
        return f.read()


# Schema cache: {filepath: parsed_json}
_schema_cache: dict[str, dict] = {}


def _load_schema(version: str | None = None) -> tuple[dict, str]:
    """Load and cache an EnergyPlus schema file. Returns (schema_properties, version_string)."""
    if version:
        schema_file = SCHEMA_DIR / f"Energy+.schema.{version}.epJSON"
        if not schema_file.exists():
            schema_file = SCHEMA_DIR / "Energy+.schema.epJSON"
            if not schema_file.exists():
                raise ValueError(
                    f"No schema found for version '{version}'. "
                    f"Place schema files in {SCHEMA_DIR}/ as 'Energy+.schema.epJSON' "
                    f"or 'Energy+.schema.{{version}}.epJSON'."
                )
    else:
        schema_file = SCHEMA_DIR / "Energy+.schema.epJSON"
        if not schema_file.exists():
            raise ValueError(f"No schema found at {schema_file}. Place an EnergyPlus schema file in {SCHEMA_DIR}/.")

    key = str(schema_file)
    if key not in _schema_cache:
        with open(schema_file) as f:
            _schema_cache[key] = json.load(f)

    schema = _schema_cache[key]
    # Detect version from the Version object's default
    ver = "unknown"
    ver_obj = schema.get("properties", {}).get("Version", {})
    pat_props = ver_obj.get("patternProperties", {})
    for v in pat_props.values():
        ver = str(v.get("properties", {}).get("version_identifier", {}).get("default", "unknown"))
    return schema.get("properties", {}), ver


def _summarize_object_schema(obj_def: dict) -> dict:
    """Extract a compact summary from a raw schema object definition."""
    inner = {}
    for v in obj_def.get("patternProperties", {}).values():
        inner = v
        break

    fields = []
    for fname, fdef in inner.get("properties", {}).items():
        field = {"name": fname}
        if "type" in fdef:
            field["type"] = fdef["type"]
        elif "anyOf" in fdef:
            field["type"] = "/".join(t.get("type", "?") for t in fdef["anyOf"] if "type" in t)
        if "units" in fdef:
            field["units"] = fdef["units"]
        if "enum" in fdef:
            field["enum"] = fdef["enum"]
        if "note" in fdef:
            field["note"] = fdef["note"]
        if "default" in fdef:
            field["default"] = fdef["default"]
        if "minimum" in fdef:
            field["minimum"] = fdef["minimum"]
        if "maximum" in fdef:
            field["maximum"] = fdef["maximum"]
        fields.append(field)

    return {
        "group": obj_def.get("group", ""),
        "memo": obj_def.get("memo", ""),
        "fields": fields,
    }


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
_data_cache = DataCache(max_size=5)


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
    _data_cache.clear()
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
def get_html_table_by_tuple(id: str, query_tuple: tuple) -> dict | list:
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


@mcp.tool()
def execute_pandas(model_id: str, code: str) -> dict:
    """Execute Python/pandas code against a model's pre-loaded data.

    Available variables in the execution environment:
    - sql_ts: DataFrame of hourly timeseries (datetime index, one column per variable).
              Column names include units, e.g. "None:Electricity:Facility [J]".
              Values are in source units (J for energy, W for power).
    - html_tables: dict of {(report_for, report_name, table_name): DataFrame}.
              All HTML summary tables as DataFrames with proper headers.
    - model_info: dict with model metadata (id, file_paths, file_types).
    - pd: pandas module
    - np: numpy module

    The last expression in the code is returned as the result.
    No filesystem, network, or import access. 30-second timeout.
    """
    try:
        validate_code(code)
    except SandboxViolation as e:
        return {"error": f"Code validation failed: {e}"}

    model_map = _get_model_map()
    model = model_map.get_model_by_id(model_id)

    data_globals = {"model_info": model.get_basic_attributes()}

    if model.sql_data:
        data_globals["sql_ts"] = _data_cache.get_sql_ts(
            model_id, model.sql_data.file_path
        )
    else:
        data_globals["sql_ts"] = pd.DataFrame()

    if model.html_data:
        data_globals["html_tables"] = _data_cache.get_html_tables(
            model_id, model.html_data.file_path
        )
    else:
        data_globals["html_tables"] = {}

    result = execute_sandboxed(code, data_globals)
    log_mcp_call("execute_pandas", result, kwargs={"model_id": model_id, "code": code[:200]})
    return result


@mcp.tool()
def get_eplus_object_schema(object_type: str, version: str | None = None) -> dict:
    """Look up an EnergyPlus object type's field definitions, types, units, and constraints from the schema. Use exact object type names (e.g., 'Coil:Cooling:WaterToAirHeatPump:EquationFit')."""

    properties, schema_ver = _load_schema(version)

    if object_type not in properties:
        # Try case-insensitive match
        match = next((k for k in properties if k.lower() == object_type.lower()), None)
        if match:
            object_type = match
        else:
            # Return suggestions
            query = object_type.lower()
            suggestions = [k for k in properties if query in k.lower()][:20]
            return {
                "error": f"Object type '{object_type}' not found in schema (v{schema_ver})",
                "suggestions": suggestions,
                "total_object_types": len(properties),
            }

    summary = _summarize_object_schema(properties[object_type])
    result = {
        "object_type": object_type,
        "schema_version": schema_ver,
        **summary,
    }

    log_mcp_call('get_eplus_object_schema', f'{len(summary["fields"])} fields', kwargs={'object_type': object_type, 'version': version})
    return _truncate_response(result, "fields")
