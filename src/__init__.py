
import glob as gb
import pickle
import os
from pydantic import BaseModel
from typing import List, Literal
from bs4 import BeautifulSoup
import pandas as pd
from io import StringIO
import json
from pathlib import Path



BASE_DIRECTORY = Path(__file__).parent.parent.absolute()
CACHE_DIRECTORY = os.path.join(BASE_DIRECTORY, 'mcp_cache')
CACHE_PICKLE = os.path.join(CACHE_DIRECTORY, 'modelmap.pickle')

EPLUS_RUNS_DIRECTORY = Path(os.path.join(BASE_DIRECTORY, 'eplus_files')).absolute()
