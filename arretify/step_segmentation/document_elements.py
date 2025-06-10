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
from typing import Callable, Dict, List, Optional

from bs4 import Tag, BeautifulSoup

from arretify.html_schemas import DOCUMENT_ELEMENTS_SCHEMAS
from arretify.parsing_utils.source_mapping import TextSegments
from arretify.regex_utils import (
    PatternProxy,
    join_with_or,
)
from arretify.utils.html import (
    PageElementOrString,
    make_data_tag,
    wrap_in_tag,
)
from arretify.utils.markdown_parsing import is_image


PAGE_FOOTERS_LIST = [
    # "X/Y"
    r"\d+/\d+\s*",
    # "Page X/Y"
    r"page\s+\d+/\d+\s*",
    # "Page X sur Y"
    r"page\s+\d+\s+sur\s+\d+\s*",
    # "Page X"
    r"page\s+\d+",
]

PAGE_FOOTER_PATTERN = PatternProxy(rf"^{join_with_or(PAGE_FOOTERS_LIST)}")
"""Detect page footer."""

TABLE_OF_CONTENTS_PAGING_PATTERN_S = r"\.{5}\s+(page\s+)?\d+"
"""Detect table of contents paging, e.g. "..... page 1" or "..... 1"."""

IS_NOT_TABLE_OF_CONTENTS_PAGING_PATTERN_S = rf"(?!.*{TABLE_OF_CONTENTS_PAGING_PATTERN_S}$)"

TABLE_OF_CONTENTS_LIST = [
    r"sommaire",
    r"table des matieres",
    r"liste des (chapitres|articles)",
    rf".*?\s+{TABLE_OF_CONTENTS_PAGING_PATTERN_S}$",
]

TABLE_OF_CONTENTS_PATTERN = PatternProxy(rf"^{join_with_or(TABLE_OF_CONTENTS_LIST)}")
"""Detect all table of contents starting sentences."""

DOCUMENT_ELEMENTS_PATTERNS: Dict[str, PatternProxy] = {
    "page_footer": PAGE_FOOTER_PATTERN,
    "table_of_contents": TABLE_OF_CONTENTS_PATTERN,
}
"""Document elements patterns."""

DOCUMENT_ELEMENTS_PROBES: Dict[str, Callable] = {
    "page_footer": lambda line: bool(PAGE_FOOTER_PATTERN.match(line)),
    "table_of_contents": lambda line: bool(TABLE_OF_CONTENTS_PATTERN.match(line)),
}
"""Document elements probes."""


def _make_positive_probe(document_element_name: Optional[str] = None) -> Callable[[str], bool]:

    if document_element_name:

        if document_element_name not in DOCUMENT_ELEMENTS_PROBES:
            raise ValueError(
                f"Unknown document element name: {document_element_name}. "
                f"Available document elements: {list(DOCUMENT_ELEMENTS_PROBES.keys())}."
            )

        return DOCUMENT_ELEMENTS_PROBES[document_element_name]

    # If no specific document element is requested, we return a probe that checks for any
    # document element by checking all patterns
    def _probe(line: str) -> bool:
        return any(probe(line) for probe in DOCUMENT_ELEMENTS_PROBES.values())

    return _probe


def is_document_element(line: str) -> bool:
    """Detect if the line is a document element."""
    # Image strings can be very long, and table of contents pattern look at the end of the
    # sentence. So, we make sure we do not have an image in the line before checking for other
    # document elements
    return not is_image(line) and _make_positive_probe()(line)


def _parse_document_element(
    soup: BeautifulSoup,
    container: Tag,
    lines: TextSegments,
    document_element_name: str,
) -> TextSegments:
    pile: List[PageElementOrString] = []
    is_current_document_element = _make_positive_probe(document_element_name)
    document_element_schema = DOCUMENT_ELEMENTS_SCHEMAS[document_element_name]

    # Image strings can be very long, and table of contents pattern look at the end of the
    # sentence. So, we make sure we do not have an image in the line before checking for other
    # document elements
    while (
        lines and not is_image(lines[0].contents) and is_current_document_element(lines[0].contents)
    ):

        pile.append(lines.pop(0).contents)

    if pile:

        document_element = make_data_tag(
            soup,
            document_element_schema,
            contents=wrap_in_tag(soup, pile, "div"),
        )
        container.append(document_element)

    return lines


def _parse_page_footer(
    soup: BeautifulSoup,
    container: Tag,
    lines: TextSegments,
) -> TextSegments:
    return _parse_document_element(
        soup,
        container,
        lines,
        "page_footer",
    )


def _parse_table_of_contents(
    soup: BeautifulSoup,
    container: Tag,
    lines: TextSegments,
) -> TextSegments:
    return _parse_document_element(
        soup,
        container,
        lines,
        "table_of_contents",
    )


def parse_document_elements(
    soup: BeautifulSoup,
    container: Tag,
    lines: TextSegments,
) -> TextSegments:
    """Parse document elements."""
    while lines and is_document_element(lines[0].contents):

        # Page footer
        lines = _parse_page_footer(soup, container, lines)

        # Table of contents
        lines = _parse_table_of_contents(soup, container, lines)

    return lines
