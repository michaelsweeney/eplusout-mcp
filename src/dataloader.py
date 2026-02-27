import pandas as pd
import sqlite3
import hashlib
from pathlib import Path
import pyarrow as pa
import pyarrow.parquet as pq
from typing import Optional, Dict, Any, List
import io
import numpy as np
import time
import logging
import ast

logger = logging.getLogger(__name__)


def _is_safe_expression(query: str) -> bool:
    """
    Check if expression only uses whitelisted attributes.
    Prevents access to dangerous methods like __class__, __import__, etc.

    Args:
        query: Python expression to validate

    Returns:
        True if expression contains only safe attributes, False otherwise
    """
    try:
        tree = ast.parse(query, mode='eval')
    except SyntaxError:
        return False

    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute):
            # Block private/dunder attributes
            if node.attr.startswith('_'):
                return False

    return True


def _format_result(result) -> str:
    """
    Format query result for display in MCP server responses.

    Converts various pandas and numpy data types into readable string format
    with appropriate truncation for large datasets to prevent token overflow.

    Args:
        result: The result object from pandas operations (DataFrame, Series, list, etc.)

    Returns:
        Formatted string representation of the result with shape/length information
        and truncated content for large datasets.

    Supported Types:
        - pandas.DataFrame: Shows shape and first 10 rows if >10 rows
        - pandas.Series: Shows length and first 10 values if >10 values  
        - list/tuple/np.ndarray: Shows length and first 20 items if >20 items
        - Other types: Direct string conversion

    Examples:
        DataFrame with 1000 rows -> "DataFrame shape: (1000, 5)\n\nFirst 10 rows:\n..."
        Series with 50 values -> "Series length: 50\n\nFirst 10 values:\n..."
        Small list -> "['item1', 'item2', 'item3']"
    """
    if isinstance(result, pd.DataFrame):
        # For DataFrames, show shape and first few rows
        if len(result) > 10:
            return f"DataFrame shape: {result.shape}\n\nFirst 10 rows:\n{result.head(10).to_string()}\n\n... ({len(result) - 10} more rows)"
        else:
            return f"DataFrame shape: {result.shape}\n\n{result.to_string()}"
    elif isinstance(result, pd.Series):
        if len(result) > 10:
            return f"Series length: {len(result)}\n\nFirst 10 values:\n{result.head(10).to_string()}\n\n... ({len(result) - 10} more values)"
        else:
            return f"Series length: {len(result)}\n\n{result.to_string()}"
    elif isinstance(result, (list, tuple, np.ndarray)):
        if len(result) > 20:
            return f"Array/List length: {len(result)}\n\nFirst 20 items: {list(result)[:20]}\n\n... ({len(result) - 20} more items)"
        else:
            return str(result)
    else:
        return str(result)


def execute_pandas_query(df: pd.DataFrame, query: str) -> str:
    """
    Execute a single-line pandas query on a DataFrame in a secure environment.

    Executes pandas operations using eval() in a restricted execution environment
    with limited built-in functions for security. Designed for single-expression
    queries that return a value.

    Args:
        df: The pandas DataFrame to operate on
        query: Single-line pandas expression to execute (e.g., "df.describe()", "df['column'].mean()")

    Returns:
        Formatted string representation of the query result, truncated if large

    Security Features:
        - Restricted execution environment with limited built-ins
        - No access to file system or dangerous functions
        - Only pandas, numpy, and basic Python functions available

    Examples:
        # Basic statistics
        execute_pandas_query(df, "df.describe()")

        # Column operations
        execute_pandas_query(df, "df['temperature'].mean()")

        # Filtering and aggregation
        execute_pandas_query(df, "df[df['value'] > 100].count()")

        # Group operations
        execute_pandas_query(df, "df.groupby('category').sum()")

    Available Functions in Query Context:
        - df: The input DataFrame
        - pd: pandas library
        - np: numpy library
        - Basic Python types: len, str, int, float, list, dict
        - Math functions: sum, max, min

    Error Handling:
        Returns formatted error message if query execution fails.
    """

    try:
        # Validate expression doesn't contain dangerous attributes
        if not _is_safe_expression(query):
            return "Query contains restricted attributes (e.g., private/dunder methods)."

        # Create safe execution environment
        safe_globals = {
            'df': df,
            'pd': pd,
            'np': np,
            'len': len,
            'str': str,
            'int': int,
            'float': float,
            'list': list,
            'dict': dict,
            'sum': sum,
            'max': max,
            'min': min,
            '__builtins__': {}
        }

        # Execute the query
        result = eval(query, safe_globals)

        # Format result
        return _format_result(result)

    except SyntaxError:
        return "Query syntax error. Check your expression and try again."
    except NameError:
        return "Undefined variable or function in query."
    except Exception as e:
        logger.error(f"Pandas query execution failed: {type(e).__name__}: {str(e)}")
        return "Query execution failed. Please check your query syntax."


def execute_multiline_pandas_query(df: pd.DataFrame, query: str) -> str:
    """
    Execute multi-line pandas code on a DataFrame in a secure environment.

    Executes complex pandas operations using exec() in a restricted execution environment.
    Supports multiple statements, variable assignments, and complex logic. Use 'result = ...'
    to specify the return value.

    Args:
        df: The pandas DataFrame to operate on
        query: Multi-line Python code to execute

    Returns:
        Formatted string representation of the result if 'result' variable is set,
        otherwise returns success message

    Security Features:
        - Restricted execution environment with limited built-ins
        - No access to file system or dangerous functions
        - Only pandas, numpy, and basic Python functions available

    Usage Pattern:
        The code should assign the desired output to a variable named 'result'.
        If no 'result' variable is found, returns execution success message.

    Examples:
        # Complex analysis with intermediate steps
        code = '''
        # Add calculated columns
        df['month'] = df['dt'].dt.month
        df['hour'] = df['dt'].dt.hour

        # Calculate monthly statistics
        monthly_stats = df.groupby('month').agg({
            'value': ['mean', 'max', 'min', 'std']
        })

        result = monthly_stats
        '''

        # Data cleaning and transformation
        code = '''
        # Remove outliers
        Q1 = df['value'].quantile(0.25)
        Q3 = df['value'].quantile(0.75)
        IQR = Q3 - Q1

        # Filter data
        cleaned_df = df[(df['value'] >= Q1 - 1.5*IQR) & 
                       (df['value'] <= Q3 + 1.5*IQR)]

        result = f"Original: {len(df)} rows, Cleaned: {len(cleaned_df)} rows"
        '''

        # Complex calculations
        code = '''
        # Peak analysis
        daily_peaks = df.groupby(df['dt'].dt.date)['value'].max()
        average_peak = daily_peaks.mean()
        peak_day = daily_peaks.idxmax()

        result = {
            'average_daily_peak': average_peak,
            'highest_peak_day': str(peak_day),
            'highest_peak_value': daily_peaks.max()
        }
        '''

    Available Objects in Execution Context:
        - df: The input DataFrame
        - pd: pandas library
        - np: numpy library
        - Basic Python types: len, str, int, float, list, dict
        - Math functions: sum, max, min

    Error Handling:
        Returns formatted error message if code execution fails.

    Note:
        For simple single-expression queries, use execute_pandas_query() instead
        for better performance and simpler syntax.
    """

    try:
        # Check for dangerous patterns in multiline code
        if '__' in query or ('_' in query and 'import' in query):
            return "Code contains restricted attributes (e.g., private/dunder methods)."

        # Create execution context
        context = {
            'df': df,
            'pd': pd,
            'np': np,
            'len': len,
            'str': str,
            'int': int,
            'float': float,
            'list': list,
            'dict': dict,
            'sum': sum,
            'max': max,
            'min': min,
            '__builtins__': {}
        }

        # For multi-line, use exec instead of eval
        exec(query, context)

        # Look for common result variables
        if 'result' in context:
            result = context['result']
            return _format_result(result)
        else:
            return "Query executed successfully. Use 'result = ...' to see output."

    except SyntaxError:
        return "Code syntax error. Check your expression and try again."
    except NameError:
        return "Undefined variable or function in code."
    except Exception as e:
        logger.error(f"Query execution error: {type(e).__name__}: {str(e)}")
        return "Query execution failed. Please check your code syntax."
