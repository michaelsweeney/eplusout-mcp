import ast
import signal
import json
import pandas as pd
import numpy as np
from typing import Any

BLOCKED_NAMES = frozenset({
    "os", "sys", "subprocess", "shutil", "pathlib", "socket",
    "requests", "urllib", "http", "ftplib", "smtplib",
    "open", "exec", "eval", "compile", "__import__",
    "getattr", "setattr", "delattr", "globals", "locals",
    "breakpoint", "exit", "quit",
})

BLOCKED_DUNDERS = frozenset({
    "__builtins__", "__class__", "__subclasses__", "__globals__",
    "__code__", "__import__", "__bases__", "__mro__",
})

MAX_OUTPUT_CHARS = 50_000
TIMEOUT_SECONDS = 30


class SandboxViolation(Exception):
    pass


class _Validator(ast.NodeVisitor):
    def visit_Import(self, node):
        raise SandboxViolation(f"import statements are not allowed: {ast.dump(node)}")

    def visit_ImportFrom(self, node):
        raise SandboxViolation(f"import statements are not allowed: from {node.module}")

    def visit_Name(self, node):
        if node.id in BLOCKED_NAMES:
            raise SandboxViolation(f"'{node.id}' is not allowed")
        self.generic_visit(node)

    def visit_Attribute(self, node):
        if node.attr in BLOCKED_DUNDERS:
            raise SandboxViolation(f"access to '{node.attr}' is not allowed")
        if node.attr in BLOCKED_NAMES:
            raise SandboxViolation(f"'{node.attr}' is not allowed")
        self.generic_visit(node)

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name) and node.func.id in BLOCKED_NAMES:
            raise SandboxViolation(f"calling '{node.func.id}' is not allowed")
        self.generic_visit(node)


def validate_code(code: str) -> ast.Module:
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        raise SandboxViolation(f"Syntax error: {e}")
    _Validator().visit(tree)
    return tree


def execute_sandboxed(code: str, data_globals: dict) -> dict:
    sandbox_globals = {
        "__builtins__": {},
        "pd": pd,
        "np": np,
        "print": print,
        "len": len,
        "range": range,
        "enumerate": enumerate,
        "zip": zip,
        "min": min,
        "max": max,
        "sum": sum,
        "abs": abs,
        "round": round,
        "sorted": sorted,
        "isinstance": isinstance,
        "dict": dict,
        "list": list,
        "tuple": tuple,
        "set": set,
        "str": str,
        "int": int,
        "float": float,
        "bool": bool,
        "type": type,
        "True": True,
        "False": False,
        "None": None,
    }
    sandbox_globals.update(data_globals)

    tree = ast.parse(code)

    if tree.body and isinstance(tree.body[-1], ast.Expr):
        last_expr = tree.body.pop()
        target = ast.Name(id="_result_", ctx=ast.Store())
        ast.copy_location(target, last_expr)
        assign = ast.Assign(
            targets=[target],
            value=last_expr.value,
        )
        ast.copy_location(assign, last_expr)
        ast.fix_missing_locations(assign)
        tree.body.append(assign)

    compiled = compile(tree, "<sandbox>", "exec")
    local_ns = {}

    def _timeout_handler(signum, frame):
        raise TimeoutError(f"Execution timed out after {TIMEOUT_SECONDS}s")

    old_handler = signal.signal(signal.SIGALRM, _timeout_handler)
    signal.alarm(TIMEOUT_SECONDS)

    try:
        exec(compiled, sandbox_globals, local_ns)
        result = local_ns.get("_result_", None)
    except TimeoutError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"}
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)

    return _serialize_result(result)


def _serialize_result(result: Any) -> dict:
    if isinstance(result, pd.DataFrame):
        serialized = {
            "type": "DataFrame",
            "shape": list(result.shape),
            "columns": list(result.columns),
            "data": result.reset_index(drop=True).to_dict(orient="records"),
        }
    elif isinstance(result, pd.Series):
        serialized = {
            "type": "Series",
            "name": result.name,
            "data": result.to_dict(),
        }
    elif isinstance(result, (dict, list, tuple, int, float, str, bool, type(None))):
        serialized = {"result": result}
    else:
        serialized = {"result": str(result)}

    text = json.dumps(serialized, default=str)
    if len(text) > MAX_OUTPUT_CHARS:
        return {
            "error": f"Output too large ({len(text)} chars, max {MAX_OUTPUT_CHARS}). "
            "Filter or aggregate your data to reduce output size.",
            "output_size": len(text),
        }
    return serialized
