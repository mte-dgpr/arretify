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
from typing import Dict, Sequence, Iterator

from bs4 import Tag

from arretify.utils.functional import iter_func_to_list, chain_functions
from arretify.parsing_utils.dates import DATE_NODE, render_date_regex_tree_match
from arretify.utils.html import is_tag
from arretify.utils.html_semantic import (
    SemanticTagSpec,
    make_semantic_tag,
    is_semantic_tag,
    get_semantic_tag_spec,
)
from arretify.utils.html_create import (
    replace_children,
    wrap_in_tag,
    make_new_tag,
)
from arretify.utils.html_split_merge import make_regex_tree_splitter
from arretify.types import DocumentContext, PageElementOrString
from arretify.parsing_utils.patterns import join_split_pile_with_pattern
from arretify.semantic_tag_specs import (
    EmblemSpec,
    EntitySpec,
    IdentificationSpec,
    ArreteSpec,
    HonorarySpec,
    VisaSpec,
    MotifSpec,
    SupplementaryMotifInfoSpec,
    PageSeparatorSpec,
    PageFooterSpec,
    TableOfContentsSpec,
)
from arretify.step_segmentation.semantic_tag_specs import (
    ListSegmentationSpec,
    TextSpanSegmentationSpec,
    ImageSegmentationSpec,
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
    make_recombine_interrupted_lines_splitter,
    make_while_splitter_for_text_spans,
    make_single_line_splitter_for_text_spans,
    group_text_span_tags_splitter,
    make_probe_from_pattern_proxy,
    get_string,
    get_strings,
    TRANSPARENT_TAG_SPECS,
)
from .document_elements import (
    render_page_footer,
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

HEADER_ELEMENTS_PATTERNS: Dict[SemanticTagSpec, PatternProxy] = {
    EmblemSpec: EMBLEM_PATTERN,
    EntitySpec: ENTITY_PATTERN,
    IdentificationSpec: IDENTIFICATION_PATTERN,
    ArreteSpec: ARRETE_TITLE_PATTERN,
    HonorarySpec: HONORARY_PATTERN,
    VisaSpec: VISA_PATTERN,
    MotifSpec: MOTIF_PATTERN,
    SupplementaryMotifInfoSpec: SUPPLEMENTARY_MOTIF_INFORMATION_PATTERN,
}

HEADER_ELEMENTS_RENDER_PATTERNS: Dict[SemanticTagSpec, PatternProxy | None] = {
    **HEADER_ELEMENTS_PATTERNS,
    HonorarySpec: PatternProxy(join_with_or(HONORARIES_LIST)),
    SupplementaryMotifInfoSpec: None,
}

HEADER_ELEMENTS_PROBES: Dict[SemanticTagSpec, Probe[PageElementOrString]] = {
    EmblemSpec: make_probe_from_pattern_proxy(EMBLEM_PATTERN),
    IdentificationSpec: make_probe_from_pattern_proxy(IDENTIFICATION_PATTERN),
    HonorarySpec: make_probe_from_pattern_proxy(HONORARY_PATTERN),
    SupplementaryMotifInfoSpec: make_probe_from_pattern_proxy(
        SUPPLEMENTARY_MOTIF_INFORMATION_PATTERN
    ),
}

HEADER_ELEMENTS_FUZZY_PROBES: Dict[SemanticTagSpec, Probe[PageElementOrString]] = {
    EntitySpec: make_probe_from_pattern_proxy(ENTITY_PATTERN),
    ArreteSpec: make_probe_from_pattern_proxy(ARRETE_TITLE_PATTERN),
}

VISA_MOTIFS_PATTERNS: Dict[SemanticTagSpec, PatternProxy] = {
    VisaSpec: VISA_PATTERN,
    MotifSpec: MOTIF_PATTERN,
}

VISA_MOTIFS_PROBES: Dict[SemanticTagSpec, Probe[PageElementOrString]] = {
    VisaSpec: make_probe_from_pattern_proxy(VISA_PATTERN),
    MotifSpec: make_probe_from_pattern_proxy(MOTIF_PATTERN),
}


def _is_nothing_else_than(spec: SemanticTagSpec, element: PageElementOrString) -> bool:
    return is_semantic_tag(element, spec_in=[TextSpanSegmentationSpec]) and not any(
        bool(HEADER_ELEMENTS_PATTERNS[other_spec].match(get_string(element)))
        for other_spec in HEADER_ELEMENTS_PATTERNS
        if other_spec != spec
    )


def parse_header(
    context: DocumentContext,
    elements: Sequence[PageElementOrString],
) -> list[PageElementOrString]:
    elements = chain_functions(
        context,
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
            # - before visas and motifs, because they use list tags
            #       to build lists of visas / motifs
            parse_lists,
        ],
    )
    elements = parse_visa_and_motif_elements(context, elements)
    return elements


def _parse_header_element(
    context: DocumentContext,
    elements: Sequence[PageElementOrString],
    spec: SemanticTagSpec,
) -> list[PageElementOrString]:
    """
    Generic function to parse header elements.
    It uses a simple regex pattern to detect the element start,
    and then gathers all following lines while the pattern still matches.
    """
    return map_splitted_elements(
        split_elements(
            elements,
            make_while_splitter_for_text_spans(
                HEADER_ELEMENTS_PROBES[spec], HEADER_ELEMENTS_PROBES[spec]
            ),
        ),
        lambda children: make_semantic_tag(context.soup, spec, contents=children),
    )


def _parse_header_element_fuzzy(
    context: DocumentContext,
    elements: Sequence[PageElementOrString],
    spec: SemanticTagSpec,
) -> list[PageElementOrString]:
    """
    Generic function to parse header elements with a fuzzy match.
    It uses a regex pattern to find the start of the element,
    and then gathers all following lines that do not match another element.
    """
    return map_splitted_elements(
        split_elements(
            elements,
            make_while_splitter_for_text_spans(
                HEADER_ELEMENTS_FUZZY_PROBES[spec],
                lambda elements, index: _is_nothing_else_than(spec, elements[index]),
            ),
        ),
        lambda children: make_semantic_tag(context.soup, spec, contents=children),
    )


def parse_emblem_element(
    context: DocumentContext,
    elements: Sequence[PageElementOrString],
) -> list[PageElementOrString]:
    return _parse_header_element(context, elements, EmblemSpec)


def parse_entity_element(
    context: DocumentContext,
    elements: Sequence[PageElementOrString],
) -> list[PageElementOrString]:
    return _parse_header_element_fuzzy(
        context,
        elements,
        EntitySpec,
    )


def parse_identification_element(
    context: DocumentContext,
    elements: Sequence[PageElementOrString],
) -> list[PageElementOrString]:
    return _parse_header_element(context, elements, IdentificationSpec)


def parse_arrete_title_element(
    context: DocumentContext,
    elements: Sequence[PageElementOrString],
) -> list[PageElementOrString]:
    return _parse_header_element_fuzzy(
        context,
        elements,
        ArreteSpec,
    )


def parse_honorary_element(
    context: DocumentContext,
    elements: Sequence[PageElementOrString],
) -> list[PageElementOrString]:
    return _parse_header_element(context, elements, HonorarySpec)


def parse_supplementary_motif_info_element(
    context: DocumentContext,
    elements: Sequence[PageElementOrString],
) -> list[PageElementOrString]:
    return _parse_header_element(
        context,
        elements,
        SupplementaryMotifInfoSpec,
    )


def parse_visa_and_motif_elements(
    context: DocumentContext,
    elements: Sequence[PageElementOrString],
) -> list[PageElementOrString]:
    elements = _parse_visa_and_motif_elements_pass1(context, elements, VisaSpec)
    elements = _parse_visa_and_motif_elements_pass1(context, elements, MotifSpec)
    elements = _parse_visa_and_motif_elements_pass2(
        context,
        elements,
        spec=VisaSpec,
    )
    elements = _parse_visa_and_motif_elements_pass3(
        context,
        elements,
        spec=VisaSpec,
    )
    elements = _parse_visa_and_motif_elements_pass2(
        context,
        elements,
        spec=MotifSpec,
    )
    elements = _parse_visa_and_motif_elements_pass3(
        context,
        elements,
        spec=MotifSpec,
    )
    return elements


@iter_func_to_list
def _parse_visa_and_motif_elements_pass1(
    context: DocumentContext,
    elements: Sequence[PageElementOrString],
    spec: SemanticTagSpec,
) -> Iterator[PageElementOrString]:
    """
    Pass 1 of parsing visa and motif elements.
    This pass splits the tag flow into segments based on the node pattern.
    It creates tags of type 'visa' or 'motif' for each segment that matches
    the pattern.
    """
    elements = map_splitted_elements(
        split_elements(
            elements,
            make_single_line_splitter_for_text_spans(VISA_MOTIFS_PROBES[spec]),
        ),
        lambda children: make_semantic_tag(context.soup, spec, contents=children),
    )

    # Visas or motifs that are in form :
    # - Vu blabla
    # - Vu bloblo
    # Should have been parsed into list tags.
    # Therefore, we must convert list tags that contain visas and motifs
    # into visa or motif tags.
    for element in elements:
        is_list_of_visas_or_motifs = False
        if is_semantic_tag(element, spec_in=[ListSegmentationSpec]):
            assert len(element.contents) > 0, "List tag should not be empty"
            is_list_of_visas_or_motifs = VISA_MOTIFS_PROBES[spec](element.contents, 0)

        if is_list_of_visas_or_motifs:
            assert is_tag(element)
            for list_item_element in element.contents:
                if is_semantic_tag(list_item_element, spec_in=[TextSpanSegmentationSpec]):
                    yield make_semantic_tag(context.soup, spec, contents=[list_item_element])
                else:
                    raise ValueError(f"Unexpected element {list_item_element}")
        else:
            yield element


@iter_func_to_list
def _parse_visa_and_motif_elements_pass2(
    context: DocumentContext,
    elements: Sequence[PageElementOrString],
    spec: SemanticTagSpec,
) -> Iterator[PageElementOrString]:
    """
    Pass 2 of parsing visa and motif elements.
    This pass processes the tag flow to find the first tag of type
    'visa' or 'motif'. Once found, it decides between one of the several
    types of variants for formatting the visas or motifs, and normalizes
    the tag flow accordingly.
    """
    element: PageElementOrString
    elements = list(elements)

    # Skip tags until we find the first tag of type 'visa' or 'motif'.
    while elements and not is_semantic_tag(elements[0], spec_in=[spec]):
        yield elements.pop(0)
    if not elements:
        return
    first_tag = elements.pop(0)
    assert is_semantic_tag(first_tag, spec_in=[spec]) and len(first_tag.contents) > 0

    first_tag_match = VISA_MOTIFS_PATTERNS[spec].match(get_string(first_tag))
    # 1. Variant "simple" :
    #   Vu que blabla
    #   Vu que bloblo
    if first_tag_match and first_tag_match.group("contents"):
        elements.insert(0, first_tag)
        # Recombine interrupted lines, e.g.
        #   Vu que blabla
        #   <page_separator>
        #   continues on the next page.
        elements = map_splitted_elements(
            split_elements(elements, make_recombine_interrupted_lines_splitter(spec)),
            _recombine_visa_motif_with_next_if_continuing_sentence,
        )
        yield from elements

    # 2. Variant "explicit list" :
    #   Vu :
    #   - blabla
    #   - bloblo
    elif elements and is_semantic_tag(elements[0], spec_in=[ListSegmentationSpec]):
        # Add the "Vu :" to the header
        yield from first_tag.children
        while elements:
            element = elements[0]
            # We're a bit lenient here and accept a few unassigned_line tags,
            # as random text sometimes interferes with the parsing.
            if is_semantic_tag(element, spec_in=TRANSPARENT_TAG_SPECS) or is_semantic_tag(
                element, spec_in=[TextSpanSegmentationSpec]
            ):
                yield elements.pop(0)

            elif is_semantic_tag(element, spec_in=[ListSegmentationSpec]):
                elements.pop(0)
                for list_item_element in element.children:
                    if is_semantic_tag(list_item_element, spec_in=[TextSpanSegmentationSpec]):
                        yield make_semantic_tag(context.soup, spec, contents=[list_item_element])
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
        yield from first_tag.children
        while elements:
            element = elements[0]

            # Lists will be handled in the next pass and appended to the visa or motif tag
            # if applicable.
            if is_semantic_tag(element, spec_in=[ListSegmentationSpec, *TRANSPARENT_TAG_SPECS]):
                yield elements.pop(0)

            elif is_semantic_tag(element, spec_in=[TextSpanSegmentationSpec]):
                yield make_semantic_tag(context.soup, spec, contents=[element])
                elements.pop(0)
            else:
                break
        yield from elements


def _recombine_visa_motif_with_next_if_continuing_sentence(
    elements: Sequence[PageElementOrString],
) -> Tag:
    assert len(elements) > 0 and is_semantic_tag(elements[0], spec_in=[VisaSpec, MotifSpec])
    elements[0].extend(elements[1:])
    return elements[0]


@iter_func_to_list
def _parse_visa_and_motif_elements_pass3(
    context: DocumentContext,
    elements: Sequence[PageElementOrString],
    spec: SemanticTagSpec,
) -> Iterator[PageElementOrString]:
    """
    Pass 3 of parsing visa and motif elements.
    Merges the tags of type 'visa' or 'motif' with the next tag
    if the next tag is a list. This is done to ensure that the
    visa or motif tag contains all its children.
    """
    elements = list(elements)

    while elements:
        element = elements.pop(0)
        if is_semantic_tag(element, spec_in=[spec]):
            transparent_tags_pile: list[Tag] = []
            while elements and is_semantic_tag(elements[0], spec_in=TRANSPARENT_TAG_SPECS):
                transparent_tags_pile.append(elements[0])
                elements.pop(0)

            if elements and is_semantic_tag(elements[0], spec_in=[ListSegmentationSpec]):
                if transparent_tags_pile:
                    element.extend(transparent_tags_pile)
                element.append(elements.pop(0))
                yield element

            else:
                yield element
                yield from transparent_tags_pile

        else:
            yield element


def render_header(
    context: DocumentContext,
    elements: Sequence[PageElementOrString],
) -> Tag:
    content = context.soup.new_tag("div")
    for element in list(elements):
        if is_semantic_tag(element, spec_in=[ArreteSpec]):
            content.append(render_arrete_title(context, element))
        elif is_semantic_tag(element, spec_in=[VisaSpec, MotifSpec]):
            content.append(render_visa_motif(context, element))
        # All header elements other than the ones above
        # are treated in a generic way.
        elif is_semantic_tag(
            element,
            spec_in=[
                EmblemSpec,
                EntitySpec,
                IdentificationSpec,
                ArreteSpec,
                HonorarySpec,
                VisaSpec,
                MotifSpec,
                SupplementaryMotifInfoSpec,
            ],
        ):
            content.append(render_header_element(context, element))
        elif is_semantic_tag(element, spec_in=[TableOfContentsSpec]):
            content.append(render_table_of_contents(context, element))
        elif is_semantic_tag(element, spec_in=[PageSeparatorSpec]):
            content.append(element)
        elif is_semantic_tag(element, spec_in=[PageFooterSpec]):
            content.append(render_page_footer(context, element))
        elif is_semantic_tag(element, spec_in=[ImageSegmentationSpec]):
            content.append(render_image(context, element))
        elif is_semantic_tag(element, spec_in=[ListSegmentationSpec]):
            content.append(render_list(context, element))
        elif is_semantic_tag(element, spec_in=[TextSpanSegmentationSpec]):
            content.append(
                make_new_tag(
                    context.soup,
                    "div",
                    contents=render_text_span(context, element),
                )
            )

        elif is_semantic_tag(element):
            raise ValueError(f"Unexpected tag {element.type} in content")

        elif isinstance(element, str):
            content.extend(wrap_in_tag(context.soup, [element], "div"))
    return content


def render_header_element(
    context: DocumentContext,
    tag: Tag,
) -> Tag:
    contents: list[PageElementOrString] = []
    spec = get_semantic_tag_spec(tag)
    pattern = HEADER_ELEMENTS_RENDER_PATTERNS[spec]

    elements: Sequence[PageElementOrString] = tag.contents
    for splitted_element in split_elements(
        elements,
        group_text_span_tags_splitter,
    ):
        if isinstance(splitted_element, SplitMatch):
            strings = get_strings(splitted_element.value)
            if pattern is not None:
                contents.extend(join_split_pile_with_pattern(strings, pattern))
            else:
                contents.extend(strings)

        else:
            raise ValueError(f"Unexpected element {splitted_element.value} in header elements")

    return replace_children(
        tag,
        wrap_in_tag(context.soup, contents, "div"),
    )


def render_visa_motif(
    context: DocumentContext,
    tag: Tag,
) -> Tag:
    assert is_semantic_tag(tag, spec_in=[VisaSpec, MotifSpec])
    contents: list[PageElementOrString] = []

    for element in tag.contents:
        if is_semantic_tag(element, spec_in=[TextSpanSegmentationSpec]):
            contents.append(get_string(element))
        elif is_semantic_tag(element, spec_in=[ListSegmentationSpec]):
            contents.append(render_list(context, element))
        elif is_semantic_tag(element, spec_in=[PageSeparatorSpec]):
            contents.append(element)
        else:
            raise ValueError(f"Unexpected element {element} in visa/motif")

    return replace_children(
        tag,
        contents,
    )


def render_arrete_title(
    context: DocumentContext,
    tag: Tag,
) -> Tag:
    elements: list[PageElementOrString] = [" ".join(get_strings(tag.contents))]
    # TODO : Parsing date should be done in a tag and not on the fly
    # like this.
    elements = map_splitted_elements(
        split_elements(
            elements,
            make_regex_tree_splitter(DATE_NODE),
        ),
        lambda tree_match: render_date_regex_tree_match(context.soup, tree_match),
    )
    return make_semantic_tag(
        context.soup,
        ArreteSpec,
        contents=[make_new_tag(context.soup, "h1", contents=elements)],
    )
