import plotly.express as px
from src import CACHE_PICKLE, CACHE_DIRECTORY
from src.model_data import get_model_map, catalog_path, read_model_map_from_cache, get_file_info, initialize_model_map_from_directory, read_or_initialize_model_map


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

# This is the shared MCP server instance
mcp = FastMCP("eplus_outputs")




@mcp.tool()
def setup_model_map(directory: str = 'eplus_files') -> str:
    """
    Initialize or refresh the model map cache for EnergyPlus models in a specified directory.
    Args:
        directory (str): Directory containing EnergyPlus model files. Defaults to 'eplus_files'.
    Returns:
        str: Status message indicating the result of the operation.
    Description:
        Loads and summarizes all EnergyPlus model files in the given directory, updating the model map cache for fast access in later operations.
    """

    initialize_model_map_from_directory(directory)
    return f"Model map initialized successfully for directory: {directory}"







@mcp.tool()
def get_available_models(directory: str) -> dict:
    """
    Retrieve a summary of all available EnergyPlus models in a specified directory.
    Args:
        directory (str): Path to the directory containing EnergyPlus model results.
    Returns:
        dict: Dictionary containing summary information for each model, including model_id, prototype, label, and file paths.
    Description:
        Loads the model map from the specified directory and returns a summary of all discovered EnergyPlus models. Useful for listing, filtering, or reporting on available models.
    """
    pickle_file = os.path.join(directory, 'modelmap.pickle')
    model_map = read_or_initialize_model_map(pickle_file, directory)
    model_summary_table = pd.DataFrame([x.model_dump(mode='json') for x in model_map.models])
    return model_summary_table.to_dict(orient='records')


# @mcp.tool()
# def get_html_table_names(id: str) -> list | dict:
#     """
#     Get the names of all HTML tables available in the report for a specific EnergyPlus model.
#     Args:
#         id (str): The model_id of the EnergyPlus model.
#     Returns:
#         list | dict: List or dictionary of available HTML table names in the model's report.
#     Description:
#         Looks up the specified model by model_id and returns the names of all tables found in its HTML report file. Useful for exploring available report data.
#     """
#     model_map = read_or_load_model_map(CACHE_PICKLE, CACHE_DIRECTORY)

#     model = model_map.get_model_by_id(id)

#     return model.html_data.get_report_names()



# @mcp.tool()
# def get_sql_available_hourlies(id: str) -> list | dict:
#     """
#     List all available hourly timeseries report names in the SQL output for a specific EnergyPlus model.
#     Args:
#         id (str): The model_id of the EnergyPlus model.
#     Returns:
#         list | dict: List or dictionary of available hourly timeseries report names in the model's SQL output.
#     Description:
#         Looks up the specified model by model_id and returns all available hourly timeseries report names from its SQL output. Useful for selecting timeseries data for analysis.
#     """
#     model_map = read_or_load_model_map(CACHE_PICKLE, CACHE_DIRECTORY)
#     model = model_map.get_model_by_id(id)
#     results = model.sql_data.get_timeseries().availseries()
#     return results


# @mcp.tool()
# def get_epjson_dict(id: str) -> dict:
#     """
#     Retrieve the parsed epJSON dictionary for a specific EnergyPlus model.
#     Args:
#         id (str): The model_id of the EnergyPlus model.
#     Returns:
#         dict: Parsed epJSON data structure for the specified model.
#     Description:
#         Looks up the specified model by model_id and returns its parsed epJSON data as a Python dictionary. Useful for programmatic inspection or manipulation of the model structure.
#     """
#     model_map = read_or_load_model_map(CACHE_PICKLE, CACHE_DIRECTORY)

#     model = model_map.get_model_by_id(id)

#     return model.epjson_data.get_data()


# @mcp.tool()
# def get_timeseries_report_by_rddid(model_id, rddid: int) -> list[dict]:
#     """
#     Retrieve hourly timeseries data for a specific variable by RDD (Report Data Dictionary) ID from an EnergyPlus model's SQL output.
#     Args:
#         model_id (str): The model_id of the EnergyPlus model to query.
#         rddid (int): The RDD (variable) ID for which to extract timeseries data.
#     Returns:
#         list[dict]: List of records, each containing timestamped values for the requested variable.
#     Description:
#         Loads the model map, locates the model by model_id, initializes the SQL object if needed, and retrieves the hourly timeseries data for the specified RDD ID. Useful for programmatic extraction and analysis of simulation results for a specific variable.
#     """
#     model_map = read_or_load_model_map(CACHE_PICKLE, CACHE_DIRECTORY)
#     model = model_map.get_model_by_id(model_id)
#     res = model.sql_data.get_timeseries().getseries_by_record_id(rddid)

#     return res



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
#     model_map = read_or_load_model_map(CACHE_PICKLE, CACHE_DIRECTORY)
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
