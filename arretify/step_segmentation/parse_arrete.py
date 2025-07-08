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
from typing import List, Tuple

from arretify.types import DocumentContext, SectionType, TextSegments
from arretify.html_schemas import (
    HEADER_SCHEMA,
    MAIN_SCHEMA,
    APPENDIX_SCHEMA,
)
from arretify.utils.html import make_data_tag
from .header import parse_header, render_header
from .titles_detection import is_title, parse_title_info
from .content import parse_content, render_content
from .core import (
    split_before_match,
    chain_flat_map_node_flow,
    NodeFlow,
    NodeList,
    is_node,
    Node,
    Probe,
)
from .basic_elements import parse_images
from .document_elements import parse_page_footer, parse_table_of_contents


def parse_arrete(document_context: DocumentContext) -> DocumentContext:
    body = document_context.soup.body
    assert body

    lines = document_context.lines
    assert lines

    node_flow: NodeFlow = [lines]
    # Add basic document elements
    node_flow = chain_flat_map_node_flow(
        node_flow,
        # Image strings can be very long, and table of contents pattern look
        # at the end of the sentence.
        # So, we make sure we parse images before table of contents.
        [parse_images, parse_page_footer, parse_table_of_contents],
    )

    # Header
    node_flow_pile, node_flow = _split_node_flow(node_flow, lambda t: is_title(t.contents))
    header = make_data_tag(document_context.soup, HEADER_SCHEMA)
    body.append(header)
    rendered_header = render_header(document_context.soup, list(parse_header(node_flow_pile)))
    header.extend(list(rendered_header.children))

    # Main content
    node_flow_pile, node_flow = _split_node_flow(node_flow, lambda t: _is_appendix(t.contents))
    main_content = make_data_tag(document_context.soup, MAIN_SCHEMA)
    body.append(main_content)
    rendered_content = render_content(document_context.soup, list(parse_content(node_flow_pile)))
    main_content.extend(list(rendered_content.children))

    # Appendix
    if node_flow:
        appendix = make_data_tag(document_context.soup, APPENDIX_SCHEMA)
        body.append(appendix)
        rendered_appendix = render_content(document_context.soup, list(parse_content(node_flow)))
        appendix.extend(list(rendered_appendix.children))

    return document_context


def _is_appendix(line: str) -> bool:
    if is_title(line):
        # Parse title info
        title_info = parse_title_info(line)
        new_section_type = title_info.section_type

        # Appendix is considered as a different part of the document
        if new_section_type == SectionType.ANNEXE:
            return True
    return False


def _split_node_flow(
    node_flow: NodeFlow,
    is_matching: Probe,
) -> Tuple[NodeFlow, NodeFlow]:
    node_list: NodeList = list(node_flow)
    node_flow_pile: List[Node | TextSegments] = []
    while node_list:
        if is_node(node_list[0]):
            node_flow_pile.append(node_list.pop(0))
        else:
            assert isinstance(node_list[0], list)
            before, after = split_before_match(node_list[0], is_matching)
            if after:
                node_list.pop(0)
                node_flow_pile.append(before)
                node_list.insert(0, after)
                break
            else:
                node_flow_pile.append(node_list.pop(0))
    return node_flow_pile, node_list
