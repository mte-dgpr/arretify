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
from typing import List, Iterator

from bs4 import BeautifulSoup

from arretify.types import SectionType, PageElementOrString
from arretify.html_schemas import (
    HEADER_SCHEMA,
    MAIN_SCHEMA,
    APPENDIX_SCHEMA,
)
from arretify.utils.html_create import make_data_tag
from arretify.utils.functional import chain_functions, iter_func_to_list
from arretify.utils.split_merge import (
    split_before_match,
)
from .header import parse_header, render_header
from .titles_detection import TITLE_NODE, parse_title_info
from .content import parse_content, render_content
from .core import (
    Node,
    NodeOrText,
    make_probe_from_pattern_proxy,
    pick_text_span_node,
    is_node,
    get_string,
)
from .basic_elements import parse_images
from .document_elements import (
    parse_page_footers,
    parse_tables_of_contents,
    initialize_document_structure,
)


_is_title = make_probe_from_pattern_proxy(
    TITLE_NODE.pattern,
)
_is_title_line = pick_text_span_node(_is_title)


def _is_appendix(elements: List[NodeOrText], index: int) -> bool:
    element = elements[index]
    assert is_node(element)
    if _is_title_line(elements, index):
        # Parse title info
        title_info = parse_title_info(get_string(element))
        new_section_type = title_info.section_type

        # Appendix is considered as a different part of the document
        if new_section_type == SectionType.ANNEXE:
            return True
    return False


_is_appendix_text_segment = pick_text_span_node(_is_appendix)


@iter_func_to_list
def parse_arrete(elements: List[NodeOrText]) -> Iterator[NodeOrText]:
    # Add basic document elements
    elements = chain_functions(
        elements,
        # Image strings can be very long, and table of contents pattern look
        # at the end of the sentence.
        # So, we make sure we parse images before table of contents.
        [initialize_document_structure, parse_images, parse_page_footers, parse_tables_of_contents],
    )

    # Header
    pile, elements = split_before_match(elements, _is_title_line)
    yield Node(
        type="header",
        children=parse_header(pile),
    )

    # Main content
    pile, elements = split_before_match(elements, _is_appendix_text_segment)
    yield Node(
        type="main",
        children=parse_content(pile),
    )

    # Appendix
    if elements:
        yield Node(
            type="appendix",
            children=parse_content(elements),
        )


@iter_func_to_list
def render_arrete(soup: BeautifulSoup, elements: List[NodeOrText]) -> Iterator[PageElementOrString]:
    body = soup.body
    assert body

    for element in elements:
        if is_node(element, type_in=["header"]):
            yield make_data_tag(soup, HEADER_SCHEMA, contents=render_header(soup, element.children))
        elif is_node(element, type_in=["main"]):
            yield make_data_tag(soup, MAIN_SCHEMA, contents=render_content(soup, element.children))
        elif is_node(element, type_in=["appendix"]):
            yield make_data_tag(
                soup, APPENDIX_SCHEMA, contents=render_content(soup, element.children)
            )
