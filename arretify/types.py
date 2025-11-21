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
from dataclasses import dataclass, field, fields
from enum import Enum
from pathlib import Path
from typing import Optional, Protocol, Sequence, Tuple, Type, TypeVar, Union, cast

from bs4 import BeautifulSoup, PageElement, Tag

from arretify._vendor import mistralai
from arretify._vendor.clients_api_droit.clients_api_droit.eurlex import EurlexClient
from arretify._vendor.clients_api_droit.clients_api_droit.legifrance import LegifranceClient
from arretify.settings import Settings

DocumentContextType = TypeVar("DocumentContextType", bound="DocumentContext")

PageLineColumn = Tuple[int, int, int]
"""Tuple page, line and column number. All values are 0-indexed."""


class _ProtectedBase(Protocol):
    @property
    def contents(self) -> list["ProtectedTagOrStr"]: ...
    def select(self, selector: str) -> list["ProtectedTag"]: ...


class ProtectedTag(_ProtectedBase, Protocol):
    """
    A BeautifulSoup Tag that is protected against any modification.
    This forces the use of utility functions to modify the tree and tag attributes,
    and enables us to enforce validation and consistency when modifying the DOM.
    """

    @property
    def name(self) -> str: ...

    def get(self, key: str, default=None) -> str | None: ...
    @property
    def attrs(self) -> dict[str, str]: ...
    def __getitem__(self, key: str) -> str: ...

    @property
    def parent(self) -> Union["ProtectedTag", "ProtectedSoup", None]: ...
    @property
    def next_sibling(self) -> Union["ProtectedTag", str, None]: ...
    @property
    def previous_sibling(self) -> Union["ProtectedTag", str, None]: ...


class ProtectedSoup(_ProtectedBase, Protocol):
    """
    A protected BeautifulSoup object that exposes only ProtectedTags.
    """

    @property
    def body(self) -> Optional[ProtectedTag]: ...


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
    This is used to ensure that each tag has a unique ID.
    """

    tag_id: int = 0
    """
    Counter for the `data-tag_id` attribute.
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

    input_path: Path | None
    """
    Path of the file / directory being processed.
    This is used to identify the parsing context and name the output files.
    """

    pdf: bytes | None
    """
    PDF of the arrêté. This is used for OCR processing.
    """

    pages: Sequence[str] | None
    """
    Contents of the markdown pages after OCR processing.
    """

    soup: BeautifulSoup

    id_counters: IdCounters = field(default_factory=IdCounters)

    @property
    def protected_soup(self) -> ProtectedSoup:
        return cast(ProtectedSoup, self.soup)

    @classmethod
    def from_session_context(
        cls: Type[DocumentContextType],
        session_context: SessionContext,
        soup: BeautifulSoup,
        input_path: Path | None = None,
        pdf: Optional[bytes] = None,
        pages: Sequence[str] | None = None,
    ) -> DocumentContextType:
        return cls(
            **{
                field.name: getattr(session_context, field.name) for field in fields(SessionContext)
            },
            input_path=input_path,
            pdf=pdf,
            pages=pages,
            soup=soup,
        )


ProtectedTagOrStr = ProtectedTag | str
"""
A type that can be either a ProtectedTag or a string.
Note that we cannot use a protected version of NavigableString, since
we want to be able to use `isinstance` checks directly throughout the codebase.
"""

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


# -------------------- Protect/Unprotect functions -------------------- #


def protect_tag(tag: Tag) -> ProtectedTag:
    return cast(ProtectedTag, tag)


def protect_soup(soup: BeautifulSoup) -> ProtectedSoup:
    return cast(ProtectedSoup, soup)


def unprotect_tag(protected_tag: ProtectedTag) -> Tag:
    return cast(Tag, protected_tag)


def unprotect_soup(protected_soup: ProtectedSoup) -> BeautifulSoup:
    return cast(BeautifulSoup, protected_soup)


def unprotect_page_element(
    protected_element: ProtectedTagOrStr,
) -> PageElement:
    """
    Use with care, make sure that `protected_element` is indeed a PageElement,
    and not a simple string which doesn't have the full PageElement functionality.
    """
    assert isinstance(protected_element, PageElement)
    return cast(PageElement, protected_element)
