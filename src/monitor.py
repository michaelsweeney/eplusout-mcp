import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Any


def estimate_tokens(text: str) -> int:
    """Estimate token count using character-based heuristic (~4 chars per token)."""
    if not text:
        return 0
    return len(str(text)) // 4


def setup_logging() -> Path:
    """Set up the logging directory and return the log file path."""
    project_root = Path(__file__).parent.parent
    log_dir = project_root / 'monitor_logs'
    log_dir.mkdir(exist_ok=True)
    return log_dir / 'mcp_calls.log'


def log_mcp_call(
    function_name: str,
    result: Any,
    kwargs: dict | None = None,
    args: tuple = ()
) -> None:
    """Log MCP function call details to file."""
    if kwargs is None:
        kwargs = {}

    log_file = setup_logging()

    input_text = f"args: {args}, kwargs: {kwargs}"
    output_text = str(result) if result is not None else ""

    input_tokens = estimate_tokens(input_text)
    output_tokens = estimate_tokens(output_text)

    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "function_name": function_name,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
        "args_summary": str(args)[:200] + "..." if len(str(args)) > 200 else str(args),
        "kwargs_summary": str(kwargs)[:200] + "..." if len(str(kwargs)) > 200 else str(kwargs),
        "result_summary": str(result)[:200] + "..." if len(str(result)) > 200 else str(result)
    }

    try:
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry) + '\n')
    except Exception as e:
        logging.getLogger(__name__).error(f"Failed to write MCP log: {e}")
