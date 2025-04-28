import re
from typing import List, Union, Tuple, Optional
from enum import Enum
from dataclasses import dataclass, fields

from bs4 import BeautifulSoup, PageElement
from arretify._vendor.clients_api_droit.clients_api_droit.legifrance import LegifranceClient
from arretify._vendor.clients_api_droit.clients_api_droit.eurlex import EurlexClient

from arretify.settings import Settings


ELEMENT_NAME_PATTERN = re.compile(r"^[a-z0-9_]+$")


LineColumn = Tuple[int, int]
"""Tuple line and column number. Line and column numbers are 0-indexed."""


@dataclass(frozen=True)
class TextSegment:
    start: LineColumn
    end: LineColumn
    contents: str


TextSegments = List[TextSegment]


@dataclass(frozen=True, kw_only=True)
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


@dataclass(frozen=True, kw_only=True)
class SessionContext:
    settings: Settings
    legifrance_client: Optional[LegifranceClient] = None
    eurlex_client: Optional[EurlexClient] = None


@dataclass(frozen=True, kw_only=True)
class ParsingContext(SessionContext):
    """
    Container for parsing context information.
    This includes the lines of text being parsed, the BeautifulSoup object,
    and the settings used for parsing.
    """

    lines: TextSegments
    soup: BeautifulSoup

    @classmethod
    def from_session_context(
        cls,
        session_context: SessionContext,
        lines: TextSegments,
        soup: BeautifulSoup,
    ) -> "ParsingContext":
        return cls(
            **{
                field.name: getattr(session_context, field.name) for field in fields(SessionContext)
            },
            lines=lines,
            soup=soup,
        )


PageElementOrString = Union[PageElement, str]

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
