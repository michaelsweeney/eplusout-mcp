from pathlib import Path
import time
import pandas as pd
import glob as gb


from typing import Any
from mcp.server.fastmcp import FastMCP
from src.monitor import log_mcp_call
from src import CACHE_PICKLE, EPLUS_RUNS_DIRECTORY
from src.model_data import initialize_model_map_from_directory, read_or_initialize_model_map
from src.dataloader import execute_pandas_query, execute_multiline_pandas_query

mcp = FastMCP("eplus_outputs")

DEFAULT_DIRECTORY = 'eplus_files/prescriptive_variability_sample'
ERROR_CHECK_DIRECTORY = 'eplus_files/forced_error/error'

@mcp.tool()
def initialize_model_map(directory: str = DEFAULT_DIRECTORY) -> str:

    """
    Initialize or refresh the model map cache for EnergyPlus models.

    Scans a directory recursively for EnergyPlus model files (.epJSON, .sql, .htm) and creates
    a cached model map for efficient access. Files are grouped by directory and filename stem,
    so 'mydir/model1.sql' and 'mydir/model1.epJSON' will be recognized as part of the same model.
    Call this first before accessing model data.

    Args:
        directory: Directory containing EnergyPlus model files. Defaults to 'DEFAULT_DIRECTORY'.
                  Subdirectories will be scanned recursively.

    Returns:
        Status message confirming successful initialization.
    """

    initialize_model_map_from_directory(directory)
    result = f"Model map initialized successfully for directory: {directory}"
    log_mcp_call('setup_model_map', result, kwargs={'directory': directory})

    return result


@mcp.tool()
def get_available_models(directory: str = DEFAULT_DIRECTORY) -> dict:
    """
    Retrieve all available EnergyPlus models and their file locations.

    Returns detailed information about all discovered EnergyPlus models,
    including their unique identifiers for use with other tools.

    Args:
        directory: Directory parameter (currently ignored, uses default directory).

    Returns:
        List of dictionaries containing model information:
        - model_id: Unique identifier for use with other tools (e.g., 'mydir/eplusout')
        - directory: Directory path where model files are located
        - stem: Filename stem (filename without extension)
        - display_name: User-friendly name for the model
        - files: Dictionary of available file paths (epjson, sql, html)
    """

    model_map = read_or_initialize_model_map(EPLUS_RUNS_DIRECTORY, CACHE_PICKLE)

    # Directly return list of attributes instead of converting through DataFrame
    result = [x.get_basic_attributes() for x in model_map.models]

    log_mcp_call('get_available_models', result, kwargs={'directory': directory})

    return result


@mcp.tool()
def get_html_table_by_tuple(id: str, query_tuple: tuple) -> list[dict]:
    """
    Retrieve a specific HTML table from an EnergyPlus model using a tuple query.

    Args:
        id: The model_id of the EnergyPlus model (obtain from get_available_models).
        query_tuple: A tuple containing (zone/component, report_name, table_name)
                    to identify the specific table to retrieve.

    Returns:
        JSON string containing the requested table data with columns and rows.
    """

    model_map = read_or_initialize_model_map(EPLUS_RUNS_DIRECTORY, CACHE_PICKLE)
    model = model_map.get_model_by_id(id)
    table = model.html_data.get_table_by_tuple(query_tuple, asjson=True)

    result = table
    log_mcp_call(
        'get_html_table_by_tuple',
        result,
        kwargs={
            'id': id,
            'query_tuple': query_tuple
        }
    )

    return table


@mcp.tool()
def get_rdd_file(id: str) -> list[str]:
    """
    Retrieve a specific RDD file from an EnergyPlus model using ID.
    Useful in debugging.

    Args:
        id: The model_id of the EnergyPlus model (obtain from get_available_models).

    Returns:
        Plain text output of RDD file, which shows available output reports.
    """

    model_map = read_or_initialize_model_map(EPLUS_RUNS_DIRECTORY, CACHE_PICKLE)
    model = model_map.get_model_by_id(id)
    err_file = model.get_associated_files_by_type('rdd')
    return err_file


@mcp.tool()
def get_error_file(id: str) -> list[str]:
    """
    Retrieve a specific Error file from an EnergyPlus model using ID.
    Useful in debugging.

    Args:
        id: The model_id of the EnergyPlus model (obtain from get_available_models).

    Returns:
        Plain text output of EPlus error file
    """

    model_map = read_or_initialize_model_map(EPLUS_RUNS_DIRECTORY, CACHE_PICKLE)
    model = model_map.get_model_by_id(id)
    err_file = model.get_associated_files_by_type('err')
    return err_file


    # result = table
    # log_mcp_call(
    #     'get_html_table_by_tuple',
    #     result,
    #     kwargs={
    #         'id': id,
    #         'query_tuple': query_tuple
    #     }
    # )

    # return table




@mcp.tool()
def get_sql_available_hourlies(id: str) -> list | dict:
    """
    List available hourly timeseries variables in the SQL output for a specific model.

    Discovers all hourly timeseries data available in a model's SQL output database,
    providing variable names and RDD IDs needed to extract specific timeseries data.

    Args:
        id: The model_id of the EnergyPlus model (obtain from get_available_models).

    Returns:
        Available hourly timeseries variables including:
        - Variable names (e.g., 'Zone Air Temperature', 'HVAC Electric Power')
        - RDD IDs for use with get_timeseries_report_by_rddid
        - Units and key values for each variable
    """
    model_map = read_or_initialize_model_map(EPLUS_RUNS_DIRECTORY, CACHE_PICKLE)
    model = model_map.get_model_by_id(id)
    result = model.sql_data.get_timeseries().availseries()

    log_mcp_call('get_sql_available_hourlies', result, kwargs={'id': id})

    return result



@mcp.tool()
def search_epjson_objects(
        model_id: str,
        object_type: str = None,
        object_name: str = None,
        search_pattern: str = None,
        case_sensitive: bool = False
) -> dict:
    """
    Search for specific objects in epJSON data structure.

    Searches through the epJSON model data to find objects matching the specified criteria.
    Useful for finding specific components, systems, or zones within the building model.

    Args:
        model_id: The model_id of the EnergyPlus model
        object_type: Specific EnergyPlus object type (e.g., "Coil:Cooling:WaterToAirHeatPump:EquationFit")
        object_name: Specific object name (e.g., "ROOM_1_FLR_3 COOLING COIL")
        search_pattern: Pattern to search for in object names (e.g., "ROOM_1_FLR_3")
        case_sensitive: Whether to perform case-sensitive search

    Returns:
        Dictionary containing:
        - search_results: Matching objects organized by type
        - search_criteria: The search parameters used
        - search_stats: Statistics about the search results
    """


    # Get the cached epJSON data or load it
    model_map = read_or_initialize_model_map(EPLUS_RUNS_DIRECTORY, CACHE_PICKLE)
    model = model_map.get_model_by_id(model_id)
    epjson_data = model.epjson_data.get_data()

    if not epjson_data:
        return {"error": f"No epJSON data found for model {model_id}"}

    results = {}
    search_stats = {
        "total_object_types": 0,
        "total_objects": 0,
        "matches_found": 0
    }

    # Helper function for pattern matching
    def matches_pattern(text, pattern, case_sensitive):
        if not pattern:
            return True
        if case_sensitive:
            return pattern in text
        return pattern.lower() in text.lower()

    # Search through all object types
    for obj_type, objects in epjson_data.items():
        if not isinstance(objects, dict):
            continue

        search_stats["total_object_types"] += 1

        # Skip if specific object type requested and this isn't it
        if object_type and obj_type != object_type:
            continue

        # Search through objects of this type
        for obj_name, obj_data in objects.items():
            search_stats["total_objects"] += 1

            # Check if this object matches our search criteria
            matches = True

            # Check object name match
            if object_name and obj_name != object_name:
                matches = False

            # Check pattern match
            if search_pattern and not matches_pattern(obj_name, search_pattern, case_sensitive):
                matches = False

            # If matches, add to results
            if matches:
                if obj_type not in results:
                    results[obj_type] = {}
                results[obj_type][obj_name] = obj_data
                search_stats["matches_found"] += 1


    result = {
        "search_results": results,
        "search_criteria": {
            "object_type": object_type,
            "object_name": object_name,
            "search_pattern": search_pattern,
            "case_sensitive": case_sensitive
        },
        "search_stats": search_stats
    }

    log_mcp_call(
        'search_epjson_objects',
        result,
        kwargs={
            'model_id': model_id,
            'object_type': object_type,
            'object_name': object_name,
            'search_pattern': search_pattern,
            'case_sensitive': case_sensitive
        }
    )

    return result


@mcp.tool()
def get_object_properties(
        model_id: str,
        object_type: str,
        object_name: str) -> dict:
    """
    Get detailed properties of a specific EnergyPlus object.

    Retrieves all properties and values for a specific object in the epJSON model,
    providing complete configuration details for analysis.

    Args:
        model_id: The model_id of the EnergyPlus model
        object_type: EnergyPlus object type
        object_name: Specific object name

    Returns:
        Dictionary containing:
        - object_type: The EnergyPlus object type
        - object_name: The specific object name
        - properties: All object properties and their values
        - property_count: Number of properties
        - model_id: The model identifier
    """
    search_result = search_epjson_objects(
        model_id=model_id,
        object_type=object_type,
        object_name=object_name
    )

    if not search_result["search_results"]:
        return {"error": f"Object '{object_name}' of type '{object_type}' not found"}

    obj_data = search_result["search_results"][object_type][object_name]

    result = {
        "object_type": object_type,
        "object_name": object_name,
        "properties": obj_data,
        "property_count": len(obj_data),
        "model_id": model_id
    }

    log_mcp_call(
        'get_object_properties',
        result,
        kwargs={
            'model_id': model_id,
            'object_type': object_type,
            'object_name': object_name,

        }
    )

    # Add metadata about the object
    return result


@mcp.tool()
def list_objects_by_type(model_id: str, object_type: str) -> dict:
    """
    List all objects of a specific type in the epJSON model.

    Retrieves all objects of a specified EnergyPlus object type, providing
    an overview of all components of that type in the building model.

    Args:
        model_id: The model_id of the EnergyPlus model
        object_type: EnergyPlus object type to list

    Returns:
        Dictionary containing:
        - object_type: The requested object type
        - object_count: Number of objects found
        - objects: All objects of the specified type with their properties
        - model_id: The model identifier
    """
    search_result = search_epjson_objects(
        model_id=model_id,
        object_type=object_type
    )

    if object_type not in search_result["search_results"]:
        return {"error": f"No objects of type '{object_type}' found"}

    objects = search_result["search_results"][object_type]


    result = {
        "object_type": object_type,
        "object_count": len(objects),
        "objects": objects,
        "model_id": model_id
    }
    log_mcp_call(
        'list_objects_by_type',
        result,
        kwargs={
            'model_id': model_id,
            'object_type': object_type,
        }
    )
    return result


@mcp.tool()
def search_related_objects(model_id: str, search_pattern: str) -> dict:
    """
    Search for all objects related to a specific component or pattern.

    Finds all objects in the epJSON model that contain a specific pattern in their names,
    useful for analyzing all components related to a particular zone, system, or equipment.

    Args:
        model_id: The model_id of the EnergyPlus model
        search_pattern: Pattern to search for (e.g., "ROOM_1_FLR_3")

    Returns:
        Dictionary containing:
        - search_pattern: The pattern that was searched for
        - total_matches: Total number of matching objects
        - related_objects: Objects organized by type, with counts and details
        - model_id: The model identifier
    """
    search_result = search_epjson_objects(
        model_id=model_id,
        search_pattern=search_pattern
    )

    related_objects = {}
    total_matches = 0

    for obj_type, objects in search_result["search_results"].items():
        if objects:
            related_objects[obj_type] = {
                "count": len(objects),
                "objects": list(objects.keys()),
                "details": objects
            }
            total_matches += len(objects)


    result = {
        "search_pattern": search_pattern,
        "total_matches": total_matches,
        "related_objects": related_objects,
        "model_id": model_id
    }

    log_mcp_call(
        'search_related_objects',
        result,
        kwargs={
            'model_id': model_id,
            'search_pattern': search_pattern,
        }
    )

    return result




@mcp.tool()
def get_timeseries_report_by_rddid_list(model_id, rddid: list[int]) -> Any:
    """
    Retrieve hourly timeseries data for a specific variable from an EnergyPlus model.

    Extracts complete hourly timeseries data for a specific variable using its
    RDD (Report Data Dictionary) ID, providing timestamped values for analysis.

    Args:
        model_id: The model_id of the EnergyPlus model (obtain from get_available_models).
        rddid: A list of RDD IDs (integers) for the desired variables (obtain from get_sql_available_hourlies).

    Returns:
        List of timestamped records, each containing:
        - dt: Timestamp for the data point
        - Value: Numeric value for the variable
        - Name: Variable name (e.g., 'Zone Air Temperature')
        - KeyValue: Zone or component identifier
        - Units: Units of measurement

    Example:
        First use get_sql_available_hourlies to find the RDD ID for 'Zone Air Temperature',
        then use that ID with this tool.
    """
    model_map = read_or_initialize_model_map(EPLUS_RUNS_DIRECTORY, CACHE_PICKLE)
    model = model_map.get_model_by_id(model_id)


    resultlist = []
    for rdd in rddid:
        rdf = model.sql_data.get_timeseries().getseries_by_record_id(rdd)
        resultlist.append(rdf)

    dflist = []
    for r in resultlist:
        tr = r[0]

        r_lbl = f'{tr['KeyValue']}-{tr['Name']}-{tr['TimestepType']}-{tr['Units']}'

        dfr = pd.DataFrame(r)
        dfr = dfr.set_index('dt')

        dfr.name = r_lbl
        dfr = dfr.rename({"Value": r_lbl}, axis=1)

        dflist.append(dfr[r_lbl])

    dff = pd.concat(dflist, axis=1)
    log_mcp_call(
        'get_timeseries_report_by_rddid',
        dff,
        kwargs={
            'model_id': model_id,
            'rddid': rddid,
        }
    )
    return dff



@mcp.tool()
def get_usage_instructions() -> str:
    """
    Get comprehensive usage instructions for the EnergyPlus MCP server.

    Returns detailed documentation about how to use all available tools,
    including workflow guidance, data structures, and best practices.

    Returns:
        Complete usage instructions and documentation for the MCP server.
    """
    try:
        with open('src/CLAUDE.md', 'r') as f:
            result = f.read()
            log_mcp_call(
                'get_usage_instructions',
                result,
                kwargs={
                }
            )
            return result
    except FileNotFoundError:
        return "Usage instructions file not found. Please ensure CLAUDE.md exists in the src directory."
    except Exception as e:
        return f"Error reading usage instructions: {str(e)}"


@mcp.tool()
def search_html_tables_by_keyword(id: str, keywords: list[str], case_sensitive: bool = False) -> dict:
    """
    Search for HTML tables containing specific keywords in their names.

    Filters available HTML tables based on keyword matches in table names,
    report names, or other metadata. Useful for finding specific types of tables
    like 'cooling', 'heating', 'energy', etc.

    Args:
        id: The model_id of the EnergyPlus model (obtain from get_available_models).
        keywords: List of keywords to search for (e.g., ['cooling', 'coil', 'capacity'])
        case_sensitive: Whether to perform case-sensitive search (default: False)

    Returns:
        Dictionary containing:
        - matching_tables: List of tables that match the keywords
        - search_keywords: The keywords that were searched for
        - total_matches: Number of matching tables found
        - search_stats: Statistics about the search
        - model_id: The model identifier

    Examples:
        # Find cooling-related tables
        search_html_tables_by_keyword(model_id, ['cooling', 'coil'])

        # Find energy consumption tables
        search_html_tables_by_keyword(model_id, ['energy', 'consumption'])

        # Case-sensitive search for specific terms
        search_html_tables_by_keyword(model_id, ['DX', 'VAV'], case_sensitive=True)

    Common Keyword Categories:

    Energy & Consumption:
        ['energy', 'consumption', 'end use', 'site energy', 'source energy',
         'electricity', 'natural gas', 'fuel', 'annual', 'monthly',
         'utility', 'cost', 'performance']

    Cooling Systems:
        ['cooling', 'coil', 'capacity', 'chiller', 'dx cooling',
         'sensible cooling', 'latent cooling', 'peak cooling',
         'cooling tower', 'evaporative cooler', 'refrigeration']

    Heating Systems:
        ['heating', 'boiler', 'heat pump', 'heating coil', 'heat recovery',
         'sensible heating', 'peak heating', 'furnace', 'baseboard',
         'radiant heating', 'heat exchanger']

    HVAC Components:
        ['fan', 'pump', 'air loop', 'plant loop', 'zone equipment',
         'terminal unit', 'ahu', 'air handler', 'vav', 'cav']

    Building Envelope:
        ['window', 'wall', 'roof', 'floor', 'construction', 'material',
         'thermal bridge', 'infiltration', 'ventilation']

    Lighting & Equipment:
        ['lighting', 'electric equipment', 'gas equipment', 'occupancy',
         'schedule', 'internal load', 'plug load']
    """

    model_map = read_or_initialize_model_map(EPLUS_RUNS_DIRECTORY, CACHE_PICKLE)
    model = model_map.get_model_by_id(id)

    # Get all table data
    report_data = model.html_data.get_report_names()

    matching_tables = []
    search_stats = {
        "total_tables_searched": len(report_data) if isinstance(report_data, list) else 0,
        "keywords_used": keywords,
        "case_sensitive": case_sensitive
    }

    # Helper function to check if any keyword matches
    def contains_keywords(text, keywords, case_sensitive):
        if not text:
            return False

        search_text = text if case_sensitive else text.lower()
        search_keywords = keywords if case_sensitive else [kw.lower() for kw in keywords]

        return any(keyword in search_text for keyword in search_keywords)

    # Search through tables
    if isinstance(report_data, list):
        for table_info in report_data:
            if isinstance(table_info, tuple):
                table_name, report_name, report_for = table_info

                # Check various fields for keyword matches
                fields_to_search = [
                    table_name, report_name, report_for
                ]

                # Combine all searchable text
                combined_text = ' '.join(str(field) for field in fields_to_search)

                if contains_keywords(combined_text, keywords, case_sensitive):
                    matching_tables.append(table_info)

    result = {
        "matching_tables": matching_tables,
        "search_keywords": keywords,
        "total_matches": len(matching_tables),
        "search_stats": search_stats,
        "model_id": id
    }

    log_mcp_call(
        'search_html_tables_by_keyword',
        result,
        kwargs={
            'id': id,
            'keywords': keywords,
            'case_sensitive': case_sensitive
        }
    )

    return result



@mcp.tool()
def execute_query(file_hash: str, query: str) -> str:
    """
    Execute a pandas query on the cached DataFrame.

    Args:
        file_hash (str): Hash of the loaded parquet file to query.
        query (str): The pandas query to execute.

    Returns:
        str: Formatted result of the query.
    """
    return execute_pandas_query(file_hash, query)


@mcp.tool()
def execute_multiline_query(file_hash: str, query: str) -> str:
    """
    Execute multi-line pandas operations on the cached DataFrame.

    Args:
        file_hash (str): Hash of the loaded parquet file to query.
        query (str): Multi-line Python code to execute.

    Returns:
        str: Formatted result or status message.

    Notes: Does not accept import statements or print statements.
    """
    return execute_multiline_pandas_query(file_hash, query)


@mcp.tool()
def execute_pandas_on_timeseries(model_id: str, rddid: list[int], query: str) -> str:
    """
    Execute pandas operations on timeseries data from an EnergyPlus model.

    Retrieves timeseries data for a specific variable and executes pandas operations on it.
    The dataframe is available as 'df' in your query.

    Args:
        model_id: The model_id of the EnergyPlus model (obtain from get_available_models).
        rddid: A list of RDD IDs for the desired variable (obtain from get_sql_available_hourlies).
        query: Pandas query to execute (e.g., "df.describe()", "df['Value'].mean()")

    Returns:
        String representation of the query result with formatted output.

    Examples:
        # Get basic statistics
        execute_pandas_on_timeseries(model_id, rddid, "df.describe()")

        # Get hourly averages by month
        execute_pandas_on_timeseries(model_id, rddid, "df.groupby(df['dt'].dt.month)['Value'].mean()")

        # Find peak values
        execute_pandas_on_timeseries(model_id, rddid, "df.loc[df['Value'].idxmax()]")
    """

    # Get the timeseries data
    model_map = read_or_initialize_model_map(EPLUS_RUNS_DIRECTORY, CACHE_PICKLE)
    model = model_map.get_model_by_id(model_id)



    resultlist = []
    for rdd in rddid:
        rdf = model.sql_data.get_timeseries().getseries_by_record_id(rdd)
        resultlist.append(rdf)

    dflist = []
    for r in resultlist:
        tr = r[0]
        r_lbl = f'{tr['KeyValue']}-{tr['Name']}-{tr['TimestepType']}-{tr['Units']}'
        dfr = pd.DataFrame(r)
        dfr = dfr.set_index('dt')
        dfr.name = r_lbl
        dfr = dfr.rename({"Value": r_lbl}, axis=1)

        dflist.append(dfr[r_lbl])

    df = pd.concat(dflist, axis=1)


    # Convert datetime if present
    if 'dt' in df.columns:
        df['dt'] = pd.to_datetime(df['dt'])

    # Execute the query
    result = execute_pandas_query(df, query)

    log_mcp_call(
        'execute_pandas_on_timeseries',
        result,
        kwargs={
            'model_id': model_id,
            'rddid': rddid,
            'query': query
        }
    )

    return result


@mcp.tool()
def execute_multiline_pandas_on_timeseries(model_id: str, rddid: list[int], code: str) -> str:
    """
    Execute multi-line pandas code on timeseries data from an EnergyPlus model.

    Retrieves timeseries data for a specific variable and executes multi-line pandas code on it.
    The dataframe is available as 'df' in your code. Use 'result = ...' to return values.

    Args:
        model_id: The model_id of the EnergyPlus model (obtain from get_available_models).
        rddid: List of RDD IDs for the desired variables (obtain from get_sql_available_hourlies).
        code: Multi-line Python code to execute

    Returns:
        String representation of the result or execution status.

    Examples:
        # Complex analysis with multiple steps
        code = '''
        df['hour'] = df['dt'].dt.hour
        df['month'] = df['dt'].dt.month
        monthly_peaks = df.groupby('month')['Value'].max()
        result = monthly_peaks
        '''
        execute_multiline_pandas_on_timeseries(model_id, rddid, code)
    """

    # Get the timeseries data
    model_map = read_or_initialize_model_map(EPLUS_RUNS_DIRECTORY, CACHE_PICKLE)
    model = model_map.get_model_by_id(model_id)

    resultlist = []
    for rdd in rddid:
        rdf = model.sql_data.get_timeseries().getseries_by_record_id(rdd)
        resultlist.append(rdf)

    dflist = []
    for r in resultlist:
        tr = r[0]
        r_lbl = f'{tr['KeyValue']}-{tr['Name']}-{tr['TimestepType']}-{tr['Units']}'
        dfr = pd.DataFrame(r)
        dfr = dfr.set_index('dt')
        dfr.name = r_lbl
        dfr = dfr.rename({"Value": r_lbl}, axis=1)

        dflist.append(dfr[r_lbl])

    df = pd.concat(dflist, axis=1)


    # Execute the code
    result = execute_multiline_pandas_query(df, code)

    log_mcp_call(
        'execute_multiline_pandas_on_timeseries',
        result,
        kwargs={
            'model_id': model_id,
            'rddid': rddid,
            'code': code
        }
    )

    return result


@mcp.tool()
def execute_pandas_on_html_table(id: str, query_tuple: tuple, query: str) -> str:
    """
    Execute pandas operations on HTML table data from an EnergyPlus model.

    Retrieves an HTML table and executes pandas operations on it.
    The dataframe is available as 'df' in your query.

    Args:
        id: The model_id of the EnergyPlus model (obtain from get_available_models).
        query_tuple: A tuple containing (zone/component, report_name, table_name) to identify the table.
        query: Pandas query to execute (e.g., "df.describe()", "df.sum()")

    Returns:
        String representation of the query result with formatted output.

    Examples:
        # Get summary statistics
        execute_pandas_on_html_table(model_id, query_tuple, "df.describe()")

        # Find maximum values
        execute_pandas_on_html_table(model_id, query_tuple, "df.max()")

        # Filter data
        execute_pandas_on_html_table(model_id, query_tuple, "df[df > 1000]")
    """

    # Get the HTML table data
    model_map = read_or_initialize_model_map(EPLUS_RUNS_DIRECTORY, CACHE_PICKLE)
    model = model_map.get_model_by_id(id)
    table_data = model.html_data.get_table_by_tuple(query_tuple, asjson=False)

    # Convert to DataFrame (assuming table_data is already a DataFrame or convertible)
    if isinstance(table_data, str):
        # If it's JSON string, parse it
        try:
            import json
            table_dict = json.loads(table_data)
            df = pd.DataFrame(table_dict)
        except:
            return "Error: Could not convert table data to DataFrame"
    elif isinstance(table_data, pd.DataFrame):
        df = table_data
    else:
        df = pd.DataFrame(table_data)

    # Execute the query
    result = execute_pandas_query(df, query)

    log_mcp_call(
        'execute_pandas_on_html_table',
        result,
        kwargs={
            'id': id,
            'query_tuple': query_tuple,
            'query': query
        }
    )

    return result


@mcp.tool()
def execute_multiline_pandas_on_html_table(id: str, query_tuple: tuple, code: str) -> str:
    """
    Execute multi-line pandas code on HTML table data from an EnergyPlus model.

    Retrieves an HTML table and executes multi-line pandas code on it.
    The dataframe is available as 'df' in your code. Use 'result = ...' to return values.

    Args:
        id: The model_id of the EnergyPlus model (obtain from get_available_models).
        query_tuple: A tuple containing (zone/component, report_name, table_name) to identify the table.
        code: Multi-line Python code to execute

    Returns:
        String representation of the result or execution status.

    Examples:
        # Complex table analysis
        code = '''
        # Convert numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        df_numeric = df[numeric_cols]

        # Calculate totals and percentages
        totals = df_numeric.sum()
        percentages = (df_numeric / totals) * 100

        result = percentages
        '''
        execute_multiline_pandas_on_html_table(model_id, query_tuple, code)
    """

    # Get the HTML table data
    model_map = read_or_initialize_model_map(EPLUS_RUNS_DIRECTORY, CACHE_PICKLE)
    model = model_map.get_model_by_id(id)
    table_data = model.html_data.get_table_by_tuple(query_tuple, asjson=False)

    # Convert to DataFrame
    if isinstance(table_data, str):
        try:
            import json
            table_dict = json.loads(table_data)
            df = pd.DataFrame(table_dict)
        except:
            return "Error: Could not convert table data to DataFrame"
    elif isinstance(table_data, pd.DataFrame):
        df = table_data
    else:
        df = pd.DataFrame(table_data)

    # Execute the code
    result = execute_multiline_pandas_query(df, code)

    log_mcp_call(
        'execute_multiline_pandas_on_html_table',
        result,
        kwargs={
            'id': id,
            'query_tuple': query_tuple,
            'code': code
        }
    )

    return result
