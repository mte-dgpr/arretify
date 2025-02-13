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


class ModificationType(Enum):
    ADD = 'add'
    DELETE = 'delete'
    UPDATE = 'update'


PageElementOrString = Union[PageElement, str]
LineColumn = Tuple[int, int]