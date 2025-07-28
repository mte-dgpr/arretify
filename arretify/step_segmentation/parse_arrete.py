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
from typing import List, cast

from arretify.types import DocumentContext, SectionType, TextSegment
from arretify.html_schemas import (
    HEADER_SCHEMA,
    MAIN_SCHEMA,
    APPENDIX_SCHEMA,
)
from arretify.utils.html_create import make_data_tag
from arretify.utils.functional import chain_functions
from arretify.utils.split_merge import (
    split_before_match,
)
from .header import parse_header, render_header
from .titles_detection import TITLE_NODE, parse_title_info
from .content import parse_content, render_content
from .core import (
    NodeOrText,
    make_probe_from_regex_tree,
    pick_text_segment,
)
from .basic_elements import parse_images
from .document_elements import parse_page_footers, parse_tables_of_contents, add_page_separators


_is_title = make_probe_from_regex_tree(
    TITLE_NODE,
)
_is_title_text_segment = pick_text_segment(_is_title)


def _is_appendix(elements: List[NodeOrText], index: int) -> bool:
    element = elements[index]
    assert isinstance(element, TextSegment)
    if _is_title(elements, index):
        # Parse title info
        title_info = parse_title_info(element.contents)
        new_section_type = title_info.section_type

        # Appendix is considered as a different part of the document
        if new_section_type == SectionType.ANNEXE:
            return True
    return False


_is_appendix_text_segment = pick_text_segment(_is_appendix)


def parse_arrete(document_context: DocumentContext) -> DocumentContext:
    body = document_context.soup.body
    assert body

    lines = document_context.lines
    assert lines

    elements: List[NodeOrText] = cast(List[NodeOrText], lines)
    # Add basic document elements
    elements = chain_functions(
        elements,
        # Image strings can be very long, and table of contents pattern look
        # at the end of the sentence.
        # So, we make sure we parse images before table of contents.
        [add_page_separators, parse_images, parse_page_footers, parse_tables_of_contents],
    )

    # Header
    pile, elements = split_before_match(elements, _is_title_text_segment)
    header = make_data_tag(document_context.soup, HEADER_SCHEMA)
    body.append(header)
    rendered_header = render_header(document_context.soup, list(parse_header(pile)))
    header.extend(list(rendered_header.children))

    # Main content
    pile, elements = split_before_match(elements, _is_appendix_text_segment)
    main_content = make_data_tag(document_context.soup, MAIN_SCHEMA)
    body.append(main_content)
    rendered_content = render_content(document_context.soup, list(parse_content(pile)))
    main_content.extend(list(rendered_content.children))

    # Appendix
    if elements:
        appendix = make_data_tag(document_context.soup, APPENDIX_SCHEMA)
        body.append(appendix)
        rendered_appendix = render_content(document_context.soup, list(parse_content(elements)))
        appendix.extend(list(rendered_appendix.children))

    return document_context
