from html.parser import HTMLParser
from typing import List
from typing import Optional
from typing import Dict
from typing import Tuple

import re


import json


def read_epjson(epjsonfile: str) -> dict:


    with open(epjsonfile, 'r') as f:
        epjd = json.load(f)

    return epjd
