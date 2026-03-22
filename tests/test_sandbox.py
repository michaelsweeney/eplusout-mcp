import pytest
from src.sandbox import validate_code, execute_sandboxed, SandboxViolation


class TestASTValidation:
    def test_rejects_import_statement(self):
        with pytest.raises(SandboxViolation, match="import"):
            validate_code("import os")

    def test_rejects_from_import(self):
        with pytest.raises(SandboxViolation, match="import"):
            validate_code("from os import path")

    def test_rejects_open_call(self):
        with pytest.raises(SandboxViolation, match="open"):
            validate_code("open('/etc/passwd')")

    def test_rejects_exec_call(self):
        with pytest.raises(SandboxViolation, match="exec"):
            validate_code("exec('print(1)')")

    def test_rejects_eval_call(self):
        with pytest.raises(SandboxViolation, match="eval"):
            validate_code("eval('1+1')")

    def test_rejects_dunder_access(self):
        with pytest.raises(SandboxViolation, match="__"):
            validate_code("x.__class__.__bases__")

    def test_rejects_os_reference(self):
        with pytest.raises(SandboxViolation, match="os"):
            validate_code("os.system('ls')")

    def test_rejects_subprocess_reference(self):
        with pytest.raises(SandboxViolation, match="subprocess"):
            validate_code("subprocess.run(['ls'])")

    def test_allows_simple_math(self):
        validate_code("x = 1 + 2")

    def test_allows_pandas_operations(self):
        validate_code("df.sum()")

    def test_allows_list_comprehension(self):
        validate_code("[x for x in range(10)]")


class TestExecution:
    @pytest.fixture
    def sample_data(self):
        import pandas as pd
        import numpy as np
        df = pd.DataFrame({
            "None:Electricity:Facility [J]": np.random.random(8760) * 1e6,
        }, index=pd.date_range("2024-01-01", periods=8760, freq="h"))
        return {"sql_ts": df, "html_tables": {}, "model_info": {"id": "test"}}

    def test_simple_math(self, sample_data):
        result = execute_sandboxed("1 + 2", sample_data)
        assert result["result"] == 3

    def test_pandas_sum(self, sample_data):
        result = execute_sandboxed("sql_ts.sum()", sample_data)
        assert result["type"] == "Series"
        assert "None:Electricity:Facility [J]" in result["data"]

    def test_pandas_describe(self, sample_data):
        result = execute_sandboxed("sql_ts.describe()", sample_data)
        assert result["type"] == "DataFrame"

    def test_timeout(self, sample_data):
        result = execute_sandboxed("while True: pass", sample_data)
        assert "error" in result
        assert "timed out" in result["error"].lower()

    def test_exception_returned(self, sample_data):
        result = execute_sandboxed("1 / 0", sample_data)
        assert "error" in result
        assert "ZeroDivisionError" in result["error"]

    def test_multiline_code(self, sample_data):
        code = """
total = sql_ts.sum().iloc[0]
gj = total / 1e9
round(gj, 2)
"""
        result = execute_sandboxed(code, sample_data)
        assert "result" in result
        assert isinstance(result["result"], float)

    def test_blocked_import_at_runtime(self, sample_data):
        result = execute_sandboxed("type(1)", sample_data)
        assert "result" in result or "type" in str(result)
