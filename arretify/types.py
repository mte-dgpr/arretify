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
from typing import Sequence, Union, Tuple, Optional, Type, TypeVar
from enum import Enum
from dataclasses import dataclass, fields, field
from uuid import uuid4

from bs4 import BeautifulSoup, PageElement
from arretify._vendor.clients_api_droit.clients_api_droit.legifrance import LegifranceClient
from arretify._vendor.clients_api_droit.clients_api_droit.eurlex import EurlexClient
from arretify._vendor import mistralai

from arretify.settings import Settings


DocumentContextType = TypeVar("DocumentContextType", bound="DocumentContext")

PageLineColumn = Tuple[int, int, int]
"""Tuple page, line and column number. All values are 0-indexed."""


class DocumentType(Enum):
    unknown = "unknown"

    self = "self"
    """Self reference"""

    unknown_arrete = "arrete"
    arrete_prefectoral = "arrete-prefectoral"
    arrete_ministeriel = "arrete-ministeriel"
    decret = "decret"
    circulaire = "circulaire"
    code = "code"
    """Code juridique (https://www.legifrance.gouv.fr/liste/code)"""

    eu_regulation = "eu-regulation"
    """
    EU regulation. (https://style-guide.europa.eu &
    https://style-guide.europa.eu/fr/content/-/isg/topic?identifier=1.2.1-classification-of-acts)
    """

    eu_directive = "eu-directive"
    """
    EU directive. (https://style-guide.europa.eu &
    https://style-guide.europa.eu/fr/content/-/isg/topic?identifier=1.2.1-classification-of-acts)
    """

    eu_decision = "eu-decision"
    """
    EU decision. (https://style-guide.europa.eu &
    https://style-guide.europa.eu/fr/content/-/isg/topic?identifier=1.2.1-classification-of-acts)
    """


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

    pages: Optional[Sequence[str]]
    """
    Contents of the markdown pages after OCR processing.
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
        pages: Sequence[str] | None = None,
    ) -> DocumentContextType:
        if filename is None:
            filename = str(uuid4())
        return cls(
            **{
                field.name: getattr(session_context, field.name) for field in fields(SessionContext)
            },
            filename=filename,
            pdf=pdf,
            pages=pages,
            soup=soup,
        )


PageElementOrString = Union[PageElement, str]

ExternalURL = str

TagId = str
"""
A unique id assigned to tags in the DOM as `data-tag_id` attribute.
This provides an alternative to referencing a tag in the DOM
using its `id` attribute, because `id` has meaning in HTML which
we don't want to interfere with.
"""

TagGroupId = str
"""
A unique id assigned to groups of tags in the DOM as `data-group_id` attribute.
"""
