'''
set of functions to open sql file, find table name, and parse it into a usable format as a dataframe.
'''

import glob as gb
import os
import sys
import sqlite3
import warnings
import pandas as pd

from pydantic import BaseModel

STRTYPEIDX = {
    1: 'ReportName',
    2: 'ReportForString',
    3: 'TableName',
    4: 'RowName',
    5: 'ColumnName',
    6: 'Units'
}


class SqlTables(BaseModel):
    """
    Provides methods to extract and manipulate tabular data from EnergyPlus SQL output files.
    Use this class to list available tables, filter tables, and extract specific tables as DataFrames.
    """
    sql_file: str
    _string_cache: dict | None = None  # Cache for Strings table lookups
    _conn: sqlite3.Connection | None = None  # Persistent connection

    class Config:
        arbitrary_types_allowed = True

    def _get_connection(self):
        """Get or create persistent connection"""
        if self._conn is None:
            self._conn = sqlite3.connect(self.sql_file)
        return self._conn

    def __del__(self):
        """Close connection on cleanup"""
        if self._conn is not None:
            self._conn.close()

    def _get_string_cache(self):
        """Get or build string lookup cache"""
        if self._string_cache is None:
            strings = self._exec_pandas_query("SELECT StringIndex, StringTypeIndex, Value FROM Strings")
            # Create nested dict: {StringTypeIndex: {Value: StringIndex}}
            self._string_cache = {}
            for _, row in strings.iterrows():
                type_idx = row['StringTypeIndex']
                if type_idx not in self._string_cache:
                    self._string_cache[type_idx] = {}
                self._string_cache[type_idx][row['Value']] = row['StringIndex']
        return self._string_cache

    def _df_cols_to_dict(self, df, keycol, valcol):
        """
        Convert two columns of a DataFrame into a dictionary.
        Args:
            df (pd.DataFrame): DataFrame to process.
            keycol (str): Column to use as keys.
            valcol (str): Column to use as values.
        Returns:
            dict: Mapping from keycol to valcol.
        """
        return pd.Series(df[valcol].values, index=df[keycol].values).to_dict()

    def _idx_to_str(self, tabledf, stringdict, lookup_col):
        """
        Replace index columns with their string values using a lookup dictionary.
        Args:
            tabledf (pd.DataFrame): DataFrame with index columns.
            stringdict (dict): Mapping from index to string.
            lookup_col (str): Name of the index column to replace.
        Returns:
            pd.DataFrame: DataFrame with string column added.
        """
        string_col = lookup_col.replace("Index", "")
        if string_col == lookup_col:
            raise ValueError("Lookup Col str has to have 'Index' in it")
        tabledf[string_col] = tabledf[lookup_col].apply(lambda x: stringdict[x])
        return tabledf

    def _exec_query(self, query):
        conn = sqlite3.connect(self.sql_file)
        cursor = conn.cursor()

        cursor.execute()

        rows = cursor.fetchall()

        conn.close()

        return rows


    def _exec_pandas_query(self, query):
        """
        Execute a SQL query on the file and return the result as a DataFrame.
        Args:
            query (str): SQL query string.
        Returns:
            pd.DataFrame: Query result.
        """
        conn = self._get_connection()
        df = pd.read_sql((query), conn)
        return df

    def _df_to_tabledict(self, df):
        """
        Convert a DataFrame of table metadata into a list of dictionaries for table extraction.
        Args:
            df (pd.DataFrame): DataFrame with table metadata.
        Returns:
            list[dict]: List of dictionaries with ReportName, ReportForString, TableName.
        """
        ziplist = list(zip(df['ReportName'].values.tolist(), df['ReportForString'].values.tolist(), df['TableName'].values.tolist()))
        zipdict = [{
            'ReportName': z[0],
            'ReportForString': z[1],
            'TableName': z[2]
        } for z in ziplist]
        return zipdict


    def _filter_tabular(self, filterquery):
        """
        Filter available tabular data for any string, returning matching rows as a DataFrame.
        Args:
            filterquery (str): String to search for in table metadata.
        Returns:
            pd.DataFrame: Filtered DataFrame.
        """
        avail = self.avail_tabular()
        df = avail[avail.apply(lambda row: row.astype(str).str.contains(filterquery).any(), axis=1)]
        return df

    def avail_tabular(self):
        """
        Return a DataFrame of all available tables (with tablename, reportfor, reportname).
        Returns:
            pd.DataFrame: DataFrame of available tables.
        """
        tabulardata = self._exec_pandas_query("SELECT * FROM 'TabularData'")
        strings = self._exec_pandas_query("SELECT * FROM 'Strings'")
        stringdict = self._df_cols_to_dict(strings, 'StringIndex', 'Value')
        get_strs = ['ReportNameIndex', 'ReportForStringIndex', 'TableNameIndex']
        for string in get_strs:
            tabulardata = self._idx_to_str(tabulardata, stringdict, string)
            tabulardata.drop(string, axis=1, inplace=True)
        tables = tabulardata[['ReportName', 'ReportForString', 'TableName']].drop_duplicates()
        return tables


    def get_tabular(self, tabledict):
        """
        Return a single table as a DataFrame given a table dictionary or DataFrame row.
        Args:
            tabledict (dict or pd.DataFrame): Table metadata.
        Returns:
            pd.DataFrame: Table data with multi-index columns for names and units.
        """

        if isinstance(tabledict, pd.DataFrame):
            assert len(tabledict) == 1, 'more than one dataframe row passed'
            report_name = tabledict['ReportName'].values[0]
            report_for = tabledict['ReportForString'].values[0]
            table_name = tabledict['TableName'].values[0]

        else:
            report_name = tabledict['ReportName']
            report_for = tabledict['ReportForString']
            table_name = tabledict['TableName']


        # Use cached string lookups instead of querying
        string_cache = self._get_string_cache()
        reportnameidx = string_cache.get(1, {}).get(report_name)
        reportforidx = string_cache.get(2, {}).get(report_for)
        tablenameidx = string_cache.get(3, {}).get(table_name)

        if reportnameidx is None or reportforidx is None or tablenameidx is None:
            raise ValueError(f"Table not found: {report_name}/{report_for}/{table_name}")



        tablestr = self._exec_pandas_query(
            "SELECT * FROM 'TabularData' WHERE TableNameIndex = {0} AND ReportForStringIndex = {1} AND ReportNameIndex = {2}".format(tablenameidx, reportforidx, reportnameidx))
        strings = self._exec_pandas_query("SELECT * FROM 'Strings'")

        stringdict = self._df_cols_to_dict(strings, 'StringIndex', 'Value')
        idxcols = [col for col in tablestr.columns if "Index" in col and "TabularDataIndex" not in col]
        for col in idxcols:
            df = self._idx_to_str(tablestr, stringdict, col)

        df = df[[col for col in df.columns if "Index" not in col]]
        coldict = self._df_cols_to_dict(df, 'ColumnId', 'ColumnName')
        colunitdict = self._df_cols_to_dict(df, 'ColumnId', 'Units')


        rowdict = self._df_cols_to_dict(df, 'RowId', 'RowName')
        valdf = df[['RowId', 'ColumnId', 'Value']].pivot(columns='ColumnId', index='RowId', values='Value')
        valdf.columns = pd.MultiIndex.from_tuples([(coldict[col], colunitdict[col]) for col in valdf.columns])

        valdf.insert(0, 'FieldName', [rowdict[row] for row in valdf.index])
        valdf.insert(0, 'TableName', table_name)
        valdf.insert(0, 'ReportForString', report_for)
        valdf.insert(0, 'ReportName', report_name)

        valdf = self._floatdf(valdf)
        return valdf

    def search_tabular(self, filter):
        """
        Search for tables with names matching a filter string and return a list of DataFrames.
        Args:
            filter (str): String to search for in table names.
        Returns:
            list[pd.DataFrame]: List of matching tables as DataFrames.
        """
        dflist = [self.get_tabular(filterdict) for filterdict in self._df_to_tabledict(self._filter_tabular(filter))]
        return dflist


    def simulations(self):
        """
        Return the 'Simulations' table as a DataFrame.
        Returns:
            pd.DataFrame: DataFrame of simulation metadata.
        """
        df = self._exec_pandas_query("SELECT * FROM 'Simulations'")
        return df





class SqlTimeseries(BaseModel):
    """
    Provides methods to extract and manipulate time series data from EnergyPlus SQL output files.
    Use this class to list available series, filter by name, and extract time series as DataFrames.
    """
    sql_file: str
    _time_cache: pd.DataFrame | None = None  # Cache for time index
    _conn: sqlite3.Connection | None = None  # Persistent connection

    class Config:
        arbitrary_types_allowed = True

    def _get_connection(self):
        """Get or create persistent connection"""
        if self._conn is None:
            self._conn = sqlite3.connect(self.sql_file)
        return self._conn

    def __del__(self):
        """Close connection on cleanup"""
        if self._conn is not None:
            self._conn.close()

    def _exec_query(self, query):
        """
        Execute a SQL query on the file and return the result as a DataFrame.
        Args:
            query (str): SQL query string.
        Returns:
            pd.DataFrame: Query result.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(query)
        res = cursor.fetchall()
        return res

    def _df_query(self, query):
        """
        Execute a SQL query on the file and return the result as a DataFrame.
        Args:
            query (str): SQL query string.
        Returns:
            pd.DataFrame: Query result.
        """
        conn = self._get_connection()
        df = pd.read_sql(query, conn)
        return df

    def _df_to_tabledict(self, df):
        """
        Convert a DataFrame of series metadata into a list of dictionaries for extraction.
        Args:
            df (pd.DataFrame): DataFrame with series metadata.
        Returns:
            list[dict]: List of dictionaries with ReportName, ReportForString, TableName.
        """
        ziplist = list(zip(df['ReportName'].values.tolist(), df['ReportForString'].values.tolist(), df['TableName'].values.tolist()))
        zipdict = [{
            'ReportName': z[0],
            'ReportForString': z[1],
            'TableName': z[2]
        } for z in ziplist]
        return zipdict


    def _filter_tabular(self, filterquery):
        """
        Filter available series data for any string, returning matching rows as a DataFrame.
        Args:
            filterquery (str): String to search for in series metadata.
        Returns:
            pd.DataFrame: Filtered DataFrame.
        """
        avail = self.availseries()
        df = avail[avail.apply(lambda row: row.astype(str).str.contains(filterquery).any(), axis=1)]
        return df


    def _maketime(self):
        """
        Build a DataFrame of time indices and corresponding datetime values for hourly data.
        Cached after first call for performance.
        Returns:
            pd.DataFrame: DataFrame with time indices and datetime values.
        """
        # Return cached version if available
        if self._time_cache is not None:
            return self._time_cache

        timedf = self._df_query("SELECT * FROM Time WHERE Interval = 60")

        def zeropad(val):
            if len(str(val)) == 1:
                val = '0' + str(val)
                return val
            else:
                return val

        timedf['Hour'] = timedf['Hour'] - 1
        timedf['Month'] = timedf['Month'].apply(lambda x: zeropad(x))
        timedf['Day'] = timedf['Day'].apply(lambda x: zeropad(x))
        timedf['Hour'] = timedf['Hour'].apply(lambda x: zeropad(x))
        timedf['dt'] = timedf['Month'].astype(str) + "-" + timedf['Day'].astype(str) + "-" + timedf['Hour'].astype(str)
        dtformat = "%m-%d-%H"
        timedf['dt'] = pd.to_datetime(timedf['dt'], format=dtformat)

        # Cache the result
        self._time_cache = timedf
        return timedf


    # public functions


    def availseries(self):
        """
        Return a DataFrame of all available hourly series.
        Returns:
            pd.DataFrame: DataFrame of available series.
        """

        rddcols = [
            'ReportDataDictionaryIndex',
            'IsMeter',
            'Type',
            'IndexGroup',
            'TimestepType',
            'KeyValue',
            'Name',
            'ReportingFrequency',
            'ScheduleName',
            'Units'
        ]

        df = self._df_query("SELECT * FROM ReportDataDictionary WHERE ReportingFrequency = 'Hourly'")
        df.columns = rddcols

        return df.to_dict(orient='records')

        return df.T.to_dict()

    def queryseries(self, filterquery):
        """
        Filter available series for a string and return the matching DataFrame.
        Args:
            filterquery (str): String to search for in series names.
        Returns:
            pd.DataFrame: Filtered DataFrame.
        """
        df = self.availseries()
        df = self._filter_tabular(filterquery)
        return df



    def getseries_by_record_id(self, rddid: int):
        """
            Given a dictionary generated from available , return the corresponding time series as a DataFrame with a datetime index.
            Args:
                rddid: ReportDataDictionary Index, int

            Returns:
                list of dictionaries

            """


        # rddi = str(tuple(df.ReportDataDictionaryIndex))
        # return rddi

        labelquery = self._exec_query(f"SELECT * FROM ReportDataDictionary WHERE ReportDataDictionaryIndex == {rddid}")
        if len(labelquery) == 1:
            labelquery = labelquery[0]
        elif len(labelquery) > 1:
            print(f'warning - multiple found for {labelquery}')
        else:
            print(f'none found for {labelquery}')


        ReportDataDictionaryIndex, IsMeter, Type, IndexGroup, TimestepType, KeyValue, Name, ReportingFrequency, ScheduleName, Units = labelquery

        listquery = f'SELECT "Value","ReportDataDictionaryIndex","TimeIndex" FROM "ReportData" WHERE "ReportDataDictionaryIndex" == {rddid}'
        df_query = self._df_query(listquery)

        df_query['Name'] = Name
        df_query['ScheduleName'] = ScheduleName
        df_query['TimestepType'] = TimestepType
        df_query['Type'] = Type
        df_query['IndexGroup'] = IndexGroup
        df_query['KeyValue'] = KeyValue
        df_query['Units'] = Units
        df_query['IsMeter'] = IsMeter
        df_query['ReportingFrequency'] = ReportingFrequency


        time = self._maketime()[['TimeIndex', 'dt']]

        dfp = pd.merge(left=df_query, right=time, left_on='TimeIndex', right_on='TimeIndex')


        dfp = dfp[[
            'dt',
            'KeyValue',
            'Name',
            'TimestepType',
            'IndexGroup',
            'ScheduleName',
            'Units',
            'IsMeter',
            'ReportingFrequency',
            'Type',
            "Value"
        ]]



        return dfp.to_dict('records')

    def old_getseries(self, df: pd.DataFrame):
        """
        Given a filtered DataFrame, return the corresponding time series as a DataFrame with a datetime index.
        Args:
            df (pd.DataFrame): Filtered DataFrame from queryseries.
        Returns:
            pd.DataFrame: Pivoted DataFrame with datetime index and multi-index columns.
        """


        rddi = str(tuple(df.ReportDataDictionaryIndex))
        # return rddi

        listquery = 'SELECT "Value","ReportDataDictionaryIndex","TimeIndex" FROM "ReportData" WHERE "ReportDataDictionaryIndex" IN ' + rddi
        df_query = self._df_query(listquery)


        time = self._maketime()[['TimeIndex', 'dt']]

        dfp = pd.merge(left=df_query, right=df, on='ReportDataDictionaryIndex')

        dfp = pd.pivot_table(dfp, columns=['IndexGroup', 'TimestepType', 'KeyValue', 'Name', 'Units'], index='TimeIndex', values='Value')

        timedict = time.set_index('TimeIndex').to_dict()['dt']

        dfp = dfp.reset_index()

        dfp['dt'] = dfp.apply(lambda x: timedict[int(x['TimeIndex'].values[0])], axis=1)

        dfp = dfp.set_index('dt', drop=True)

        dfp = dfp.drop("TimeIndex", axis=1)

        idx = pd.MultiIndex.from_tuples(list(dfp.columns))

        dfp.columns = idx

        return dfp
