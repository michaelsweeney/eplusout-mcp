
from pydantic import BaseModel
from typing import List, Literal
import pickle
import logging
import os
import glob as gb
from src.tools.func_html import get_all_table_data, get_html_report_name_data
from src.tools.func_epjson import read_epjson
from src.tools.func_sql import SqlTimeseries, SqlTables
from src import CACHE_PICKLE, CACHE_DIRECTORY


"""pydantic base model classes"""


class HtmlFileData(BaseModel):
    """
    Represents an HTML report file and provides methods to extract report names and table data.

    Attributes:
        file_path (str): Path to the HTML file.
        data (dict | None): Cached table data from the file.
        report_names (list | None): Cached list of report names from the file.
    """

    file_path: str
    data: dict | None = None
    report_names: list | None = None

    def get_report_names(self):
        if self.report_names is None:
            self.report_names = get_html_report_name_data(self.file_path)
        return self.report_names


    def get_data(self) -> list:
        if self.data is None:
            self.data = get_all_table_data(self.file_path)
        return self.data


class SqlFileData(BaseModel):
    """
    Represents a SQL output file and provides access to its parsed SqlObj.

    Attributes:
        file_path (str): Path to the SQL file.
        sql_obj (SqlObj | None): Cached SqlObj instance for this file.
    """

    file_path: str
    sql_timeseries: SqlTimeseries | None = None
    sql_tables: SqlTables | None = None

    def get_timeseries(self):

        if self.sql_timeseries is None:
            self.sql_timeseries = SqlTimeseries(sql_file=self.file_path)
        return self.sql_timeseries

    def get_tables(self):

        if self.sql_tables is None:
            self.sql_tables = SqlTimeseries(sql_file=self.file_path)

        return self.sql_tables




class EpJsonFileData(BaseModel):
    """
    Represents an EnergyPlus epJSON file and provides methods to extract its data.

    Attributes:
        file_path (str): Path to the epJSON file.
        data (dict | None): Cached parsed data from the file.
    """

    file_path: str
    data: dict | None = None

    def get_data(self) -> dict:
        if self.data is None:
            self.data = read_epjson(self.file_path)
        return self.data


class ModelFileData(BaseModel):
    """
    Represents a single EnergyPlus model and its associated files.

    Attributes:
        codename (str): Model codename (e.g., 'ASHRAE901').
        prototype (str): Building prototype (e.g., 'HotelLarge').
        codeyear (str): Code year (e.g., 'STD2025').
        city (str): City or location.
        label (str): Model label or variant.
        epjson_data (EpJsonFileData | None): Associated epJSON file data.
        sql_data (SqlFileData | None): Associated SQL file data.
        html_data (HtmlFileData | None): Associated HTML file data.
    """

    codename: str
    prototype: str
    codeyear: str
    city: str
    label: str
    model_id: str
    epjson_data: EpJsonFileData | None = None
    sql_data: SqlFileData | None = None
    html_data: HtmlFileData | None = None


class ModelMap(BaseModel):
    """
    Container for a list of ModelFileData objects, with search and add methods.

    Attributes:
        models (List[ModelFileData]): List of model objects.

    Methods:
        search: Filter models by codename, prototype, codeyear, city, or label.
        add: Add a new ModelFileData object to the list.
    """

    models: List[ModelFileData] = []


    def get_all_model_ids(self):
        return [
            x.model_id for x in self.models
        ]

    def get_model_by_id(self, id):

        dff = [x for x in self.models if x.model_id == id]

        if len(dff) == 1:
            return dff[0]
        elif len(dff) > 1:
            # logger.warning(f'multiple ids found; returning first: {id}')

            return dff[0]
        else:
            pass
            # logger.warning(f'no ids found: {id}')

    def search_models(
            self,
            codename: str | None = None,
            prototype: str | None = None,
            codeyear: str | None = None,
            city: str | None = None,
            label: str | None = None,
    ):
        model_filt = [x for x in self.models]

        if len(model_filt) == 0:
            return []
        else:
            mf = [x for x in model_filt if x.codename == codename]
            mf = [x for x in model_filt if x.prototype == prototype]
            mf = [x for x in model_filt if x.codeyear == codeyear]
            mf = [x for x in model_filt if x.city == city]
            mf = [x for x in model_filt if x.label == label]
            return mf

    def _add_model(self, obj: ModelFileData):
        self.models.append(obj)


    def get_epjson_by_id(self, id):
        model = self.get_model_by_id(id)

        return model.epjson_data.get_data()

    def get_html_by_id(self, id):
        model = self.get_model_by_id(id)

        return model.html_data.get_data()


    def write_to_cache(self, pickle_file: str = CACHE_PICKLE) -> None:
        """
        Save a ModelMap object to disk as a pickle file.

        Args:
            model_map (ModelMap): The ModelMap object to cache.

        Returns:
            None
        """

        with open(pickle_file, 'wb') as f:
            print(f'writing to cache: {pickle_file}')
            pickle.dump(self, f)




def get_files_by_type(directory, ext):
    """
    List all files in a directory with a given extension.

    This function is used by the MCP server to discover EnergyPlus model files
    of specific types (HTML, SQL, epJSON) within a directory structure.

    Args:
        directory (str): Directory path to search for files.
        ext (str): File extension (with or without dot) to filter by.

    Returns:
        list[str]: List of absolute file paths matching the extension.

    Example:
        >>> get_files_by_type('/path/to/eplus_files', '.sql')
        ['/path/to/eplus_files/model1.sql', '/path/to/eplus_files/model2.sql']
    """

    ext = ext.replace(".", "")

    fsstr = f'{directory}/*.{ext}'
    files = gb.glob(fsstr)

    return files


def get_file_info(fpath):
    """
    Parse a file name to extract model metadata such as codename, prototype, codeyear, city, label, and extension.

    This function is critical for the MCP server to understand and categorize EnergyPlus model files
    based on their standardized naming convention. It extracts key metadata that allows the server
    to organize and filter models by building type, code year, location, and HVAC system.

    Args:
        fpath (str): Full file path to parse for metadata extraction.

    Returns:
        dict: Dictionary containing parsed metadata with keys:
            - codename (str): Model code standard (e.g., 'ASHRAE901')
            - prototype (str): Building prototype (e.g., 'HotelLarge', 'Warehouse')
            - codeyear (str): Code year (e.g., 'STD2025')
            - city (str): Location/city name (e.g., 'Buffalo', 'Tampa')
            - label (str): HVAC system label (e.g., 'gshp', 'vav_ac_blr')
            - extension (str): File extension (e.g., 'sql', 'epJSON', 'table.htm')
            - file_name (str): Base filename
            - file_path (str): Original file path

    Example:
        >>> get_file_info('/path/ASHRAE901_HotelLarge_STD2025_Buffalo_SkipEC_gshp.sql')
        {
            'codename': 'ASHRAE901',
            'prototype': 'HotelLarge', 
            'codeyear': 'STD2025',
            'city': 'Buffalo',
            'label': 'gshp',
            'extension': 'sql',
            'file_name': 'ASHRAE901_HotelLarge_STD2025_Buffalo_SkipEC_gshp.sql',
            'file_path': '/path/ASHRAE901_HotelLarge_STD2025_Buffalo_SkipEC_gshp.sql'
        }
    """


    fname = os.path.basename(fpath)

    left = fname.split("_")[:4]

    right = '_'.join(fname.split("_")[5:])


    model_lbl = right.split(".")[0]

    ext = '.'.join(right.split(".")[1:])


    codename = left[0]
    prototype = left[1]
    codeyear = left[2]
    city = left[3]

    return {
        'codename': codename,
        'prototype': prototype,
        'codeyear': codeyear,
        'city': city,
        'label': model_lbl,
        'extension': ext,
        'file_name': fname,
        'file_path': fpath
    }



def catalog_path(path):
    """
    Scan a directory for HTML, SQL, and epJSON files and return their metadata as lists.

    This function is the primary discovery mechanism for the MCP server to inventory
    all EnergyPlus model files in a directory. It identifies the three main file types
    that contain model input data, simulation results, and summary reports.

    Args:
        path (str): Directory path to scan for EnergyPlus model files.

    Returns:
        dict: Dictionary with lists of file metadata for each file type:
            - html_data (list): List of HTML report file metadata dictionaries
            - sql_data (list): List of SQL results file metadata dictionaries  
            - epjson_data (list): List of epJSON input file metadata dictionaries

    Note:
        Each metadata dictionary contains the same structure as returned by get_file_info(),
        allowing the MCP server to understand the model characteristics and organize them
        into a coherent model map.

    Example:
        >>> catalog_path('/path/to/eplus_files')
        {
            'html_data': [{'codename': 'ASHRAE901', 'prototype': 'HotelLarge', ...}, ...],
            'sql_data': [{'codename': 'ASHRAE901', 'prototype': 'HotelLarge', ...}, ...],
            'epjson_data': [{'codename': 'ASHRAE901', 'prototype': 'HotelLarge', ...}, ...]
        }
    """

    html_files = get_files_by_type(path, '.htm')
    sql_files = get_files_by_type(path, '.sql')
    epjson_files = get_files_by_type(path, '.epJSON')

    html_data = [get_file_info(x) for x in html_files]
    sql_data = [get_file_info(x) for x in sql_files]
    epjson_data = [get_file_info(x) for x in epjson_files]



    return {'html_data': html_data, 'sql_data': sql_data, 'epjson_data': epjson_data}


def get_model_map(listdict):
    """
    Build a ModelMap object from a dictionary of file info lists (from catalog_path).

    This function is the core model organization mechanism for the MCP server. It takes
    the cataloged file information and creates a unified ModelMap that groups related
    files (HTML, SQL, epJSON) into coherent model objects. This enables the server
    to provide integrated access to all aspects of each EnergyPlus model.

    Args:
        listdict (dict): Dictionary with file metadata lists containing:
            - 'html_data': List of HTML report file metadata
            - 'sql_data': List of SQL results file metadata  
            - 'epjson_data': List of epJSON input file metadata

    Returns:
        ModelMap: Populated ModelMap object containing ModelFileData objects,
                 each representing a complete EnergyPlus model with all associated files.

    Note:
        The function handles the complex logic of matching files that belong to the same
        model based on their parsed metadata (codename, prototype, codeyear, city, label).
        This allows the MCP server to treat each model as a unified entity regardless
        of how the files are stored on disk.

    Example:
        Input from catalog_path() gets transformed into a ModelMap where each model
        has references to its HTML report, SQL results, and epJSON input files.
    """

    htmldata = listdict['html_data']
    epjsondata = listdict['epjson_data']
    sqldata = listdict['sql_data']

    catalog = ModelMap()

    def handle_merge_obj(
            catalog: ModelMap,
            obj: list[dict],
            ftype: Literal['sql', 'epjson', 'html']
    ):

        for h in obj:

            codename = h['codename']
            prototype = h['prototype']
            codeyear = h['codeyear']
            city = h['city']
            label = h['label']
            file_path = h['file_path']
            filepath_abs = os.path.abspath(h['file_path'])

            # TODO should ensure this is unique.
            model_id = f'{codename}|{prototype}|{codeyear}|{city}|{label}'
            # check if exists
            model_search = catalog.search_models(
                codename=codename,
                prototype=prototype,
                codeyear=codeyear,
                city=city,
                label=label
            )
            # if no match
            if len(model_search) == 0:
                model = ModelFileData(
                    codename=codename,
                    prototype=prototype,
                    codeyear=codeyear,
                    city=city,
                    label=label,
                    model_id=model_id
                )

                catalog._add_model(model)

            elif len(model_search) == 1:
                model = model_search[0]
            else:
                raise ValueError('multiples found')

            obj_dict = {
                'sql': SqlFileData,
                'epjson': EpJsonFileData,
                'html': HtmlFileData
            }

            file_obj = obj_dict[ftype](
                codename=codename,
                prototype=prototype,
                codeyear=codeyear,
                city=city,
                label=label,
                file_path=filepath_abs
            )

            if ftype == 'sql':
                file_obj.file_path = filepath_abs
                model.sql_data = file_obj
            elif ftype == 'html':
                file_obj.file_path = filepath_abs
                model.html_data = file_obj
            elif ftype == 'epjson':
                file_obj.file_path = filepath_abs
                model.epjson_data = file_obj
            else:
                raise ValueError('parsing error')


    handle_merge_obj(
        catalog=catalog,
        obj=htmldata,
        ftype='html'
    )

    handle_merge_obj(
        catalog=catalog,
        obj=sqldata,
        ftype='sql'
    )

    handle_merge_obj(
        catalog=catalog,
        obj=epjsondata,
        ftype='epjson'
    )

    return catalog


"""file operations"""


def read_model_map_from_cache(pickle_file: str) -> ModelMap:
    """
    Load the cached ModelMap object from disk.

    This function enables the MCP server to quickly restore a previously built ModelMap
    from disk cache, avoiding the need to re-scan and re-parse all model files on
    every server startup. This significantly improves server performance for large
    model directories.

    Args:
        pickle_file (str): Path to the pickle cache file containing the serialized ModelMap.

    Returns:
        ModelMap: The deserialized ModelMap object loaded from cache.

    Raises:
        FileNotFoundError: If the pickle cache file doesn't exist.
        pickle.UnpicklingError: If the cache file is corrupted or incompatible.

    Note:
        The MCP server should handle cases where the cache file doesn't exist or
        is corrupted by falling back to rebuilding the ModelMap from the source directory.
    """

    with open(pickle_file, 'rb') as f:
        print(f'reading cached file {pickle_file}')
        pc = pickle.load(f)

    return pc




def initialize_model_map_from_directory(directory: str) -> ModelMap:
    """
    Scan a directory for model files, build a ModelMap, and cache it to disk.

    This function provides the MCP server with a complete model discovery and caching
    workflow. It scans the specified directory for EnergyPlus model files, builds
    a comprehensive ModelMap, and saves it to cache for future use.

    Args:
        directory (str): Directory path to scan for EnergyPlus model files.

    Returns:
        ModelMap: Newly built ModelMap object containing all discovered models.

    Side Effects:
        - Writes the ModelMap to the default cache location (CACHE_PICKLE)
        - Prints progress messages about cache operations

    Note:
        This function is typically called by the MCP server during initial setup
        or when refreshing the model cache. It performs the full workflow of
        discovery, parsing, organization, and caching.
    """

    catalog_info = catalog_path(directory)
    model_map = get_model_map(catalog_info)

    model_map.write_to_cache()

    return model_map



def reset_cache(pickle_file):

    if os.path.exists(pickle_file):

        os.remove(pickle_file)


def read_or_initialize_model_map(directory: str, pickle_file: str = CACHE_PICKLE) -> ModelMap:
    """
    Load the ModelMap from cache if available, otherwise build and cache it from the given directory.

    Args:
        directory (str): Directory to scan if cache is missing.

    Returns:
        ModelMap: The loaded or newly built ModelMap object.
    """

    if os.path.exists(pickle_file):
        model_map = read_model_map_from_cache(pickle_file)

    else:
        model_map = initialize_model_map_from_directory(pickle_file, directory)
        model_map.write_to_cache()

    return model_map
