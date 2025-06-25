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

from bs4 import Tag, BeautifulSoup

from arretify.html_schemas import PAGE_FOOTER_SCHEMA, TABLE_OF_CONTENTS_SCHEMA
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
from arretify.types import PageElementOrString
from arretify.utils.markdown_parsing import is_image

from .core import NodeFlow, Node, assert_single_text_segments, flat_map_node_flow, is_node


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


def is_table_of_contents(line: str) -> bool:
    return bool(TABLE_OF_CONTENTS_PATTERN.match(line))


def is_page_footer(line: str) -> bool:
    return bool(PAGE_FOOTER_PATTERN.match(line))


def is_document_element_DEPRECATED(line: str) -> bool:
    """Detect if the line is a document element."""
    # Image strings can be very long, and table of contents pattern look at the end of the
    # sentence. So, we make sure we do not have an image in the line before checking for other
    # document elements
    return not is_image(line) and (is_table_of_contents(line) or is_page_footer(line))


def parse_table_of_contents(
    lines: TextSegments,
) -> NodeFlow:
    lines = list(lines)
    pile: TextSegments = []
    while lines:
        while lines and not is_table_of_contents(lines[0].contents):
            pile.append(lines.pop(0))
        if pile:
            yield pile
            pile = []

        while lines and any(is_table_of_contents(lines[i].contents) for i in range(3)):
            pile.append(lines.pop(0))
        if pile:
            yield Node(type="table_of_contents", children=[pile])
            pile = []


def parse_parse_page_footer(
    lines: TextSegments,
) -> NodeFlow:
    lines = list(lines)
    pile: TextSegments = []

    while lines:
        while lines and not is_page_footer(lines[0].contents):
            pile.append(lines.pop(0))
        if pile:
            yield pile
            pile = []

        while lines and is_page_footer(lines[0].contents):
            pile.append(lines.pop(0))
        if pile:
            yield Node(type="page_footer", children=[pile])
            pile = []


def render_table_of_contents(
    soup: BeautifulSoup,
    node: Node,
) -> PageElementOrString:
    text_segments = assert_single_text_segments(node)
    return make_data_tag(
        soup,
        TABLE_OF_CONTENTS_SCHEMA,
        contents=wrap_in_tag(soup, [t.contents for t in text_segments], "div"),
    )


def render_page_footer(
    soup: BeautifulSoup,
    node: Node,
) -> PageElementOrString:
    text_segments = assert_single_text_segments(node)
    return make_data_tag(
        soup,
        PAGE_FOOTER_SCHEMA,
        contents=wrap_in_tag(soup, [t.contents for t in text_segments], "div"),
    )
