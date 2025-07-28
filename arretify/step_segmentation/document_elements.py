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
from typing import List, Iterator, cast

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
)
from arretify.utils.html_create import make_data_tag, wrap_in_tag
from arretify.utils.functional import iter_func_to_list
from arretify.utils.split_merge import (
    split_before_match,
    split_elements,
    map_splitted_elements,
)
from .core import (
    Node,
    NodeOrText,
    is_node,
    assert_single_text_segment,
    make_while_splitter_for_text_segments,
    make_probe_from_pattern_proxy,
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

TABLE_OF_CONTENTS_LIST = [
    r"sommaire",
    r"table des matieres",
    r"liste des (chapitres|articles)",
    rf".*?\s+{TABLE_OF_CONTENTS_PAGING_PATTERN_S}$",
]

TABLE_OF_CONTENTS_PATTERN = PatternProxy(rf"^{join_with_or(TABLE_OF_CONTENTS_LIST)}")
"""Detect all table of contents starting sentences."""


_is_table_of_contents = make_probe_from_pattern_proxy(TABLE_OF_CONTENTS_PATTERN)
_is_page_footer = make_probe_from_pattern_proxy(PAGE_FOOTER_PATTERN)


def parse_tables_of_contents(
    elements: List[NodeOrText],
) -> List[NodeOrText]:
    return map_splitted_elements(
        split_elements(
            elements,
            make_while_splitter_for_text_segments(
                _is_table_of_contents,
                _table_of_contents_while_condition,
            ),
        ),
        lambda pile: Node(type="table_of_contents", children=pile),
    )


def _table_of_contents_while_condition(elements: List[NodeOrText], index: int) -> bool:
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
    next_elements = elements[index : index + 3]
    if any(
        isinstance(next_elements[i], TextSegment) and _is_table_of_contents(next_elements, i)
        for i in range(len(next_elements))
    ):
        return True
    return False


def parse_page_footers(
    elements: List[NodeOrText],
) -> List[NodeOrText]:
    return map_splitted_elements(
        split_elements(
            elements,
            make_while_splitter_for_text_segments(_is_page_footer, _is_page_footer),
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
            lambda elements, index: isinstance(elements[index], TextSegment)
            and cast(TextSegment, elements[index]).start[0] != current_page,
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
