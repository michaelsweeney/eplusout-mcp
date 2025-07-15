#!/usr/bin/env python3
"""
FastMCP server for building stock analysis.
"""

import pandas as pd
import numpy as np
import glob as gb
from fastmcp import FastMCP

import os

mcp = FastMCP("EPlus Outputs")





# @mcp.tool()
# @ensure_readme_first()
# def apply_demo_rate_for_projection_year(file_hash: str, projection_year: int, filepath: str = None) -> str:

#     """
#     Apply the demolition rate for a given projection year to the cached DataFrame.

#     Args:
#         file_hash (str): Hash of the loaded parquet file to modify.
#         projection_year (int): The projection year for which to apply the demolition rate.
#         filepath (str, optional): Path to the parquet file, used if file_hash is not found.

#     Returns:
#         str: Hash for the new modified dataset.

#     Raises:
#         ValueError: If file_hash is not found and filepath is not provided.
#     """
#     description = f"Applied demolition rate for {projection_year}. Building hash: {file_hash}"

#     try:
#         return handler.create_modified_dataset(file_hash, description, apply_demo_rate_to_df_for_projection_year, function_args={'projection_year': projection_year})
#     except KeyError:
#         if filepath is None:
#             raise ValueError("File hash not found and no filepath provided to reload parquet file.")
#         # Load the parquet file and get the new hash
#         new_hash = handler.load_parquet_file(filepath)
#         return handler.create_modified_dataset(new_hash, description, apply_demo_rate_to_df_for_projection_year, function_args={'projection_year': projection_year})


# @mcp.tool()
# @ensure_readme_first()
# def get_target_summary_for_year(file_hash: str, target_year: int, state: ENUM_STATE_SHORT, filepath: str = None) -> str:

#     """
#     Generate a target summary for a given target year and state from the cached DataFrame.

#     Args:
#         file_hash (str): Hash of the loaded parquet file to summarize.
#         target_year (int): The target year to be pulled from the targets file.
#         state (ENUM_STATE_SHORT): State abbreviation.
#         filepath (str, optional): Path to the parquet file, used if file_hash is not found.

#     Returns:
#         str: Hash for the new summary dataset.

#     Raises:
#         ValueError: If file_hash is not found and filepath is not provided.
#     """
#     description = f"Target Summary for {target_year}, {state}. Building hash: {file_hash}"

#     try:
#         return handler.create_modified_dataset(file_hash, description, get_target_summary, function_args={'projection_year': target_year, 'state': state})
#     except KeyError:
#         if filepath is None:
#             raise ValueError("File hash not found and no filepath provided to reload parquet file.")
#         # Load the parquet file and get the new hash
#         new_hash = handler.load_parquet_file(filepath)
#         return handler.create_modified_dataset(new_hash, description, get_target_summary, function_args={'projection_year': target_year, 'state': state})


# @mcp.tool()
# @ensure_readme_first()
# def filter_by_minimum_sf(file_hash: str, min_area: int, filepath: str = None) -> str:
#     """
#     Filter the cached DataFrame for buildings with square footage greater than or equal to min_area.


#     Args:
#         file_hash (str): Hash of the loaded parquet file to filter.
#         min_area (int): Minimum building square footage to include.
#         filepath (str, optional): Path to the parquet file, used if file_hash is not found.

#     Users should provide filepath if they expect the hash might not be cached.

#     Returns:
#         str: Hash for the new filtered dataset.
#     """

#     description = f"Filtered for buildings >= {min_area} sq ft"

#     def apply_func(df: pd.DataFrame):
#         return df.loc[df[WEIGHTED_BLDG_SF] >= min_area]

#     try:
#         return handler.create_modified_dataset(file_hash, description, apply_func)
#     except KeyError:
#         if filepath is None:
#             raise ValueError("File hash not found and no filepath provided to reload parquet file.")
#         # Load the parquet file and get the new hash
#         new_hash = handler.load_parquet_file(filepath)
#         return handler.create_modified_dataset(new_hash, description, apply_func)


# @mcp.tool()
# @ensure_readme_first()
# def filter_by_county(file_hash: str, county: str, filepath: str = None) -> str:
#     """
#     Filter the cached DataFrame for buildings in the specified county.

#     Args:
#         file_hash (str): Hash of the loaded parquet file to filter.
#         county (str): County name to filter by.
#         filepath (str, optional): Path to the parquet file, used if file_hash is not found.

#     Users should provide filepath if they expect the hash might not be cached.

#     Returns:
#         str: Hash for the new filtered dataset.
#     """
#     description = f"Filtered for county: {county}"

#     def apply_func(df: pd.DataFrame):
#         return df.loc[df[COUNTY_NAME] == county]

#     try:
#         return handler.create_modified_dataset(file_hash, description, apply_func)
#     except KeyError:
#         if filepath is None:
#             raise ValueError("File hash not found and no filepath provided to reload parquet file.")
#         # Load the parquet file and get the new hash
#         new_hash = handler.load_parquet_file(filepath)
#         return handler.create_modified_dataset(new_hash, description, apply_func)


# @mcp.tool()
# @ensure_readme_first()
# def filter_by_building_type_group(file_hash: str, building_type_group: ENUM_BUILDING_TYPE_GROUP, filepath: str = None) -> str:
#     """
#     Filter the cached DataFrame for buildings in the specified building type group.

#     Args:
#         file_hash (str): Hash of the loaded parquet file to filter.
#         building_type_group (ENUM_BUILDING_TYPE_GROUP): Building type group to filter by.
#         filepath (str, optional): Path to the parquet file, used if file_hash is not found.

#     Users should provide filepath if they expect the hash might not be cached.

#     Returns:
#         str: Hash for the new filtered dataset.
#     """
#     description = f"Filtered for building type group: {building_type_group}"

#     def apply_func(df: pd.DataFrame, **kwargs):
#         return df.loc[df[BUILDING_TYPE_GROUP] == building_type_group]

#     try:
#         return handler.create_modified_dataset(file_hash, description, apply_func)
#     except KeyError:
#         if filepath is None:
#             raise ValueError("File hash not found and no filepath provided to reload parquet file.")
#         # Load the parquet file and get the new hash
#         new_hash = handler.load_parquet_file(filepath)
#         return handler.create_modified_dataset(new_hash, description, apply_func)


# @mcp.tool()
# @ensure_readme_first()
# def list_available_parquet_files() -> list:
#     """
#     Return a list of available parquet files in the PARQUET_PATH directory.

#     Returns:
#         list: List of file paths to available parquet files.
#     """
#     return gb.glob(PARQUET_PATH + '*.parquet')


# @mcp.tool()
# @ensure_readme_first()
# def load_parquet_file(filepath: str, force_reload: bool = False) -> str:
#     """
#     Load a parquet file and generate a summary.

#     Args:
#         filepath (str): Path to the parquet file to load.
#         force_reload (bool, optional): If True, reload the file even if cached.

#     Returns:
#         str: Summary of the loaded parquet file.
#     """
#     return handler.load_parquet_file(filepath, force_reload)


# @mcp.tool()
# @ensure_readme_first()
# def execute_query(file_hash: str, query: str) -> str:
#     """
#     Execute a pandas query on the cached DataFrame.

#     Args:
#         file_hash (str): Hash of the loaded parquet file to query.
#         query (str): The pandas query to execute.

#     Returns:
#         str: Formatted result of the query.
#     """
#     return handler.execute_query(file_hash, query)


# @mcp.tool()
# @ensure_readme_first()
# def execute_multiline_query(file_hash: str, query: str) -> str:
#     """
#     Execute multi-line pandas operations on the cached DataFrame.

#     Args:
#         file_hash (str): Hash of the loaded parquet file to query.
#         query (str): Multi-line Python code to execute.

#     Returns:
#         str: Formatted result or status message.
#     """
#     return handler.execute_multiline_query(file_hash, query)


# @mcp.tool()
# @ensure_readme_first()
# def list_cached_files() -> str:
#     """
#     List all currently cached parquet files.

#     Returns:
#         str: Information about cached parquet files.
#     """
#     return handler.list_cached_files()


# @mcp.tool()
# @ensure_readme_first()
# def get_file_columns(file_hash: str) -> str:
#     """
#     Get column names and types from a loaded parquet file.

#     Args:
#         file_hash (str): Hash of the loaded parquet file.

#     Returns:
#         str: List of columns and their data types.
#     """
#     return handler.get_file_columns(file_hash)


# @mcp.tool()
# @ensure_readme_first()
# def get_file_sample(file_hash: str, n_rows: int = 10) -> str:
#     """
#     Get a sample of rows from the loaded parquet data.

#     Args:
#         file_hash (str): Hash of the loaded parquet file.
#         n_rows (int, optional): Number of rows to sample (default 10).

#     Returns:
#         str: Sampled data as a string.
#     """
#     return handler.get_file_sample(file_hash, n_rows)


# @mcp.tool()
# @ensure_readme_first()
# def write_df_to_csv(file_hash: str, fname: str) -> str:
#     """
#     Write the cached DataFrame corresponding to the given file hash to a CSV file.

#     Args:
#         file_hash (str): Hash of the loaded parquet file whose DataFrame will be written.
#         fname (str): Name of the output CSV file (not a full path; will be saved in MCP_OUTPUT_PATH). Should have ".csv" at the end.

#     Returns:
#         str: Path to the written CSV file.
#     """
#     df = handler._get_dataframe_from_hash(file_hash)
#     file_out = os.path.join(MCP_OUTPUT_PATH, fname)
#     df.to_csv(file_out)


if __name__ == "__main__":
    # Run with stdio transport for MCP
    mcp.run(transport="stdio")
