import tiktoken
import time
import os
import json
from pathlib import Path
from datetime import datetime
from functools import wraps
from typing import Any, Dict


def estimate_tokens(text: str, model: str = "cl100k_base") -> int:
    """
    Estimate token count for text using tiktoken encoding.

    Args:
        text: Text string to count tokens for
        model: Tiktoken encoding model name (default: "cl100k_base")

    Returns:
        Integer count of estimated tokens
    """
    if not text:
        return 0

    try:
        encoding = tiktoken.get_encoding(model)
        return len(encoding.encode(text))
    except Exception:
        # Fallback to simple estimation
        return int(len(str(text).split()) * 1.3)


def setup_logging() -> Path:
    """
    Set up the logging directory and return the log file path.

    Returns:
        Path to the log file
    """
    # Get the project root directory (parent of src)
    project_root = Path(__file__).parent.parent
    log_dir = project_root / 'monitor_logs'

    # Create directory if it doesn't exist
    log_dir.mkdir(exist_ok=True)

    return log_dir / 'mcp_calls.log'


def log_mcp_call(
    function_name: str,
    result: Any,
    kwargs: dict = {},
    args: tuple = ()
    # duration: float,
    # success: bool,
    # error_message: str = None
) -> None:
    """
    Log MCP function call details to file.

    Args:
        function_name: Name of the MCP function that was called
        args: Function arguments
        kwargs: Function keyword arguments
        result: Function return value
        duration: Execution time in seconds
        success: Boolean indicating if the call succeeded
        error_message: Error message if the call failed
    """
    log_file = setup_logging()

    # Estimate tokens
    input_text = f"args: {args}, kwargs: {kwargs}"
    output_text = str(result) if result is not None else ""

    input_tokens = estimate_tokens(input_text)
    output_tokens = estimate_tokens(output_text)

    # Create log entry
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "function_name": function_name,
        # "duration_seconds": round(duration, 4),
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
        # "success": success,
        # "error_message": error_message,
        "args_summary": str(args)[:200] + "..." if len(str(args)) > 200 else str(args),
        "kwargs_summary": str(kwargs)[:200] + "..." if len(str(kwargs)) > 200 else str(kwargs),
        "result_summary": str(result)[:200] + "..." if len(str(result)) > 200 else str(result)
    }

    try:
        # Append to log file
        with open(log_file, 'a', encoding='utf-8') as f:
            # Write as JSON line
            f.write(json.dumps(log_entry) + '\n')

        # Also print to console for immediate feedback
        # print(f"[MCP LOG] {function_name}: {duration:.3f}s, {input_tokens + output_tokens} tokens, {'✓' if success else '✗'}")

    except Exception as e:
        # Fallback to console only if file logging fails
        print(f"[MCP LOG ERROR] Failed to write log: {e}")
        # print(f"[MCP LOG] {function_name}: {duration:.3f}s, {input_tokens + output_tokens} tokens, {'✓' if success else '✗'}")


def monitor_mcp_call(func):
    """
    Decorator to monitor FastMCP function calls with performance metrics.

    This decorator works with FastMCP by wrapping the function execution
    and logging detailed metrics including timing and token usage.

    Args:
        func: The MCP function to be monitored

    Returns:
        Wrapped function that logs metrics while preserving original behavior
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        function_name = func.__name__

        try:
            result = func(*args, **kwargs)
            success = True
            error_message = None
        except Exception as e:
            result = None
            success = False
            error_message = str(e)
            # Re-raise the exception to maintain original behavior
            raise
        finally:
            end_time = time.time()
            duration = end_time - start_time

            # Log the call
            log_mcp_call(
                function_name=function_name,
                args=args,
                kwargs=kwargs,
                result=result,
                duration=duration,
                success=success,
                error_message=error_message
            )

        return result

    return wrapper


def get_log_stats() -> Dict[str, Any]:
    """
    Get statistics from the MCP call logs.

    Returns:
        Dictionary with log statistics
    """
    log_file = setup_logging()

    if not log_file.exists():
        return {"error": "No log file found"}

    try:
        stats = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "total_tokens": 0,
            "total_duration": 0,
            "functions": {}
        }

        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    stats["total_calls"] += 1

                    if entry["success"]:
                        stats["successful_calls"] += 1
                    else:
                        stats["failed_calls"] += 1

                    stats["total_tokens"] += entry["total_tokens"]
                    stats["total_duration"] += entry["duration_seconds"]

                    func_name = entry["function_name"]
                    if func_name not in stats["functions"]:
                        stats["functions"][func_name] = {"calls": 0, "tokens": 0, "duration": 0}

                    stats["functions"][func_name]["calls"] += 1
                    stats["functions"][func_name]["tokens"] += entry["total_tokens"]
                    stats["functions"][func_name]["duration"] += entry["duration_seconds"]

                except json.JSONDecodeError:
                    continue

        return stats

    except Exception as e:
        return {"error": f"Failed to read log file: {e}"}


def clear_logs() -> str:
    """
    Clear the MCP call logs.

    Returns:
        Status message
    """
    log_file = setup_logging()

    try:
        if log_file.exists():
            log_file.unlink()
        return "Logs cleared successfully"
    except Exception as e:
        return f"Failed to clear logs: {e}"
