import re
from typing import List, Union, Iterable, Tuple
from enum import Enum
from dataclasses import dataclass

from bs4 import PageElement


@dataclass(frozen=True)
class DataElementSchema:
    name: str
    tag_name: str
    data_keys: List[str]


class OperationType(Enum):
    ADD = 'add'
    DELETE = 'delete'
    REPLACE = 'replace'


PageElementOrString = Union[PageElement, str]
LineColumn = Tuple[int, int]
"""Tuple line and column number. Line and column numbers are 0-indexed."""

URI = str
"""
Custom URIs for references to documents and sections. The format is as follows:

dsr://<type>_<id>_<num>_<date>_<title>/<type>_<start_id>_<start_num>_<end_id>_<end_num>/
"""

ExternalURL = str