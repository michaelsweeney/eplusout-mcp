#!/usr/bin/env python3
"""
Test script for MCP logging functionality
"""

from monitor import setup_logging, log_mcp_call, get_log_stats
import sys
import os
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))



def test_logging():
    """Test the logging system"""
    print("Testing MCP logging system...")

    # Setup logging
    log_file = setup_logging()
    print(f"Log file path: {log_file.absolute()}")
    print(f"Log file exists: {log_file.exists()}")

    # Test a log entry
    log_mcp_call(
        function_name="test_function",
        args=("arg1", "arg2"),
        kwargs={"param1": "value1", "param2": 42},
        result="Test result with some data",
        duration=0.123,
        success=True,
        error_message=None
    )

    print(f"Log file exists after logging: {log_file.exists()}")

    if log_file.exists():
        print(f"Log file size: {log_file.stat().st_size} bytes")

        # Read and display log content
        with open(log_file, 'r') as f:
            content = f.read()
            print("\nLog file content:")
            print(content)

    # Get stats
    stats = get_log_stats()
    print(f"\nLog stats: {stats}")


if __name__ == "__main__":
    test_logging()
