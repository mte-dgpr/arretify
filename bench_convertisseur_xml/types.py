import re
from typing import List, Union, Tuple
from enum import Enum
from dataclasses import dataclass

from bs4 import PageElement


ELEMENT_NAME_PATTERN = re.compile(r"^[a-z0-9_]+$")


@dataclass(frozen=True)
class DataElementSchema:
    name: str
    tag_name: str
    data_keys: List[str]

    def __post_init__(self):
        matched = ELEMENT_NAME_PATTERN.match(self.name)
        if not matched:
            raise ValueError(f"Invalid name: {self.name}")
        if "element_id" in self.data_keys:
            raise ValueError("element_id is a reserved key")


class OperationType(Enum):
    ADD = "add"
    DELETE = "delete"
    REPLACE = "replace"


PageElementOrString = Union[PageElement, str]
LineColumn = Tuple[int, int]
"""Tuple line and column number. Line and column numbers are 0-indexed."""

URI = str
"""
Custom URIs for references to documents and sections. The format is as follows:

dsr://<type>_<id>_<num>_<date>_<title>/<type>_<start_id>_<start_num>_<end_id>_<end_num>/
"""

ExternalURL = str

ElementId = str
"""
A unique id assigned to elements in the DOM as `data-element_id` attribute.
This provides an alternative to referencing an element in the DOM
using its `id` attribute, because `id` has meaning in HTML which
we don't want to interfere with.
"""
