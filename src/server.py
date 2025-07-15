import plotly.express as px
from src import CACHE_PICKLE, CACHE_DIRECTORY, EPLUS_RUNS_DIRECTORY
from src.model_data import get_model_map, catalog_path, read_model_map_from_cache, get_file_info, initialize_model_map_from_directory, read_or_initialize_model_map, read_or_initialize_model_map

from pathlib import Path
import pickle
import json
from io import StringIO
import pandas as pd
from bs4 import BeautifulSoup
from typing import Literal
from typing import List
from pydantic import BaseModel
import os
import glob as gb
from mcp.server.fastmcp import FastMCP
mcp = FastMCP("eplus_outputs")


@mcp.tool()
def setup_model_map(directory: str = 'eplus_files') -> str:
    """
    Initialize or refresh the model map cache for EnergyPlus models in a specified directory.

    This MCP tool scans a directory for EnergyPlus model files (.epJSON, .sql, .htm) and creates
    a cached model map for efficient access. Use this tool first before accessing model data.

    Args:
        directory (str): Directory containing EnergyPlus model files. Defaults to 'eplus_files'.

    Returns:
        str: Status message confirming successful initialization.

    Usage:
        Call this tool once per session or when the model directory changes to ensure
        the MCP server has an up-to-date inventory of available models.

    Note:
        For comprehensive usage instructions and workflow guidance, use get_usage_instructions().
    """

    initialize_model_map_from_directory(directory)
    return f"Model map initialized successfully for directory: {directory}"



@mcp.tool()
def get_available_models(directory: str = 'eplus_files') -> dict:
    """
    Retrieve a comprehensive list of all available EnergyPlus models in the default directory.

    This MCP tool returns detailed information about all discovered EnergyPlus models,
    including their metadata, file paths, and unique identifiers for use with other tools.

    Args:
        directory (str): Directory parameter (ignored, uses default eplus_files directory).

    Returns:
        dict: List of dictionaries, each containing complete model information:
            - model_id: Unique identifier for use with other MCP tools
            - codename: Model standard (e.g., 'ASHRAE901')
            - prototype: Building type (e.g., 'HotelLarge', 'Warehouse')
            - codeyear: Code year (e.g., 'STD2025')
            - city: Location (e.g., 'Buffalo', 'Tampa')
            - label: HVAC system type (e.g., 'gshp', 'vav_ac_blr')
            - file paths for epJSON, SQL, and HTML files

    Usage:
        Use this tool to discover available models and obtain their model_id values
        for use with other MCP tools that analyze specific models.
    """
    pickle_file = CACHE_PICKLE
    model_map = read_or_initialize_model_map(str(EPLUS_RUNS_DIRECTORY), pickle_file)
    model_summary_table = pd.DataFrame([x.model_dump(mode='json') for x in model_map.models])
    return model_summary_table.to_dict(orient='records')


@mcp.tool()
def get_html_table_names(id: str) -> list | dict:
    """
    Get the names of all HTML tables available in the report for a specific EnergyPlus model.

    This MCP tool extracts the names of all summary tables from an EnergyPlus HTML report,
    allowing you to discover what tabular data is available for analysis.

    Args:
        id (str): The model_id of the EnergyPlus model (obtain from get_available_models).

    Returns:
        list | dict: List or dictionary of available HTML table names such as:
            - 'Annual Building Utility Performance Summary'
            - 'HVAC Sizing Summary'
            - 'Zone Component Loads Summary'
            - 'Equipment Summary'

    Usage:
        Use this tool to explore what summary tables are available in a model's HTML report
        before extracting specific table data for analysis.
    """
    model_map = read_or_initialize_model_map(CACHE_PICKLE, CACHE_DIRECTORY)

    model = model_map.get_model_by_id(id)

    return model.html_data.get_report_names()



@mcp.tool()
def get_sql_available_hourlies(id: str) -> list | dict:
    """
    List all available hourly timeseries variables in the SQL output for a specific EnergyPlus model.

    This MCP tool discovers all hourly timeseries data available in a model's SQL output database,
    providing the variable names and RDD IDs needed to extract specific timeseries data.

    Args:
        id (str): The model_id of the EnergyPlus model (obtain from get_available_models).

    Returns:
        list | dict: List or dictionary of available hourly timeseries variables including:
            - Variable names (e.g., 'Zone Air Temperature', 'HVAC Electric Power')
            - RDD IDs for use with get_timeseries_report_by_rddid
            - Units and key values for each variable

    Usage:
        Use this tool to discover what hourly timeseries data is available in a model
        before extracting specific variables for analysis or visualization.
    """
    model_map = read_or_initialize_model_map(CACHE_PICKLE, CACHE_DIRECTORY)
    model = model_map.get_model_by_id(id)
    results = model.sql_data.get_timeseries().availseries()
    return results


@mcp.tool()
def get_epjson_dict(id: str) -> dict:
    """
    Retrieve the complete epJSON input model data for a specific EnergyPlus model.

    This MCP tool returns the full epJSON input file as a Python dictionary, providing
    access to all building geometry, materials, systems, and simulation settings.

    Args:
        id (str): The model_id of the EnergyPlus model (obtain from get_available_models).

    Returns:
        dict: Complete epJSON data structure containing all model input parameters:
            - Building geometry and zones
            - Construction materials and assemblies
            - HVAC system definitions
            - Schedules and control strategies
            - Simulation settings and output variables

    Usage:
        Use this tool to inspect or analyze the input parameters of an EnergyPlus model,
        such as building characteristics, system configurations, or simulation settings.

    Warning:
        This returns the complete model data and may be very large. Consider using
        targeted analysis rather than processing the entire dictionary.
    """
    model_map = read_or_initialize_model_map(CACHE_PICKLE, CACHE_DIRECTORY)

    model = model_map.get_model_by_id(id)

    return model.epjson_data.get_data()


@mcp.tool()
def get_timeseries_report_by_rddid(model_id, rddid: int) -> list[dict]:
    """
    Retrieve hourly timeseries data for a specific variable from an EnergyPlus model's SQL output.

    This MCP tool extracts complete hourly timeseries data for a specific variable using its
    RDD (Report Data Dictionary) ID, providing timestamped values for analysis and visualization.

    Args:
        model_id (str): The model_id of the EnergyPlus model (obtain from get_available_models).
        rddid (int): The RDD ID for the desired variable (obtain from get_sql_available_hourlies).

    Returns:
        list[dict]: List of timestamped records, each containing:
            - dt: Timestamp for the data point
            - Value: Numeric value for the variable
            - Name: Variable name (e.g., 'Zone Air Temperature')
            - KeyValue: Zone or component identifier
            - Units: Units of measurement

    Usage:
        Use this tool to extract specific timeseries data for analysis, visualization,
        or comparison between different models or time periods. The data is ready for
        use with pandas DataFrame or plotting libraries.

    Example:
        To get zone air temperature data, first use get_sql_available_hourlies to find
        the RDD ID for 'Zone Air Temperature', then use that ID with this tool.
    """
    model_map = read_or_initialize_model_map(CACHE_PICKLE, CACHE_DIRECTORY)
    model = model_map.get_model_by_id(model_id)
    res = model.sql_data.get_timeseries().getseries_by_record_id(rddid)

    return res



@mcp.tool()
def get_usage_instructions() -> str:
    """
    Get comprehensive usage instructions for the EnergyPlus MCP server.

    This MCP tool returns detailed documentation about how to use all the available tools,
    including workflow guidance, data structures, and best practices.

    Returns:
        str: Complete usage instructions and documentation for the MCP server.

    Usage:
        Call this tool when you need guidance on how to use the EnergyPlus MCP server
        or want to understand the available data and workflows.
    """
    try:
        with open('src/CLAUDE.md', 'r') as f:
            return f.read()
    except FileNotFoundError:
        return "Usage instructions file not found. Please ensure CLAUDE.md exists in the src directory."
    except Exception as e:
        return f"Error reading usage instructions: {str(e)}"


# @mcp.tool()
# def plot_timeseries_line(model_id, rddid):
#     """
#     Retrieve hourly timeseries data for a specific variable by RDD (Report Data Dictionary) ID from an EnergyPlus model's SQL output and plot it.
#     Args:
#         model_id (str): The model_id of the EnergyPlus model to query.
#         rddid (int): The RDD (variable) ID for which to extract timeseries data.
#     Returns:
#         list[dict]: List of records, each containing timestamped values for the requested variable.
#     Description:
#         Loads the model map, locates the model by model_id, initializes the SQL object if needed, and retrieves the hourly timeseries data for the specified RDD ID. Useful for programmatic extraction and analysis of simulation results for a specific variable.
#     """
#     model_map = read_or_initialize_model_map(CACHE_PICKLE, CACHE_DIRECTORY)
#     model = model_map.get_model_by_id(model_id)

#     res = model.sql_data.get_timeseries().getseries_by_record_id(rddid)

#     pdf = pd.DataFrame(res)

#     title = ' | '.join(pdf[['Name', "KeyValue", "Units"]].iloc[0, :].values)

#     fig = px.line(
#         pdf,
#         x='dt', y='Value', title=title
#     )

#     fileout = os.path.abspath('cache/tempplot.html')

#     # fightml = fig.to_html()

#     fig.write_html(fileout)

#     return fileout
