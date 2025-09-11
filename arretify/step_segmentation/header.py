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
from typing import List, Dict, Literal, cast, Iterator

from bs4 import Tag, BeautifulSoup

from arretify.utils.functional import iter_func_to_list, chain_functions
from arretify.parsing_utils.dates import DATE_NODE, render_date_regex_tree_match
from arretify.utils.html_create import wrap_in_tag, make_data_tag, make_new_tag
from arretify.utils.html_split_merge import make_regex_tree_splitter
from arretify.types import PageElementOrString, DataElementSchema
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
    PatternProxy,
    join_with_or,
)
from arretify.utils.split_merge import (
    split_elements,
    SplitMatch,
    map_splitted_elements,
    Probe,
)
from .core import (
    Node,
    NodeOrText,
    is_node,
    make_recombine_interrupted_lines_splitter,
    make_while_splitter_for_text_span_nodes,
    make_single_line_splitter_for_text_span_nodes,
    group_text_span_nodes_splitter,
    make_probe_from_pattern_proxy,
    get_string,
    get_strings,
    TRANSPARENT_NODE_TYPES,
)
from .document_elements import (
    render_page_footer,
    render_page_separator,
    render_table_of_contents,
)
from .basic_elements import parse_lists, render_image, render_list, render_text_span


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
    r"cellule",
    r"installations? classees? pour la protection de l'environnement",
    r"etablissements? dangereux,? insalubres? ou incommodes?",
    r"(dossier|affaire)s? suivie?s? par",
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

ARRETE_TITLE_PATTERN = PatternProxy(r"^\W*(arrete(nt)?)")
"""Detect if the sentence starts with "arrete"."""

HONORARIES_LIST = [
    r"l[ea] presidente?",
    r"l[ea] ministre",
    r"la prefecture",
    r"l[ea] prefete?",
    r"commissaire",
    r"(l[ea] )?rect(eur|rice)",
    r"l[ea] direct(eur|rice)",
    r"commandeur",
    r"chevalier",
    r"officier",
    r"chancelier",
    r"l[ea]s? maires?",
    r"maitre",
    r"gentilhomme",
]

HONORARY_PATTERN = PatternProxy(rf"^\W*({join_with_or(HONORARIES_LIST)})")
"""Detect all honorary titles."""

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

HEADER_ELEMENTS_PATTERNS: Dict[str, PatternProxy] = dict(
    emblem=EMBLEM_PATTERN,
    entity=ENTITY_PATTERN,
    identification=IDENTIFICATION_PATTERN,
    arrete_title=ARRETE_TITLE_PATTERN,
    honorary=HONORARY_PATTERN,
    visa=VISA_PATTERN,
    motif=MOTIF_PATTERN,
    supplementary_motif_info=SUPPLEMENTARY_MOTIF_INFORMATION_PATTERN,
)

HEADER_ELEMENTS_RENDER_PATTERNS: Dict[str, PatternProxy | None] = dict(
    HEADER_ELEMENTS_PATTERNS,
    honorary=PatternProxy(join_with_or(HONORARIES_LIST)),
    supplementary_motif_info=None,
)

HEADER_ELEMENTS_SCHEMAS: Dict[str, DataElementSchema] = dict(
    emblem=EMBLEM_SCHEMA,
    entity=ENTITY_SCHEMA,
    identification=IDENTIFICATION_SCHEMA,
    arrete_title=ARRETE_TITLE_SCHEMA,
    honorary=HONORARY_SCHEMA,
    visa=VISA_SCHEMA,
    motif=MOTIF_SCHEMA,
    supplementary_motif_info=SUPPLEMENTARY_MOTIF_INFORMATION_SCHEMA,
)

HEADER_ELEMENTS_PROBES: Dict[str, Probe[NodeOrText]] = dict(
    emblem=make_probe_from_pattern_proxy(EMBLEM_PATTERN),
    identification=make_probe_from_pattern_proxy(IDENTIFICATION_PATTERN),
    honorary=make_probe_from_pattern_proxy(HONORARY_PATTERN),
    supplementary_motif_info=make_probe_from_pattern_proxy(SUPPLEMENTARY_MOTIF_INFORMATION_PATTERN),
)

HEADER_ELEMENTS_FUZZY_PROBES: Dict[str, Probe[NodeOrText]] = dict(
    entity=make_probe_from_pattern_proxy(ENTITY_PATTERN),
    arrete_title=make_probe_from_pattern_proxy(ARRETE_TITLE_PATTERN),
)

VISA_MOTIFS_PATTERNS: Dict[str, PatternProxy] = dict(
    visa=VISA_PATTERN,
    motif=MOTIF_PATTERN,
)

VISA_MOTIFS_PROBES: Dict[str, Probe[NodeOrText]] = dict(
    visa=make_probe_from_pattern_proxy(VISA_PATTERN),
    motif=make_probe_from_pattern_proxy(MOTIF_PATTERN),
)


def _is_nothing_else_than(name: str, element: NodeOrText) -> bool:
    return is_node(element, type_in=["text_span"]) and not any(
        bool(HEADER_ELEMENTS_PATTERNS[other_name].match(get_string(element)))
        for other_name in HEADER_ELEMENTS_PATTERNS
        if other_name != name
    )


def parse_header(
    elements: List[NodeOrText],
) -> List[NodeOrText]:
    elements = chain_functions(
        elements,
        [
            parse_emblem_element,
            parse_entity_element,
            parse_identification_element,
            parse_arrete_title_element,
            parse_honorary_element,
            parse_supplementary_motif_info_element,
            # We need to run list parsing here :
            # - after header elements, because some of them
            #       might contain lists which we don't want captured.
            #
            # - before visas and motifs, because they use list Nodes
            #       to build lists of visas / motifs
            parse_lists,
        ],
    )
    elements = parse_visa_and_motif_elements(elements)
    return elements


def _parse_header_element(
    elements: List[NodeOrText],
    node_type: str,
) -> List[NodeOrText]:
    """
    Generic function to parse header elements.
    It uses a simple regex pattern to detect the element start,
    and then gathers all following lines while the pattern still matches.
    """
    return map_splitted_elements(
        split_elements(
            elements,
            make_while_splitter_for_text_span_nodes(
                HEADER_ELEMENTS_PROBES[node_type], HEADER_ELEMENTS_PROBES[node_type]
            ),
        ),
        lambda children: Node(
            type=node_type,
            children=children,
        ),
    )


def _parse_header_element_fuzzy(
    elements: List[NodeOrText],
    node_type: str,
) -> List[NodeOrText]:
    """
    Generic function to parse header elements with a fuzzy match.
    It uses a regex pattern to find the start of the element,
    and then gathers all following lines that do not match another element.
    """
    return map_splitted_elements(
        split_elements(
            elements,
            make_while_splitter_for_text_span_nodes(
                HEADER_ELEMENTS_FUZZY_PROBES[node_type],
                lambda elements, index: _is_nothing_else_than(node_type, elements[index]),
            ),
        ),
        lambda children: Node(
            type=node_type,
            children=children,
        ),
    )


def parse_emblem_element(
    elements: List[NodeOrText],
) -> List[NodeOrText]:
    return _parse_header_element(elements, "emblem")


def parse_entity_element(
    elements: List[NodeOrText],
) -> List[NodeOrText]:
    return _parse_header_element_fuzzy(
        elements,
        "entity",
    )


def parse_identification_element(
    elements: List[NodeOrText],
) -> List[NodeOrText]:
    return _parse_header_element(elements, "identification")


def parse_arrete_title_element(
    elements: List[NodeOrText],
) -> List[NodeOrText]:
    return _parse_header_element_fuzzy(
        elements,
        "arrete_title",
    )


def parse_honorary_element(
    elements: List[NodeOrText],
) -> List[NodeOrText]:
    return _parse_header_element(elements, "honorary")


def parse_supplementary_motif_info_element(
    elements: List[NodeOrText],
) -> List[NodeOrText]:
    return _parse_header_element(
        elements,
        "supplementary_motif_info",
    )


def parse_visa_and_motif_elements(
    elements: List[NodeOrText],
) -> List[NodeOrText]:
    elements = _parse_visa_and_motif_elements_pass1(elements, "visa")
    elements = _parse_visa_and_motif_elements_pass1(elements, "motif")
    elements = _parse_visa_and_motif_elements_pass2(
        elements,
        node_type="visa",
    )
    elements = _parse_visa_and_motif_elements_pass3(
        elements,
        node_type="visa",
    )
    elements = _parse_visa_and_motif_elements_pass2(
        elements,
        node_type="motif",
    )
    elements = _parse_visa_and_motif_elements_pass3(
        elements,
        node_type="motif",
    )
    return elements


@iter_func_to_list
def _parse_visa_and_motif_elements_pass1(
    elements: List[NodeOrText],
    node_type: Literal["visa", "motif"],
) -> Iterator[NodeOrText]:
    """
    Pass 1 of parsing visa and motif elements.
    This pass splits the node flow into segments based on the node pattern.
    It creates nodes of type 'visa' or 'motif' for each segment that matches
    the pattern.
    """
    elements = map_splitted_elements(
        split_elements(
            elements,
            make_single_line_splitter_for_text_span_nodes(VISA_MOTIFS_PROBES[node_type]),
        ),
        lambda children: Node(
            type=node_type,
            children=children,
        ),
    )

    # Visas or motifs that are in form :
    # - Vu blabla
    # - Vu bloblo
    # Should have been parsed into list nodes.
    # Therefore, we must convert list nodes that contain visas and motifs
    # into visa or motif nodes.
    for element in elements:
        is_list_of_visas_or_motifs = False
        if is_node(element, type_in=["list"]):
            assert len(element.children) > 0, "List node should not be empty"
            is_list_of_visas_or_motifs = VISA_MOTIFS_PROBES[node_type](element.children, 0)

        if is_list_of_visas_or_motifs:
            assert is_node(element)
            for list_item_element in element.children:
                if is_node(list_item_element, type_in=["text_span"]):
                    yield Node(
                        type=node_type,
                        children=[list_item_element],
                    )
                else:
                    raise ValueError(f"Unexpected element {list_item_element}")
        else:
            yield element


@iter_func_to_list
def _parse_visa_and_motif_elements_pass2(
    elements: List[NodeOrText],
    node_type: Literal["visa", "motif"],
) -> Iterator[NodeOrText]:
    """
    Pass 2 of parsing visa and motif elements.
    This pass processes the node flow to find the first node of type
    'visa' or 'motif'. Once found, it decides between one of the several
    types of variants for formatting the visas or motifs, and normalizes
    the node flow accordingly.
    """
    element: NodeOrText
    elements = list(elements)

    # Skip nodes until we find the first node of type 'visa' or 'motif'.
    while elements and not is_node(elements[0], type_in=[node_type]):
        yield elements.pop(0)
    if not elements:
        return
    first_node = elements.pop(0)
    assert (
        is_node(first_node, type_in=[node_type])
        and len(first_node.children) > 0
        and is_node(first_node.children[0])
    )

    first_node_match = VISA_MOTIFS_PATTERNS[node_type].match(get_string(first_node))
    # 1. Variant "simple" :
    #   Vu que blabla
    #   Vu que bloblo
    if first_node_match and first_node_match.group("contents"):
        elements.insert(0, first_node)
        # Recombine interrupted lines, e.g.
        #   Vu que blabla
        #   <page_separator>
        #   continues on the next page.
        elements = map_splitted_elements(
            split_elements(elements, make_recombine_interrupted_lines_splitter(node_type)),
            _recombine_visa_motif_with_next_if_continuing_sentence,
        )
        yield from elements

    # 2. Variant "explicit list" :
    #   Vu :
    #   - blabla
    #   - bloblo
    elif elements and is_node(elements[0], type_in=["list"]):
        # Add the "Vu :" to the header
        yield from first_node.children
        while elements:
            element = elements[0]
            # We're a bit lenient here and accept a few unassigned_line nodes,
            # as random text sometimes interferes with the parsing.
            if is_node(element, type_in=TRANSPARENT_NODE_TYPES) or is_node(
                element, type_in=["text_span"]
            ):
                yield elements.pop(0)

            elif is_node(element, type_in=["list"]):
                elements.pop(0)
                for list_item_element in element.children:
                    if is_node(list_item_element, type_in=["text_span"]):
                        yield Node(
                            type=node_type,
                            children=[list_item_element],
                        )
                    else:
                        yield list_item_element
            else:
                break
        yield from elements

    # 3. Variant "implicit list" (no explicit bullets) :
    #   Vu :
    #   blabla
    #   bloblo
    else:
        # Add the "Vu :" to the header
        yield from first_node.children
        while elements:
            element = elements[0]

            # Lists will be handled in the next pass and appended to the visa or motif node
            # if applicable.
            if is_node(element, type_in=["list", *TRANSPARENT_NODE_TYPES]):
                yield elements.pop(0)

            elif is_node(element, type_in=["text_span"]):
                yield Node(
                    type=node_type,
                    children=[element],
                )
                elements.pop(0)
            else:
                break
        yield from elements


def _recombine_visa_motif_with_next_if_continuing_sentence(
    elements: List[NodeOrText],
) -> Node:
    assert len(elements) > 0 and is_node(elements[0], type_in=["visa", "motif"])
    elements[0].children.extend(elements[1:])
    return elements[0]


@iter_func_to_list
def _parse_visa_and_motif_elements_pass3(
    elements: List[NodeOrText],
    node_type: Literal["visa", "motif"],
) -> Iterator[NodeOrText]:
    """
    Pass 3 of parsing visa and motif elements.
    Merges the nodes of type 'visa' or 'motif' with the next node
    if the next node is a list. This is done to ensure that the
    visa or motif node contains all its children.
    """
    elements = list(elements)

    while elements:
        element = elements.pop(0)
        if is_node(element, type_in=[node_type]):
            transparent_nodes_pile: List[Node] = []
            while elements and is_node(elements[0], type_in=TRANSPARENT_NODE_TYPES):
                transparent_nodes_pile.append(elements[0])
                elements.pop(0)

            if elements and is_node(elements[0], type_in=["list"]):
                if transparent_nodes_pile:
                    element.children.extend(transparent_nodes_pile)
                element.children.append(elements.pop(0))
                yield element

            else:
                yield element
                yield from transparent_nodes_pile

        else:
            yield element


def render_header(
    soup: BeautifulSoup,
    elements: List[NodeOrText],
) -> Tag:
    content = soup.new_tag("div")
    for element in elements:
        if is_node(element, type_in=["arrete_title"]):
            content.append(rendre_arrete_title(soup, element))
        elif is_node(element, type_in=["visa", "motif"]):
            content.append(render_visa_motif(soup, element))
        # All header elements other than the ones above
        # are treated in a generic way.
        elif is_node(element, type_in=list(HEADER_ELEMENTS_SCHEMAS.keys())):
            content.append(render_header_element(soup, element))
        elif is_node(element, type_in=["table_of_contents"]):
            content.append(render_table_of_contents(soup, element))
        elif is_node(element, type_in=["page_separator"]):
            content.append(render_page_separator(soup, element))
        elif is_node(element, type_in=["page_footer"]):
            content.append(render_page_footer(soup, element))
        elif is_node(element, type_in=["image"]):
            content.append(render_image(soup, element))
        elif is_node(element, type_in=["list"]):
            content.append(render_list(soup, element))
        elif is_node(element, type_in=["text_span"]):
            content.append(
                make_new_tag(
                    soup,
                    "div",
                    contents=render_text_span(soup, element),
                )
            )

        elif is_node(element):
            raise ValueError(f"Unexpected node {element.type} in content")

        elif isinstance(element, str):
            content.extend(wrap_in_tag(soup, [element], "div"))
    return content


def render_header_element(
    soup: BeautifulSoup,
    node: Node,
) -> Tag:
    elements: List[PageElementOrString] = []
    pattern = HEADER_ELEMENTS_RENDER_PATTERNS[node.type]

    for splitted_element in split_elements(
        node.children,
        group_text_span_nodes_splitter,
    ):
        if isinstance(splitted_element, SplitMatch):
            strings = get_strings(splitted_element.value)
            if pattern is not None:
                elements.extend(join_split_pile_with_pattern(strings, pattern))
            else:
                elements.extend(strings)

        elif is_node(cast(Node, splitted_element.value), type_in=["page_separator"]):
            elements.append(render_page_separator(soup, cast(Node, splitted_element.value)))

        else:
            raise ValueError(f"Unexpected element {splitted_element.value} in header elements")

    return make_data_tag(
        soup,
        HEADER_ELEMENTS_SCHEMAS[node.type],
        contents=wrap_in_tag(soup, elements, "div"),
    )


def render_visa_motif(
    soup: BeautifulSoup,
    node: Node,
) -> Tag:
    assert is_node(node, type_in=["visa", "motif"])
    elements: List[PageElementOrString] = []
    for element in node.children:
        if is_node(element, type_in=["text_span"]):
            elements.append(get_string(element))
        elif is_node(element, type_in=["list"]):
            elements.append(render_list(soup, element))
        elif is_node(element, type_in=["page_separator"]):
            elements.append(render_page_separator(soup, element))
        else:
            raise ValueError(f"Unexpected element {element} in visa/motif")
    return make_data_tag(
        soup,
        HEADER_ELEMENTS_SCHEMAS[node.type],
        contents=elements,
    )


def rendre_arrete_title(
    soup: BeautifulSoup,
    node: Node,
) -> Tag:
    elements: List[PageElementOrString] = [" ".join(get_strings(node.children))]
    # TODO : Parsing date should be done in a node and not on the fly
    # like this.
    elements = map_splitted_elements(
        split_elements(
            elements,
            make_regex_tree_splitter(DATE_NODE),
        ),
        lambda tree_match: render_date_regex_tree_match(soup, tree_match),
    )
    return make_data_tag(
        soup,
        ARRETE_TITLE_SCHEMA,
        contents=[make_new_tag(soup, "h1", contents=elements)],
    )
