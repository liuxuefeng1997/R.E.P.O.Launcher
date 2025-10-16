import os
import sys


def resource_path(relative_path: str) -> str:
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    ret_path = os.path.join(base_path, relative_path)
    return ret_path
