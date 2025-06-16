#
# Copyright (c) 2025 Direction générale de la prévention des risques (DGPR).
#
# This file is part of Arrêtify.
# See https://github.com/mte-dgpr/arretify for further info.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import re
from typing import List, Union, Tuple, Optional, Type, TypeVar, Dict
from enum import Enum
from dataclasses import dataclass, fields, field
from uuid import uuid4

from bs4 import BeautifulSoup, PageElement
from arretify._vendor.clients_api_droit.clients_api_droit.legifrance import LegifranceClient
from arretify._vendor.clients_api_droit.clients_api_droit.eurlex import EurlexClient
from arretify._vendor import mistralai

from arretify.settings import Settings


ELEMENT_NAME_PATTERN = re.compile(r"^[a-z0-9_]+$")
DocumentContextType = TypeVar("DocumentContextType", bound="DocumentContext")

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
        if "group_id" in self.data_keys:
            raise ValueError("group_id is a reserved key")


DataElementDataDict = Dict[str, str | None]


class SectionType(Enum):
    """
    Order in the enum is important. The order is used to determine the hierarchy of the sections.
    """

    ANNEXE = "annexe"
    TITRE = "titre"
    CHAPITRE = "chapitre"
    ARTICLE = "article"
    UNKNOWN = "unknown"
    """Unknown section type. Needs context to be resolved"""
    ALINEA = "alinea"

    @classmethod
    def from_string(cls, section_name):
        return cls(section_name.lower())


class OperationType(Enum):
    ADD = "add"
    DELETE = "delete"
    REPLACE = "replace"


@dataclass(frozen=True, kw_only=True)
class SessionContext:
    settings: Settings
    legifrance_client: Optional[LegifranceClient] = None
    eurlex_client: Optional[EurlexClient] = None
    mistral_client: Optional[mistralai.Mistral] = None


@dataclass
class IdCounters:
    """
    Container for the counters used to assign unique IDs to elements in the DOM.
    This is used to ensure that each element has a unique ID.
    """

    element_id: int = 0
    """
    Counter for the `data-element_id` attribute.
    This is used to assign unique IDs to elements in the DOM.
    """

    group_id: int = 0
    """
    Counter for the `data-group_id` attribute.
    This is used to assign unique IDs to groups of elements in the DOM.
    """


@dataclass(frozen=True, kw_only=True)
class DocumentContext(SessionContext):
    """
    Container for parsing context information.
    This includes the lines of text being parsed, the BeautifulSoup object,
    and the settings used for parsing.
    """

    filename: str
    """
    Name of the file being processed (without extension).
    This is used to identify the parsing context and name the output files.
    """

    pdf: Optional[bytes]
    """
    PDF of the arrêté. This is used for OCR processing.
    TODO : support for streaming PDF content
    """

    lines: Optional[TextSegments]
    """
    Contents of the markdown pages after OCR processing.
    TODO : TextSegments should keep track of pages from the original document
    """

    soup: BeautifulSoup

    id_counters: IdCounters = field(default_factory=IdCounters)

    @classmethod
    def from_session_context(
        cls: Type[DocumentContextType],
        session_context: SessionContext,
        soup: BeautifulSoup,
        filename: str | None = None,
        pdf: Optional[bytes] = None,
        lines: TextSegments | None = None,
    ) -> DocumentContextType:
        if filename is None:
            filename = str(uuid4())
        return cls(
            **{
                field.name: getattr(session_context, field.name) for field in fields(SessionContext)
            },
            filename=filename,
            pdf=pdf,
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

ElementGroupId = str
"""
A unique id assigned to groups of elements in the DOM as `data-group_id` attribute.
"""
