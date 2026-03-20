
from pydantic import BaseModel
from typing import List, Literal
from pathlib import Path
import pandas as pd
import logging
import glob as gb

logger = logging.getLogger(__name__)
from src.tools.func_html import get_all_table_data
from src.tools.func_epjson import read_epjson
from src.tools.func_sql import SqlTimeseries, SqlTables


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

    def get_report_names(self) -> list[tuple]:

        """
        return list of tuples, "report_for", "report_name", "table_name"
        """
        data = self.get_data()

        return [
            (
                x['report_for'], x['report_name'], x['table_name']
            ) for x in data]


    def get_data(self) -> list:
        if self.data is None:
            logger.debug(f'storing html data: {self.file_path}')
            self.data = get_all_table_data(self.file_path)
        return self.data


    def get_table_by_tuple(self, tabletuple, asjson=True):
        """
        tabletuple is in order "report_for", "report_name", "table_name" 
        """
        data = self.get_data()

        report_for, report_name, table_name = tabletuple

        datafilter = [
            x for x in data if x['report_for'] == report_for and x['report_name'] == report_name and x['table_name'] == table_name
        ]

        if len(datafilter) == 0:
            logger.warning(f'no tables found: {tabletuple}')
        elif len(datafilter) > 1:
            logger.warning(f'multiple tables found: {tabletuple}')

        else:

            tabledata = datafilter[0]['table_data']
            if not asjson:
                return tabledata
            tdd = pd.DataFrame(tabledata)

            tdd.columns = tdd.iloc[0]
            tdd = tdd.iloc[1:, :]

            # handle
            identifier = tdd.columns.to_series().groupby(level=0).transform('cumcount')
            # rename columns with the new identifiers

            identifier = identifier.astype(str).replace("0", "")

            tdd.columns = tdd.columns.astype('string') + "_" + identifier.astype('string')

            def trim_last(x):
                if x[-1] == '_':
                    return x[:-1]
            tdd.columns = [trim_last(x) for x in tdd.columns]

            split = tdd.to_dict(orient='split')
            return {"columns": split["columns"], "data": split["data"]}

        return []




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
            self.sql_tables = SqlTables(sql_file=self.file_path)

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
        model_id (str): Unique identifier for this model (e.g., 'mydir/eplusout').
        directory (str): Directory path where the model files are located.
        stem (str): Filename stem (filename without extension).
        display_name (str): User-friendly name for the model (defaults to stem).
        epjson_data (EpJsonFileData | None): Associated epJSON file data.
        sql_data (SqlFileData | None): Associated SQL file data.
        html_data (HtmlFileData | None): Associated HTML file data.
    """

    model_id: str
    directory: str
    stem: str
    display_name: str | None = None

    epjson_data: EpJsonFileData | None = None
    sql_data: SqlFileData | None = None
    html_data: HtmlFileData | None = None

    def model_post_init(self, __context):
        """Set display_name to stem if not provided"""
        if self.display_name is None:
            self.display_name = self.stem

    def get_basic_attributes(self):
        """Get basic model attributes for display"""
        file_types = []
        if self.epjson_data:
            file_types.append('epjson')
        if self.sql_data:
            file_types.append('sql')
        if self.html_data:
            file_types.append('html')

        return {
            'model_id': self.model_id,
            'stem': self.stem,
            'file_types': file_types
        }

    def get_associated_files_by_type(self, ext: str, file_type: Literal['plain_text', 'csv'] = 'plain_text'):

        # assumes there is one and only one epjson_data file. also assumes that it is a plain text object and returns lines.
        # TODO this really doesnt belong here.

        if self.epjson_data:
            epjson_path = Path(self.epjson_data.file_path)
            parent = epjson_path.parent
            stem = epjson_path.stem
            files_found = [x for x in parent.glob(f'{stem}*{ext}')]

            if len(files_found) >= 1:
                ftr = files_found[0]
                if file_type == 'plain_text':
                    with open(ftr, 'r') as f:
                        return f.readlines()
                elif file_type == 'csv':
                    try:
                        df = pd.read_csv(ftr, encoding='utf-8')
                    except pd.errors.ParserError as e:
                        with open(ftr, 'r') as f:
                            logger.warning(f"csv parser error, returning as text: {ftr}")
                            return f.readlines()
                    return df
                else:
                    return f'error -- no implementation for type {file_type}'
            else:
                return f"error - no file found for type {ext}"
        pass


class ModelMap(BaseModel):
    """
    Container for a list of ModelFileData objects, with search and add methods.

    Attributes:
        models (List[ModelFileData]): List of model objects.

    Methods:
        search_models: Filter models by pattern matching on model_id or display_name.
        _add_model: Add a new ModelFileData object to the list.
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
            return dff[0]
        else:
            available = [m.model_id for m in self.models]
            raise ValueError(
                f"Model '{id}' not found. Available models: {available}"
            )

    def search_models(self, pattern: str | None = None):
        """
        Filter models by model_id or display_name pattern.

        Args:
            pattern (str | None): Search pattern to match against model_id or display_name.
                                 If None, returns all models.

        Returns:
            list: List of ModelFileData objects matching the pattern.

        Example:
            >>> model_map.search_models('mydir')
            [<ModelFileData model_id='mydir/model1'>, <ModelFileData model_id='mydir/model2'>]
        """
        if not pattern:
            return self.models

        pattern_lower = pattern.lower()
        return [
            m for m in self.models
            if pattern_lower in m.model_id.lower() or
               pattern_lower in (m.display_name or '').lower()
        ]

    def _add_model(self, obj: ModelFileData):
        self.models.append(obj)


    def get_epjson_by_id(self, id):
        model = self.get_model_by_id(id)

        return model.epjson_data.get_data()

    def get_html_by_id(self, id):
        model = self.get_model_by_id(id)

        return model.html_data.get_data()






def get_files_by_type(directory, ext, recursive=True):
    """
    List all files in a directory with a given extension.

    This function is used by the MCP server to discover EnergyPlus model files
    of specific types (HTML, SQL, epJSON) within a directory structure.

    Args:
        directory (str): Directory path to search for files.
        ext (str): File extension (with or without dot) to filter by.
        recursive (bool): If True, search recursively in subdirectories. Default is True.

    Returns:
        list[str]: List of absolute file paths matching the extension.

    Example:
        >>> get_files_by_type('/path/to/eplus_files', '.sql')
        ['/path/to/eplus_files/model1.sql', '/path/to/eplus_files/subdir/model2.sql']
    """

    ext = ext.replace(".", "")

    if recursive:
        fsstr = f'{directory}/**/*.{ext}'
        files = gb.glob(fsstr, recursive=True)
    else:
        fsstr = f'{directory}/*.{ext}'
        files = gb.glob(fsstr)

    return files


def get_file_info(fpath) -> dict:
    """
    Extract path-based metadata from a file.

    This function extracts only directory and filename information without assuming
    any specific naming convention. Files are identified by their directory location
    and stem (filename without extension).

    Args:
        fpath (str): Full file path to parse.

    Returns:
        dict: Dictionary containing path metadata with keys:
            - directory (str): Parent directory path
            - stem (str): Filename without extension (e.g., 'eplusout', 'somemodel')
            - extension (str): File extension (e.g., 'sql', 'epJSON', 'htm')
            - file_name (str): Base filename with extension
            - file_path (str): Original absolute file path

    Example:
        >>> get_file_info('/path/mydir/eplusout.sql')
        {
            'directory': '/path/mydir',
            'stem': 'eplusout',
            'extension': 'sql',
            'file_name': 'eplusout.sql',
            'file_path': '/path/mydir/eplusout.sql'
        }
    """
    p = Path(fpath)

    # Get extension without the dot
    ext = p.suffix.lstrip('.')

    # Handle .table.htm files - remove .table. to get the correct stem
    stem = p.stem
    if stem.endswith('.table') and ext in ['htm', 'html']:
        stem = stem[:-6]  # Remove '.table'

    return {
        'directory': str(p.parent),
        'stem': stem,
        'extension': ext,
        'file_name': p.name,
        'file_path': str(p.absolute())
    }



def catalog_path(path):
    """
    Scan a directory for HTML, SQL, and epJSON files and group them by directory + stem.

    This function is the primary discovery mechanism for the MCP server to inventory
    all EnergyPlus model files in a directory. Files are grouped together when they share
    the same directory and filename stem (filename without extension).

    Args:
        path (str): Directory path to scan for EnergyPlus model files (scanned recursively).

    Returns:
        dict: Dictionary where keys are model_ids (directory/stem) and values contain grouped files:
            {
                'dir1/model1': {
                    'directory': 'dir1',
                    'stem': 'model1',
                    'html': '/full/path/dir1/model1.htm',
                    'sql': '/full/path/dir1/model1.sql',
                    'epjson': '/full/path/dir1/model1.epJSON'
                },
                'dir2/model2': { ... }
            }

    Note:
        Files with different stems in the same directory are treated as separate models.
        For example, 'mydir/model1.sql' and 'mydir/model2.sql' would create two distinct
        model entries: 'mydir/model1' and 'mydir/model2'.

    Example:
        >>> catalog_path('/path/to/eplus_files')
        {
            'eplus_files/run1/eplusout': {
                'directory': '/path/to/eplus_files/run1',
                'stem': 'eplusout',
                'html': '/path/to/eplus_files/run1/eplusout.htm',
                'sql': '/path/to/eplus_files/run1/eplusout.sql',
                'epjson': '/path/to/eplus_files/run1/eplusout.epJSON'
            }
        }
    """

    html_files = get_files_by_type(path, '.htm', recursive=True)
    html_files += get_files_by_type(path, '.html', recursive=True)
    sql_files = get_files_by_type(path, '.sql', recursive=True)
    epjson_files = get_files_by_type(path, '.epJSON', recursive=True)

    # Dictionary to group files by (directory, stem)
    grouped_models = {}

    # Process all files
    all_files = html_files + sql_files + epjson_files

    for file_path in all_files:
        file_info = get_file_info(file_path)

        directory = file_info['directory']
        stem = file_info['stem']
        ext = file_info['extension'].lower()

        # Create unique key for this model (using relative path from base)
        # Use Path to get relative path
        try:
            rel_dir = Path(directory).relative_to(Path(path))
            model_key = f"{rel_dir}/{stem}".replace("\\", "/")
        except ValueError:
            # If path is not relative, use full directory
            model_key = f"{directory}/{stem}".replace("\\", "/")

        # Initialize model entry if it doesn't exist
        if model_key not in grouped_models:
            grouped_models[model_key] = {
                'directory': directory,
                'stem': stem,
                'html': None,
                'sql': None,
                'epjson': None
            }

        # Assign file to appropriate type
        if ext in ['htm', 'html']:
            grouped_models[model_key]['html'] = file_info['file_path']
        elif ext == 'sql':
            grouped_models[model_key]['sql'] = file_info['file_path']
        elif ext == 'epjson':
            grouped_models[model_key]['epjson'] = file_info['file_path']

    return grouped_models


def get_model_map(grouped_models):
    """
    Build a ModelMap object from grouped model files (from catalog_path).

    This function is the core model organization mechanism for the MCP server. It takes
    the cataloged and grouped file information and creates a unified ModelMap that contains
    model objects with their associated files (HTML, SQL, epJSON).

    Args:
        grouped_models (dict): Dictionary from catalog_path() where keys are model_ids
                              and values contain grouped file paths:
            {
                'dir/stem': {
                    'directory': '/full/path/dir',
                    'stem': 'stem',
                    'html': '/full/path/dir/stem.htm',
                    'sql': '/full/path/dir/stem.sql',
                    'epjson': '/full/path/dir/stem.epJSON'
                }
            }

    Returns:
        ModelMap: Populated ModelMap object containing ModelFileData objects,
                 each representing a complete EnergyPlus model with all associated files.

    Note:
        Files are already grouped by catalog_path() based on directory and stem.
        This function simply creates the ModelFileData objects and populates the ModelMap.

    Example:
        Input from catalog_path() gets transformed into a ModelMap where each model
        has references to its HTML report, SQL results, and epJSON input files.
    """

    catalog = ModelMap()

    for model_id, file_info in grouped_models.items():
        directory = file_info['directory']
        stem = file_info['stem']

        # Create the model object
        model = ModelFileData(
            model_id=model_id,
            directory=directory,
            stem=stem
        )

        # Attach file data objects if files exist
        if file_info['html']:
            model.html_data = HtmlFileData(file_path=file_info['html'])

        if file_info['sql']:
            model.sql_data = SqlFileData(file_path=file_info['sql'])

        if file_info['epjson']:
            model.epjson_data = EpJsonFileData(file_path=file_info['epjson'])

        # Add model to catalog
        catalog._add_model(model)

    return catalog





def initialize_model_map_from_directory(directory: str) -> ModelMap:
    """
    Scan a directory for model files and build a ModelMap.

    Args:
        directory (str): Directory path to scan for EnergyPlus model files.

    Returns:
        ModelMap: Newly built ModelMap object containing all discovered models.
    """
    catalog_info = catalog_path(directory)
    return get_model_map(catalog_info)
