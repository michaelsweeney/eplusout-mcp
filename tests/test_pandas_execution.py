"""Tests for the safe pandas execution sandbox."""

import pandas as pd
import numpy as np
from src.dataloader import (
    execute_pandas_query,
    execute_multiline_pandas_query,
    _format_result,
    _is_safe_expression,
)


def _sample_df():
    return pd.DataFrame({"a": [1, 2, 3, 4, 5], "b": [10, 20, 30, 40, 50]})


# --- _is_safe_expression ---

def test_safe_expression_allowed():
    assert _is_safe_expression("df['a'].sum()") is True


def test_dunder_expression_blocked():
    assert _is_safe_expression("df.__class__") is False


# --- execute_pandas_query ---

def test_basic_sum():
    df = _sample_df()
    result = execute_pandas_query(df, "df['a'].sum()")
    assert "15" in result


def test_basic_mean():
    df = _sample_df()
    result = execute_pandas_query(df, "df['b'].mean()")
    assert "30" in result


def test_dunder_rejected():
    df = _sample_df()
    result = execute_pandas_query(df, "df.__class__.__name__")
    assert "restricted" in result.lower()


def test_syntax_error():
    df = _sample_df()
    result = execute_pandas_query(df, "df[['a'")
    # _is_safe_expression returns False on SyntaxError, so "restricted" message is returned
    assert "restricted" in result.lower() or "syntax" in result.lower()


# --- execute_multiline_pandas_query ---

def test_multiline_with_result():
    df = _sample_df()
    code = "total = df['a'].sum()\nresult = total"
    result = execute_multiline_pandas_query(df, code)
    assert "15" in result


def test_multiline_without_result():
    df = _sample_df()
    code = "x = df['a'].sum()"
    result = execute_multiline_pandas_query(df, code)
    assert "result" in result.lower()


def test_multiline_import_blocked():
    df = _sample_df()
    code = "__import__('os').listdir('.')"
    result = execute_multiline_pandas_query(df, code)
    assert "restricted" in result.lower()


# --- _format_result ---

def test_format_small_dataframe():
    df = pd.DataFrame({"x": [1, 2, 3]})
    result = _format_result(df)
    assert "DataFrame shape: (3, 1)" in result


def test_format_large_dataframe_truncated():
    df = pd.DataFrame({"x": range(100)})
    result = _format_result(df)
    assert "First 10 rows" in result
    assert "90 more rows" in result


def test_format_series():
    s = pd.Series(range(5))
    result = _format_result(s)
    assert "Series length: 5" in result


def test_format_large_list():
    result = _format_result(list(range(50)))
    assert "First 20 items" in result
    assert "30 more items" in result


def test_format_scalar():
    result = _format_result(42)
    assert result == "42"
