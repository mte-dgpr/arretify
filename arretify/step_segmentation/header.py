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
from typing import List, Dict, Literal

from bs4 import Tag, BeautifulSoup

from arretify.utils.functional import flat_map_string
from arretify.parsing_utils.dates import DATE_NODE, render_date_regex_tree_match
from arretify.regex_utils import PatternProxy, join_with_or
from arretify.utils.html import wrap_in_tag, make_data_tag, make_new_tag
from arretify.types import TextSegments, TextSegment, PageElementOrString
from arretify.parsing_utils.patterns import join_split_pile_with_pattern
from arretify.html_schemas import (
    EMBLEM_SCHEMA,
    ENTITY_SCHEMA,
    IDENTIFICATION_SCHEMA,
    ARRETE_TITLE_SCHEMA,
    HONORARY_SCHEMA,
    VISA_SCHEMA,
    MOTIF_SCHEMA,
    SUPPLEMENTARY_MOTIF_INFORMATION_SCHEMA,
)
from arretify.regex_utils import (
    map_regex_tree_match,
    split_string_with_regex_tree,
    PatternProxy,
    join_with_or,
)
from .core import (
    NodeFlow,
    Node,
    flat_map_node_flow,
    split_text_segments,
    make_while_splitter,
    map_splitted_text_segments,
    split_before_match,
    is_node,
    assert_single_text_segments,
    make_single_line_splitter,
    assert_single_text_segment,
)
from .document_elements import (
    parse_parse_page_footer,
    parse_table_of_contents,
    render_page_footer,
    render_table_of_contents,
)
from .basic_elements import parse_images, parse_lists, render_image, render_list
from .document_elements import IS_NOT_TABLE_OF_CONTENTS_PAGING_PATTERN_S
from .titles_detection import is_title


EMBLEMS_LIST = [
    r"liberte",
    r"egalite",
    r"fraternite",
    r"republique fran[cç]aise",
]

EMBLEM_PATTERN = PatternProxy(rf"^{join_with_or(EMBLEMS_LIST)}")
"""Detect all sentences starting with French emblems."""

ENTITIES_LIST = [
    r"gouvernement",
    r"ministeres?",
    r"prefecture",
    r"sous-prefecture",
    r"secretariat",
    r"sg",
    r"prefete?",
    r"academie",
    r"rectorat",
    r"direction",
    r"drire",
    r"deal",
    r"dreal",
    r"service",
    r"section",
    r"pole",
    r"bureau",
    r"mission",
    r"unite",
    r"installations? classees? pour la protection de l'environnement",
    r"affaires? suivies? par",
    r"cheff?e? de (bureau|mission)",
]

ENTITY_PATTERN = PatternProxy(rf"^{join_with_or(ENTITIES_LIST)}")
"""Detect all services taking the arretes."""

IDENTIFICATIONS_LIST = [
    r"réf",
    r"n°",
    r"n/ref",
    r"nor",
]

IDENTIFICATION_PATTERN = PatternProxy(rf"^{join_with_or(IDENTIFICATIONS_LIST)}")
"""Detect all references."""

ARRETE_TITLE_PATTERN = PatternProxy(
    r"^\W*(arrete(nt)?)" + IS_NOT_TABLE_OF_CONTENTS_PAGING_PATTERN_S
)
"""Detect if the sentence starts with "arrete" without ending points for table of contents."""

HONORARIES_LIST = [
    r"l[ea] presidente?",
    r"l[ea] ministre",
    r"la prefecture",
    r"l[ea] prefete?",
    r"commissaire",
    r"l[ea] rect(eur|rice)",
    r"recteur",
    r"l[ea] direct(eur|rice)",
    r"commandeur",
    r"chevalier",
    r"officier",
    r"chancelier",
]

HONORARY_PATTERN = PatternProxy(rf"^\W*({join_with_or(HONORARIES_LIST)})")
"""Detect all honorary titles."""

HONORARY_SPLIT_PATTERN = PatternProxy(join_with_or(HONORARIES_LIST))
"""Pattern to split honorary titles into separate elements."""

VISA_PATTERN = PatternProxy(r"^\W*vu(\s*:\s*|\b)(?P<contents>.*)")
"""Detect if the sentence starts with "vu"."""

MOTIF_PATTERN = PatternProxy(r"^\W*considerant(\s*:\s*|\b)(?P<contents>.*)")
"""Detect if the sentence starts with "considerant"."""

SUPPLEMENTARY_MOTIF_INFORMATIONS_LIST = [
    r"le (demandeur|petitionnaire) entendu",
    r"l'exploitant entendu",
    r"apres communication",
    r"sur (?:la )?proposition",
]

SUPPLEMENTARY_MOTIF_INFORMATION_PATTERN = PatternProxy(
    rf"^\W*({join_with_or(SUPPLEMENTARY_MOTIF_INFORMATIONS_LIST)})"
)
"""Detect all other information that can be part of the motifs."""

HEADER_ELEMENTS_PATTERNS: Dict[str, PatternProxy] = {
    "emblem": EMBLEM_PATTERN,
    "entity": ENTITY_PATTERN,
    "identification": IDENTIFICATION_PATTERN,
    "arrete_title": ARRETE_TITLE_PATTERN,
    "honorary": HONORARY_PATTERN,
    "visa": VISA_PATTERN,
    "motif": MOTIF_PATTERN,
    "supplementary_motif_info": SUPPLEMENTARY_MOTIF_INFORMATION_PATTERN,
}


HEADER_ELEMENTS_SCHEMAS = dict(
    emblem=EMBLEM_SCHEMA,
    entity=ENTITY_SCHEMA,
    identification=IDENTIFICATION_SCHEMA,
    arrete_title=ARRETE_TITLE_SCHEMA,
    honorary=HONORARY_SCHEMA,
    visa=VISA_SCHEMA,
    motif=MOTIF_SCHEMA,
    supplementary_motif_info=SUPPLEMENTARY_MOTIF_INFORMATION_SCHEMA,
)


def _is_nothing_else_than(name: str, t: TextSegment) -> bool:
    return not any(
        bool(HEADER_ELEMENTS_PATTERNS[other_name].match(t.contents))
        for other_name in HEADER_ELEMENTS_PATTERNS
        if other_name != name
    )


def parse_header(
    lines: TextSegments,
) -> NodeFlow:
    node_flow: NodeFlow = [lines]
    node_flow = flat_map_node_flow(
        node_flow,
        parse_table_of_contents,
    )
    node_flow = flat_map_node_flow(
        node_flow,
        parse_images,
    )
    node_flow = flat_map_node_flow(
        node_flow,
        parse_parse_page_footer,
    )
    node_flow = flat_map_node_flow(
        node_flow,
        parse_emblem_element,
    )
    node_flow = flat_map_node_flow(
        node_flow,
        parse_entity_element,
    )
    node_flow = flat_map_node_flow(
        node_flow,
        parse_identification_element,
    )
    node_flow = flat_map_node_flow(
        node_flow,
        parse_arrete_title_element,
    )
    node_flow = flat_map_node_flow(
        node_flow,
        parse_honorary_element,
    )
    node_flow = flat_map_node_flow(
        node_flow,
        parse_supplementary_motif_info_element,
    )
    node_flow = flat_map_node_flow(
        node_flow,
        parse_lists,
    )
    node_flow = parse_visa_and_motif_elements(node_flow)
    return node_flow


def parse_header_DEPRECATED(
    soup: BeautifulSoup,
    header: Tag,
    lines: TextSegments,
) -> TextSegments:
    pile: TextSegments = []
    while lines and not is_title(lines[0].contents):
        pile.append(lines.pop(0))
    parsed_content = list(parse_header(pile))
    rendered_content = render_header(soup, parsed_content)
    header.extend(list(rendered_content.children))
    return lines


def _parse_header_element(
    lines: TextSegments,
    node_pattern: PatternProxy,
    node_type: str,
) -> NodeFlow:
    """
    Generic function to parse header elements.
    It uses a simple regex pattern to detect the element start, 
    and then gathers all following lines while the pattern still matches.
    """
    lines = list(lines)
    return map_splitted_text_segments(
        split_text_segments(
            lines,
            make_while_splitter(
                lambda t: bool(node_pattern.match(t.contents)),
            ),
        ),
        lambda text_segments: Node(
            type=node_type,
            children=[text_segments],
        ),
    )


def _parse_header_element_fuzzy(
    lines: TextSegments,
    node_pattern: PatternProxy,
    node_type: str,
) -> NodeFlow:
    """
    Generic function to parse header elements with a fuzzy match.
    It uses a regex pattern to find the start of the element,
    and then gathers all following lines that do not match another element.
    """
    lines = list(lines)
    return map_splitted_text_segments(
        split_text_segments(
            lines,
            make_while_splitter(
                lambda t: _is_nothing_else_than(node_type, t),
                start_is_matching=lambda t: bool(node_pattern.match(t.contents)),
            ),
        ),
        lambda text_segments: Node(
            type=node_type,
            children=[text_segments],
        ),
    )


def parse_emblem_element(
    lines: TextSegments,
) -> NodeFlow:
    return _parse_header_element(lines, EMBLEM_PATTERN, "emblem")


def parse_entity_element(
    lines: TextSegments,
) -> NodeFlow:
    return _parse_header_element_fuzzy(
        lines,
        ENTITY_PATTERN,
        "entity",
    )


def parse_identification_element(
    lines: TextSegments,
) -> NodeFlow:
    return _parse_header_element(lines, IDENTIFICATION_PATTERN, "identification")


def parse_arrete_title_element(
    lines: TextSegments,
) -> NodeFlow:
    return _parse_header_element_fuzzy(
        lines,
        ARRETE_TITLE_PATTERN,
        "arrete_title",
    )


def parse_honorary_element(
    lines: TextSegments,
) -> NodeFlow:
    return _parse_header_element(lines, HONORARY_PATTERN, "honorary")


def parse_supplementary_motif_info_element(
    lines: TextSegments,
) -> NodeFlow:
    return _parse_header_element_fuzzy(
        lines,
        SUPPLEMENTARY_MOTIF_INFORMATION_PATTERN,
        "supplementary_motif_info",
    )


def parse_visa_and_motif_elements(
    node_flow: NodeFlow,
) -> NodeFlow:
    node_flow = list(_parse_visa_and_motif_elements_pass1(node_flow, "visa", VISA_PATTERN))
    node_flow = list(_parse_visa_and_motif_elements_pass1(node_flow, "motif", MOTIF_PATTERN))
    node_flow = list(
        _parse_visa_and_motif_elements_pass2(
            node_flow,
            node_type="visa",
            node_pattern=VISA_PATTERN,
        )
    )
    node_flow = list(
        _parse_visa_and_motif_elements_pass3(
            node_flow,
            node_type="visa",
        )
    )
    node_flow = list(
        _parse_visa_and_motif_elements_pass2(
            node_flow,
            node_type="motif",
            node_pattern=MOTIF_PATTERN,
        )
    )
    node_flow = list(
        _parse_visa_and_motif_elements_pass3(
            node_flow,
            node_type="motif",
        )
    )
    return node_flow


def _parse_visa_and_motif_elements_pass1(
    node_flow: NodeFlow,
    node_type: Literal["visa", "motif"],
    node_pattern: PatternProxy,
) -> NodeFlow:
    """
    Pass 1 of parsing visa and motif elements.
    This pass splits the node flow into segments based on the node pattern.
    It creates nodes of type 'visa' or 'motif' for each segment that matches 
    the pattern.
    """
    node_flow = list(node_flow)
    node_flow = flat_map_node_flow(
        node_flow,
        lambda lines: map_splitted_text_segments(
            split_text_segments(
                lines,
                make_single_line_splitter(lambda t: bool(node_pattern.match(t.contents))),
            ),
            lambda text_segments: Node(
                type=node_type,
                children=[text_segments],
            ),
        ),
    )

    # Visas or motifs that are in form :
    # - Vu blabla
    # - Vu bloblo
    # Should have been parsed into list nodes.
    # Therefore, we must convert list nodes that contain visas and motifs
    # into visa or motif nodes.
    for node_or_text_segments in node_flow:
        if is_node(node_or_text_segments, type_in=["list"]):
            lines = assert_single_text_segments(node_or_text_segments)
            if bool(node_pattern.match(lines[0].contents)):
                for line in lines:
                    yield Node(
                        type=node_type,
                        children=[[line]],
                    )
            else:
                yield node_or_text_segments
        else:
            yield node_or_text_segments


def _parse_visa_and_motif_elements_pass2(
    node_flow: NodeFlow,
    node_type: Literal["visa", "motif"],
    node_pattern: PatternProxy,
) -> NodeFlow:
    """
    Pass 2 of parsing visa and motif elements.
    This pass processes the node flow to find the first node of type 
    'visa' or 'motif'. Once found, it decides between one of the several
    types of variants for formatting the visas or motifs, and normalizes
    the node flow accordingly.
    """
    next_node: Node | TextSegments
    node_flow = list(node_flow)

    # Skip nodes until we find the first node of type 'visa' or 'motif'.
    while node_flow and not is_node(node_flow[0], type_in=[node_type]):
        yield node_flow.pop(0)
    if not node_flow:
        return
    first_node = node_flow.pop(0)
    assert is_node(first_node, type_in=[node_type])

    
    first_node_match = node_pattern.match(assert_single_text_segment(first_node).contents)
    # 1. Variant "simple" : 
    #   Vu que blabla
    #   Vu que bloblo
    if first_node_match and first_node_match.group("contents"):
        yield first_node

    # 2. Variant "explicit list" : 
    #   Vu :
    #   - blabla
    #   - bloblo
    elif node_flow and is_node(node_flow[0], type_in=["list"]):
        # Add the "Vu :" to the header
        yield from first_node.children
        while node_flow:
            next_node = node_flow[0]
            if is_node(next_node, type_in=["page_footer"]) or isinstance(next_node, list):
                yield node_flow.pop(0)

            elif is_node(next_node, type_in=["list"]):
                node_flow.pop(0)
                for line in assert_single_text_segments(next_node):
                    yield Node(
                        type=node_type,
                        children=[[line]],
                    )
            else:
                break

    # 3. Variant "implicit list" (no explicit bullets) : 
    #   Vu :
    #   blabla
    #   bloblo
    else:
        # Add the "Vu :" to the header
        yield from first_node.children
        while node_flow:
            next_node = node_flow[0]
            if is_node(next_node, type_in=["page_footer", "list"]):
                yield node_flow.pop(0)

            elif isinstance(next_node, list):
                node_flow.pop(0)
                for line in next_node:
                    yield Node(
                        type=node_type,
                        children=[[line]],
                    )
            else:
                break

    yield from node_flow


def _parse_visa_and_motif_elements_pass3(
    node_flow: NodeFlow,
    node_type: Literal["visa", "motif"],
) -> NodeFlow:
    """
    Pass 3 of parsing visa and motif elements.
    Merges the nodes of type 'visa' or 'motif' with the next node
    if the next node is a list. This is done to ensure that the
    visa or motif node contains all its children.
    """
    node_flow = list(node_flow)
    while node_flow:
        node_or_text_segments = node_flow.pop(0)
        if is_node(node_or_text_segments, type_in=[node_type]):
            if node_flow and is_node(node_flow[0], type_in=["list"]):
                node_or_text_segments.children.append(node_flow.pop(0))
            yield node_or_text_segments
        else:
            yield node_or_text_segments


def render_header(
    soup: BeautifulSoup,
    node_flow: NodeFlow,
) -> Tag:
    content = soup.new_tag("div")
    for node in node_flow:
        if is_node(node, type_in=["arrete_title"]):
            content.append(rendre_arrete_title(soup, node))
        elif is_node(node, type_in=["visa", "motif"]):
            content.append(render_visa_motif(soup, node))
        elif is_node(node, type_in=["honorary"]):
            content.append(render_honorary(soup, node))
        elif is_node(node, type_in=["supplementary_motif_info"]):
            content.append(render_supplementary_motif_info_element(soup, node))
        elif is_node(node, type_in=list(HEADER_ELEMENTS_SCHEMAS.keys())):
            content.append(render_header_elements(soup, node))
        elif is_node(node, type_in=["table_of_contents"]):
            content.append(render_table_of_contents(soup, node))
        elif is_node(node, type_in=["page_footer"]):
            content.append(render_page_footer(soup, node))
        elif is_node(node, type_in=["image"]):
            content.extend(render_image(soup, node))
        elif is_node(node, type_in=["list"]):
            content.extend(render_list(soup, node))

        elif is_node(node):
            raise ValueError(f"Unexpected node {node.type} in content")

        elif isinstance(node, list):
            content.extend(wrap_in_tag(soup, [t.contents for t in node], "div"))
    return content


def render_header_elements(
    soup: BeautifulSoup,
    node: Node,
) -> Tag:
    lines = assert_single_text_segments(node)
    elements: List[PageElementOrString]
    elements = join_split_pile_with_pattern(
        [t.contents for t in lines], HEADER_ELEMENTS_PATTERNS[node.type]
    )
    return make_data_tag(
        soup,
        HEADER_ELEMENTS_SCHEMAS[node.type],
        contents=wrap_in_tag(soup, elements, "div"),
    )


def render_supplementary_motif_info_element(
    soup: BeautifulSoup,
    node: Node,
) -> Tag:
    lines = assert_single_text_segments(node)
    return make_data_tag(
        soup,
        SUPPLEMENTARY_MOTIF_INFORMATION_SCHEMA,
        contents=wrap_in_tag(soup, [t.contents for t in lines], "div"),
    )


def render_honorary(
    soup: BeautifulSoup,
    node: Node,
) -> Tag:
    lines = assert_single_text_segments(node)
    elements = join_split_pile_with_pattern([t.contents for t in lines], HONORARY_SPLIT_PATTERN)
    return make_data_tag(
        soup,
        HONORARY_SCHEMA,
        contents=wrap_in_tag(soup, elements, "div"),
    )


def render_visa_motif(
    soup: BeautifulSoup,
    node: Node,
) -> Tag:
    assert is_node(node, type_in=["visa", "motif"])
    elements: List[PageElementOrString] = []
    for node_or_text_segments in node.children:
        if is_node(node_or_text_segments, type_in=["list"]):
            elements.extend(render_list(soup, node_or_text_segments))
        elif isinstance(node_or_text_segments, list):
            elements.extend(t.contents for t in node_or_text_segments)
        else:
            raise ValueError(f"Unexpected node {node_or_text_segments.type} in visa/motif contents")
    return make_data_tag(
        soup,
        HEADER_ELEMENTS_SCHEMAS[node.type],
        contents=elements,
    )


def rendre_arrete_title(
    soup: BeautifulSoup,
    node: Node,
) -> Tag:
    lines = assert_single_text_segments(node)
    elements: List[PageElementOrString] = join_split_pile_with_pattern(
        [t.contents for t in lines], ARRETE_TITLE_PATTERN
    )
    elements = list(
        flat_map_string(
            elements,
            lambda string: map_regex_tree_match(
                split_string_with_regex_tree(DATE_NODE, string),
                lambda date_match: render_date_regex_tree_match(soup, date_match),
                allowed_group_names=["__date"],
            ),
        )
    )
    return make_data_tag(
        soup,
        ARRETE_TITLE_SCHEMA,
        contents=[make_new_tag(soup, "h1", elements)],
    )
