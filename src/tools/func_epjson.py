from html.parser import HTMLParser
from typing import List
from typing import Optional
from typing import Dict
from typing import Tuple

import re


import json


def read_epjson(epjsonfile: str) -> dict:
    """
    Read and parse epJSON file.

    Args:
        epjsonfile: Path to the epJSON file

    Returns:
        Parsed JSON content as dictionary

    Raises:
        ValueError: If file contains invalid JSON
        IOError: If file cannot be read
    """
    try:
        with open(epjsonfile, 'r') as f:
            epjd = json.load(f)
        return epjd
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in epJSON file: {str(e)[:50]}")
    except Exception as e:
        raise IOError(f"Cannot read epJSON file: Permission denied or file not found")
