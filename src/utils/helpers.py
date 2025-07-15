from typing import Literal
import os


import os
import time


def get_json_diff(json1: list | dict, json2: list | dict, path: str = ""):
    differences = {}
    for key in json1.keys() | json2.keys():
        new_path = f"{path}/{key}" if path else key
        if key not in json1:
            differences[new_path] = {"added": json2[key]}
        elif key not in json2:
            differences[new_path] = {"removed": json1[key]}
        else:
            if isinstance(json1[key], dict) and isinstance(json2[key], dict):
                sub_diff = get_json_diff(json1[key], json2[key], new_path)
                if sub_diff:
                    differences.update(sub_diff)
            elif json1[key] != json2[key]:
                differences[new_path] = {"from": json1[key], "to": json2[key]}
    return differences





def gj_to_kwh(x): return x * 277.777778
