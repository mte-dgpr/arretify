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
from typing import List, cast, Iterator

from bs4 import BeautifulSoup, Tag

from arretify.types import TextSegment
from arretify.html_schemas import (
    PAGE_FOOTER_SCHEMA,
    TABLE_OF_CONTENTS_SCHEMA,
    PAGE_SEPARATOR_SCHEMA,
)
from arretify.regex_utils import (
    PatternProxy,
    join_with_or,
)
from arretify.utils.html import (
    PageElementOrString,
    make_data_tag,
    wrap_in_tag,
)
from arretify.utils.functional import iter_func_to_list

from .core import (
    Node,
    Split,
    is_node,
    assert_single_text_segment,
    split_before_match,
    NodeOrText,
    split_text_segments,
    map_splitted_text_segments,
    make_while_splitter,
)


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


def parse_tables_of_contents(
    elements: List[NodeOrText],
) -> List[NodeOrText]:
    return map_splitted_text_segments(
        split_text_segments(elements, _table_of_contents_splitter),
        lambda pile: Node(type="table_of_contents", children=pile),
    )


def _table_of_contents_splitter(input_list: List[NodeOrText]) -> Split[List[NodeOrText]] | None:
    pile: List[NodeOrText] = []
    before, after = split_before_match(input_list, lambda t: is_table_of_contents(t.contents))
    while after:
        # Instead of checking just the first line, we check the next few lines.
        # This allows to deal with case when TOC contains lines that are not
        # easily recognizable as TOC, e.g.:
        #
        #   Title 1
        #       article 1.1 ..... page 1
        #       article 1.2 ..... page 2
        #   Title 2
        #       article 2.1 ..... page 3
        #
        # Aditionnally, this takes in nodes such as `page_separator` that might appear
        # between text segments.
        if any(
            isinstance(after[i], TextSegment)
            and is_table_of_contents(cast(TextSegment, after[i]).contents)
            for i in range(min(3, len(after)))
        ):
            pile.append(after.pop(0))
        elif is_node(after[0], type_in=["page_separator"]):
            pile.append(after.pop(0))
        else:
            break
    if pile:
        return (before, pile, after)
    else:
        return None


def parse_page_footers(
    elements: List[NodeOrText],
) -> List[NodeOrText]:
    return map_splitted_text_segments(
        split_text_segments(
            elements,
            make_while_splitter(lambda t: is_page_footer(t.contents)),
        ),
        lambda pile: Node(type="page_footer", children=pile),
    )


@iter_func_to_list
def add_page_separators(
    elements: List[NodeOrText],
) -> Iterator[NodeOrText]:
    current_page = -1
    while elements:
        page_lines, elements = split_before_match(
            elements,
            lambda element: isinstance(element, TextSegment) and element.start[0] != current_page,
        )
        if page_lines:
            yield from page_lines
        if elements:
            assert isinstance(elements[0], TextSegment)
            current_page = elements[0].start[0]
            yield Node(
                type="page_separator",
                data=dict(page_index=current_page),
                children=[],
            )


def render_table_of_contents(
    soup: BeautifulSoup,
    node: Node,
) -> Tag:
    page_elements: List[PageElementOrString] = []
    for element in node.children:
        if isinstance(element, TextSegment):
            page_elements.append(element.contents)
        elif is_node(element, type_in=["page_separator"]):
            page_elements.append(render_page_separator(soup, element))
        else:
            raise ValueError(f"Unexpected element type in table of contents: {element.type}")
    return make_data_tag(
        soup,
        TABLE_OF_CONTENTS_SCHEMA,
        contents=wrap_in_tag(soup, page_elements, "div"),
    )


def render_page_footer(
    soup: BeautifulSoup,
    node: Node,
) -> Tag:
    text_segment = assert_single_text_segment(node)
    return make_data_tag(
        soup,
        PAGE_FOOTER_SCHEMA,
        contents=wrap_in_tag(soup, [text_segment.contents], "div"),
    )


def render_page_separator(
    soup: BeautifulSoup,
    node: Node,
) -> Tag:
    return make_data_tag(
        soup,
        PAGE_SEPARATOR_SCHEMA,
        data=dict(page_index=node.data["page_index"]),
    )
