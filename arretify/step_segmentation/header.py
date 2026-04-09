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
from typing import Dict, Iterator, Sequence

from arretify.parsing_utils.dates import DATE_NODE, render_date_regex_tree_match
from arretify.regex_utils import PatternProxy, join_with_or
from arretify.semantic_tag_specs import (
    ArreteTitleSpec,
    EmblemSpec,
    EntitySpec,
    HonorarySpec,
    IdentificationSpec,
    MotifSpec,
    SupplementaryMotifInfoSpec,
    VisaSpec,
)
from arretify.step_segmentation.semantic_tag_specs import (
    HeaderSegmentationSpec,
    ListSegmentationSpec,
    MotifSegmentationSpec,
    TextSpanSegmentationSpec,
    VisaSegmentationSpec,
)
from arretify.types import DocumentContext, ProtectedTag, ProtectedTagOrStr
from arretify.utils.functional import chain_functions, iter_func_to_list
from arretify.utils.html import is_tag
from arretify.utils.html_create import make_semantic_tag, make_tag, replace_contents
from arretify.utils.html_semantic import SemanticTagSpec, is_semantic_tag
from arretify.utils.html_split_merge import (
    PatternSplitterMatch,
    make_pattern_splitter_ignoring_inline_tags,
    make_regex_tree_splitter,
    recombine_strings,
)
from arretify.utils.split_merge import (
    Probe,
    SplitMatch,
    Splitter,
    split_and_map_elements,
    split_elements,
)

from .basic_elements import parse_lists, parse_unknown_elements
from .core import (
    PAGINATION_TAG_SPECS,
    get_string,
    get_strings,
    make_probe_from_pattern_proxy,
    make_recombine_interrupted_lines_splitter,
    make_single_line_splitter_for_text_spans,
    make_while_splitter_for_text_spans,
    pick_text_spans,
)


def parse_header(
    context: DocumentContext,
    elements: Sequence[ProtectedTagOrStr],
) -> list[ProtectedTagOrStr]:
    return chain_functions(
        context,
        list(elements),
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
            # Must be executed after parsing of all other elements,
            # in particular because visas and motifs parsing is more fuzzy.
            parse_visa_and_motif_elements,
            # Final step, to catch and save any unknown elements instead of raising errors
            lambda context, elements: parse_unknown_elements(
                context, HeaderSegmentationSpec, elements
            ),
        ],
    )


# -------------------- Header elements -------------------- #


EMBLEMS_LIST = [
    r"liberté",
    r"égalité",
    r"fraternité",
    r"république fran[cç]aise",
]

EMBLEM_PATTERN = PatternProxy(join_with_or(EMBLEMS_LIST))
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

HEADER_ELEMENTS_SPECS: Sequence[SemanticTagSpec] = [
    EmblemSpec,
    EntitySpec,
    IdentificationSpec,
    ArreteTitleSpec,
    HonorarySpec,
    SupplementaryMotifInfoSpec,
]


HEADER_ELEMENTS_PATTERNS: Dict[SemanticTagSpec, PatternProxy] = {
    EmblemSpec: EMBLEM_PATTERN,
    EntitySpec: ENTITY_PATTERN,
    IdentificationSpec: IDENTIFICATION_PATTERN,
    ArreteTitleSpec: ARRETE_TITLE_PATTERN,
    HonorarySpec: HONORARY_PATTERN,
    SupplementaryMotifInfoSpec: SUPPLEMENTARY_MOTIF_INFORMATION_PATTERN,
}

HEADER_ELEMENTS_PROBES: Dict[SemanticTagSpec, Probe[ProtectedTagOrStr]] = {
    EmblemSpec: make_probe_from_pattern_proxy(EMBLEM_PATTERN),
    IdentificationSpec: make_probe_from_pattern_proxy(IDENTIFICATION_PATTERN),
    HonorarySpec: make_probe_from_pattern_proxy(HONORARY_PATTERN),
    SupplementaryMotifInfoSpec: make_probe_from_pattern_proxy(
        SUPPLEMENTARY_MOTIF_INFORMATION_PATTERN
    ),
}

HEADER_ELEMENTS_FUZZY_PROBES: Dict[SemanticTagSpec, Probe[ProtectedTagOrStr]] = {
    EntitySpec: make_probe_from_pattern_proxy(ENTITY_PATTERN),
    ArreteTitleSpec: make_probe_from_pattern_proxy(ARRETE_TITLE_PATTERN),
}

HEADER_ELEMENTS_RENDER_SPLITTERS: Dict[
    SemanticTagSpec, Splitter[ProtectedTagOrStr, PatternSplitterMatch] | None
] = {
    cls: make_pattern_splitter_ignoring_inline_tags(pattern)
    for cls, pattern in HEADER_ELEMENTS_PATTERNS.items()
}
HEADER_ELEMENTS_RENDER_SPLITTERS.update(
    {
        HonorarySpec: make_pattern_splitter_ignoring_inline_tags(
            PatternProxy(join_with_or(HONORARIES_LIST))
        ),
        SupplementaryMotifInfoSpec: None,
    }
)


ARRETE_KEYWORD_PATTERN = PatternProxy(r"^\W*arrête\W*$")
"""Detect the "arrête" keyword, marking the beginning of the main content of the document."""


is_arrete_keyword = pick_text_spans(make_probe_from_pattern_proxy(ARRETE_KEYWORD_PATTERN))


def parse_emblem_element(
    context: DocumentContext,
    elements: Sequence[ProtectedTagOrStr],
) -> list[ProtectedTagOrStr]:
    return split_and_map_elements(
        elements,
        _make_header_elements_splitter(EmblemSpec),
        lambda contents: _make_header_element_tag(context, EmblemSpec, contents),
    )


def parse_entity_element(
    context: DocumentContext,
    elements: Sequence[ProtectedTagOrStr],
) -> list[ProtectedTagOrStr]:
    return split_and_map_elements(
        elements,
        _make_header_elements_fuzzy_splitter(EntitySpec),
        lambda contents: _make_header_element_tag(context, EntitySpec, contents),
    )


def parse_identification_element(
    context: DocumentContext,
    elements: Sequence[ProtectedTagOrStr],
) -> list[ProtectedTagOrStr]:
    return split_and_map_elements(
        elements,
        _make_header_elements_splitter(IdentificationSpec),
        lambda contents: _make_header_element_tag(context, IdentificationSpec, contents),
    )


def parse_arrete_title_element(
    context: DocumentContext,
    elements: Sequence[ProtectedTagOrStr],
) -> list[ProtectedTagOrStr]:
    return split_and_map_elements(
        elements,
        _make_header_elements_fuzzy_splitter(ArreteTitleSpec),
        lambda contents: _make_arrete_title_tag(context, contents),
    )


def parse_honorary_element(
    context: DocumentContext,
    elements: Sequence[ProtectedTagOrStr],
) -> list[ProtectedTagOrStr]:
    return split_and_map_elements(
        elements,
        _make_header_elements_splitter(HonorarySpec),
        lambda contents: _make_header_element_tag(context, HonorarySpec, contents),
    )


def parse_supplementary_motif_info_element(
    context: DocumentContext,
    elements: Sequence[ProtectedTagOrStr],
) -> list[ProtectedTagOrStr]:
    return split_and_map_elements(
        elements,
        _make_header_elements_splitter(SupplementaryMotifInfoSpec),
        lambda contents: _make_header_element_tag(context, SupplementaryMotifInfoSpec, contents),
    )


def parse_arrete_keyword(
    context: DocumentContext,
    elements: Sequence[ProtectedTagOrStr],
) -> Sequence[ProtectedTagOrStr]:
    """
    Parse the "arrête" keyword just before the first section title.
    """
    if not is_arrete_keyword(elements, len(elements) - 1):
        raise ValueError("The element should be the 'arrête' keyword.")
    return [
        *elements[:-1],
        _make_header_element_tag(context, SupplementaryMotifInfoSpec, [elements[-1]]),
    ]


def _make_header_elements_splitter(
    spec: SemanticTagSpec,
) -> Splitter[ProtectedTagOrStr, Sequence[ProtectedTagOrStr]]:
    return make_while_splitter_for_text_spans(
        HEADER_ELEMENTS_PROBES[spec], HEADER_ELEMENTS_PROBES[spec]
    )


def _make_header_elements_fuzzy_splitter(
    spec: SemanticTagSpec,
) -> Splitter[ProtectedTagOrStr, Sequence[ProtectedTagOrStr]]:
    return make_while_splitter_for_text_spans(
        HEADER_ELEMENTS_FUZZY_PROBES[spec],
        lambda elements, index: _is_nothing_else_than(spec, elements[index]),
    )


def _is_nothing_else_than(spec: SemanticTagSpec, element: ProtectedTagOrStr) -> bool:
    all_patterns: Dict[SemanticTagSpec, PatternProxy] = {
        **HEADER_ELEMENTS_PATTERNS,
        **VISA_MOTIFS_PATTERNS,
    }
    return is_semantic_tag(element, spec_in=[TextSpanSegmentationSpec]) and not any(
        bool(all_patterns[other_spec].match(get_string(element)))
        for other_spec in all_patterns
        if other_spec != spec
    )


def _make_arrete_title_tag(
    context: DocumentContext,
    contents: Sequence[ProtectedTagOrStr],
) -> ProtectedTag:
    elements: list[ProtectedTagOrStr] = [" ".join(get_strings(contents))]
    elements = split_and_map_elements(
        elements,
        make_regex_tree_splitter(DATE_NODE),
        lambda tree_match: render_date_regex_tree_match(context.protected_soup, tree_match),
    )
    return make_semantic_tag(
        context.protected_soup,
        ArreteTitleSpec,
        contents=[make_tag(context.protected_soup, "h1", contents=elements)],
    )


def _make_header_element_tag(
    context: DocumentContext,
    spec: SemanticTagSpec,
    contents: Sequence[ProtectedTagOrStr],
) -> ProtectedTag:
    if not all(
        is_semantic_tag(c, spec_in=[TextSpanSegmentationSpec, *PAGINATION_TAG_SPECS])
        for c in contents
    ):
        raise ValueError(f"Unexpected contents in rendering for {spec.spec_name}:\n{contents}")

    rendered_contents: list[ProtectedTagOrStr] = []
    splitter = HEADER_ELEMENTS_RENDER_SPLITTERS[spec]

    if splitter is None:
        for element in contents:
            if is_semantic_tag(element, spec_in=[TextSpanSegmentationSpec]):
                rendered_contents.append(_make_header_element_line(context, element.contents))
            else:
                rendered_contents.append(element)

    # If a splitter is provided, we want to reorganise the lines so that we start a line by a match.
    # Example :
    #
    # "Service risque bureau des déchets" -> is reorganised as :
    #
    # "Service risques"
    # "Bureau des déchets"
    else:
        # 1. Extract all text from text_spans into a flat list for easier splitting.
        flattened: list[ProtectedTagOrStr] = []
        for element in contents:
            if is_semantic_tag(element, spec_in=[TextSpanSegmentationSpec]):
                flattened.extend(element.contents)
            else:
                flattened.append(element)
        flattened = recombine_strings(flattened, separator=" ")

        # 2. Split the text using the splitter, each match corresponds with the start of a line.
        line_elements: list[ProtectedTagOrStr] = []
        for split_match in split_elements(flattened, splitter):
            if isinstance(split_match, SplitMatch):
                if line_elements:
                    rendered_contents.append(_make_header_element_line(context, line_elements))
                line_elements = list(split_match.value.elements)
            else:
                line_elements.extend(split_match.value)
        if line_elements:
            rendered_contents.append(_make_header_element_line(context, line_elements))

    return make_semantic_tag(
        context.protected_soup,
        spec,
        contents=rendered_contents,
    )


def _make_header_element_line(
    context: DocumentContext, contents: list[ProtectedTagOrStr]
) -> ProtectedTag:
    if isinstance(contents[0], str):
        contents[0] = contents[0].lstrip()
    if isinstance(contents[-1], str):
        contents[-1] = contents[-1].rstrip()
    return make_tag(context.protected_soup, "div", contents=contents)


# -------------------- Visa and Motifs -------------------- #

VISA_PATTERN = PatternProxy(r"^\W*vu(\s*:\s*|\b)(?P<contents>.*)")
"""Detect if the sentence starts with "vu"."""

MOTIF_PATTERN = PatternProxy(r"^\W*considerant(\s*:\s*|\b)(?P<contents>.*)")
"""Detect if the sentence starts with "considerant"."""

VISA_MOTIFS_PATTERNS: Dict[SemanticTagSpec, PatternProxy] = {
    VisaSegmentationSpec: VISA_PATTERN,
    MotifSegmentationSpec: MOTIF_PATTERN,
}

VISA_MOTIFS_PROBES: Dict[SemanticTagSpec, Probe[ProtectedTagOrStr]] = {
    VisaSegmentationSpec: make_probe_from_pattern_proxy(VISA_PATTERN),
    MotifSegmentationSpec: make_probe_from_pattern_proxy(MOTIF_PATTERN),
}

VISA_MOTIFS_RENDER_SPECS: Dict[SemanticTagSpec, SemanticTagSpec] = {
    VisaSegmentationSpec: VisaSpec,
    MotifSegmentationSpec: MotifSpec,
}


def parse_visa_and_motif_elements(
    context: DocumentContext,
    elements: Sequence[ProtectedTagOrStr],
) -> list[ProtectedTagOrStr]:
    elements = _parse_visa_and_motif_elements_pass1(context, elements, VisaSegmentationSpec)
    elements = _parse_visa_and_motif_elements_pass1(context, elements, MotifSegmentationSpec)
    elements = _parse_visa_and_motif_elements_pass2(
        context,
        elements,
        spec=VisaSegmentationSpec,
    )
    elements = _parse_visa_and_motif_elements_pass3(
        context,
        elements,
        spec=VisaSegmentationSpec,
    )
    elements = _parse_visa_and_motif_elements_pass2(
        context,
        elements,
        spec=MotifSegmentationSpec,
    )
    elements = _parse_visa_and_motif_elements_pass3(
        context,
        elements,
        spec=MotifSegmentationSpec,
    )
    return elements


@iter_func_to_list
def _parse_visa_and_motif_elements_pass1(
    context: DocumentContext,
    elements: Sequence[ProtectedTagOrStr],
    spec: SemanticTagSpec,
) -> Iterator[ProtectedTagOrStr]:
    """
    Pass 1 of parsing visa and motif elements.
    It simply creates tags of type 'visa' or 'motif' for each line that matches
    the pattern, without taking into account following lines.
    """
    elements = split_and_map_elements(
        elements,
        make_single_line_splitter_for_text_spans(VISA_MOTIFS_PROBES[spec]),
        lambda contents: make_semantic_tag(context.protected_soup, spec, contents=contents),
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
                    yield make_semantic_tag(
                        context.protected_soup, spec, contents=[list_item_element]
                    )
                elif is_semantic_tag(list_item_element, spec_in=PAGINATION_TAG_SPECS):
                    yield list_item_element
                else:
                    raise ValueError(f"Unexpected element {list_item_element}")
        else:
            yield element


@iter_func_to_list
def _parse_visa_and_motif_elements_pass2(
    context: DocumentContext,
    elements: Sequence[ProtectedTagOrStr],
    spec: SemanticTagSpec,
) -> Iterator[ProtectedTagOrStr]:
    """
    Pass 2 of parsing visa and motif elements.
    This pass processes the tag flow to find the first tag of type
    'visa' or 'motif'. Once found, it decides between one of the several
    types of variants for formatting the visas or motifs, and normalizes
    the tag flow accordingly.
    """
    element: ProtectedTagOrStr
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
    first_tag_contents: str | None = None
    if first_tag_match:
        first_tag_contents = first_tag_match.group("contents")
        if first_tag_contents is not None:
            first_tag_contents = first_tag_contents.strip()
    if first_tag_contents:
        elements.insert(0, first_tag)
        # Recombine interrupted lines, e.g.
        #   Vu que blabla
        #   <page_separator>
        #   continues on the next page.
        elements = split_and_map_elements(
            elements,
            make_recombine_interrupted_lines_splitter(spec),
            _recombine_visa_motif_with_next_if_continuing_sentence,
        )
        yield from elements

    # 2. Variant "explicit list" :
    #   Vu :
    #   - blabla
    #   - bloblo
    elif elements and is_semantic_tag(elements[0], spec_in=[ListSegmentationSpec]):
        # Add the "Vu :" to the header
        yield from first_tag.contents
        while elements:
            element = elements[0]
            # We're a bit lenient here and accept a few extra tags,
            # as random text sometimes interferes with the parsing
            # (e.g. some page footer text that we couldn't filter out before).
            if is_semantic_tag(element, spec_in=[TextSpanSegmentationSpec, *PAGINATION_TAG_SPECS]):
                yield elements.pop(0)

            elif is_semantic_tag(element, spec_in=[ListSegmentationSpec]):
                elements.pop(0)
                for list_item_element in element.contents:
                    if is_semantic_tag(list_item_element, spec_in=[TextSpanSegmentationSpec]):
                        yield make_semantic_tag(
                            context.protected_soup, spec, contents=[list_item_element]
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
        yield from first_tag.contents
        while elements:
            element = elements[0]

            # Lists will be handled in the next pass and appended to the visa or motif tag
            # if applicable.
            if is_semantic_tag(element, spec_in=[ListSegmentationSpec, *PAGINATION_TAG_SPECS]):
                yield elements.pop(0)

            elif is_semantic_tag(element, spec_in=[TextSpanSegmentationSpec]):
                yield make_semantic_tag(context.protected_soup, spec, contents=[element])
                elements.pop(0)
            else:
                break
        yield from elements


def _recombine_visa_motif_with_next_if_continuing_sentence(
    elements: Sequence[ProtectedTagOrStr],
) -> ProtectedTag:
    assert len(elements) > 0 and is_semantic_tag(
        elements[0], spec_in=[VisaSegmentationSpec, MotifSegmentationSpec]
    )
    return replace_contents(elements[0], elements[0].contents + list(elements[1:]))


@iter_func_to_list
def _parse_visa_and_motif_elements_pass3(
    context: DocumentContext,
    elements: Sequence[ProtectedTagOrStr],
    spec: SemanticTagSpec,
) -> Iterator[ProtectedTagOrStr]:
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
            transparent_tags_pile: list[ProtectedTag] = []
            while elements and is_semantic_tag(elements[0], spec_in=PAGINATION_TAG_SPECS):
                transparent_tags_pile.append(elements[0])
                elements.pop(0)

            if elements and is_semantic_tag(elements[0], spec_in=[ListSegmentationSpec]):
                yield replace_contents(
                    element, element.contents + transparent_tags_pile + [elements.pop(0)]
                )

            else:
                yield element
                yield from transparent_tags_pile

        else:
            yield element
