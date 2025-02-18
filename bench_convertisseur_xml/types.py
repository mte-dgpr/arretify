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