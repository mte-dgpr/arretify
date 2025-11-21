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
import logging
from typing import Dict, Iterator, Optional, Sequence

from arretify.errors import ErrorCodes
from arretify.semantic_tag_specs import (
    AlineaData,
    PageFooterSpec,
    PageSeparatorSpec,
    TableOfContentsSpec,
)
from arretify.step_segmentation.semantic_tag_specs import (
    AlineaSegmentationSpec,
    SectionSegmentationSpec,
    SectionTitleSegmentationData,
    SectionTitleSegmentationSpec,
    TableDescriptionSegmentationSpec,
    TableSegmentationSpec,
    TextSpanSegmentationSpec,
)
from arretify.types import DocumentContext, ProtectedTag, ProtectedTagOrStr, SectionType
from arretify.utils.functional import chain_functions, iter_func_to_list
from arretify.utils.html_create import make_semantic_tag
from arretify.utils.html_semantic import (
    get_semantic_tag_data,
    is_semantic_tag,
    set_semantic_tag_data,
)
from arretify.utils.split import split_at_first_verb
from arretify.utils.split_merge import split_and_map_elements

from .basic_elements import parse_blockquotes, parse_images, parse_lists, parse_tables
from .core import (
    combine_text_spans,
    get_string,
    make_probe_from_pattern_proxy,
    make_recombine_interrupted_lines_splitter,
    make_single_line_splitter_for_text_spans,
)
from .titles_detection import TITLE_NODE, is_next_title, parse_title_info, parse_title_text

_LOGGER = logging.getLogger(__name__)


_is_title_string = make_probe_from_pattern_proxy(
    TITLE_NODE.pattern,
)


def is_title(elements: Sequence[ProtectedTagOrStr], index: int) -> bool:
    element = elements[index]
    assert is_semantic_tag(element, spec_in=[TextSpanSegmentationSpec])
    # Exclude text_span tags that start with an inline tag.
    # This excludes cases when a line starts with an address
    # or another inline element, which cannot be a title.
    if len(element.contents) == 0 or not isinstance(element.contents[0], str):
        return False
    else:
        return _is_title_string(elements, index)


def _get_downstream_sections_types(section_type):
    ordered_sections_types = [section_type for section_type in SectionType]
    section_index = ordered_sections_types.index(section_type)
    return ordered_sections_types[section_index + 1 :]


def parse_content(
    context: DocumentContext,
    elements: Sequence[ProtectedTagOrStr],
) -> list[ProtectedTagOrStr]:
    elements = parse_blockquotes(context, elements)
    elements = parse_section_titles(context, elements)
    elements = parse_sections(context, elements)
    return elements


def parse_section_titles(
    context: DocumentContext,
    elements: Sequence[ProtectedTagOrStr],
    lite: bool = False,
) -> list[ProtectedTagOrStr]:
    # First fix titles containing alinea
    # Do it only if we are not in lite mode as this is computation intensive
    if lite is False:
        elements = _fix_titles_containing_alineas(context, elements)

    # Then collect all section titles in list
    tag_list = _create_section_title_tags(context, elements)
    section_title_tags: list[ProtectedTag] = [
        e for e in tag_list if is_semantic_tag(e, spec_in=[SectionTitleSegmentationSpec])
    ]

    # Ancestry order from root to the current section in the parsing context
    sections: int = 1

    # list of integers from previous section title
    current_global_levels: Optional[list[int]] = None

    # Previous list of integers extracted from the lastly seen section title for each section type
    current_titles_levels: Dict[SectionType, Optional[list[int]]] = {}

    # Considering the usual section types hierarchy, this dictionary helps improving the
    # hierarchy within the document, e.g. when finding titles, chapters and articles all having
    # only one number in their numberings, it adds minimal level for selecting the correct schema
    min_titles_levels: Dict[SectionType, int] = {}

    # Used to select the schema level for titles
    current_schema_level = -1

    for section_title_tag in section_title_tags:
        error_codes: list[ErrorCodes] = []
        title_text = get_string(section_title_tag)

        # Parse title info
        title_info = parse_title_info(title_text)
        new_section_type = title_info.section_type

        # Add a tag if the titles are not contiguous
        current_title_levels = current_titles_levels.get(new_section_type)
        new_title_levels = list(title_info.levels) if title_info.levels else None

        if not is_next_title(current_global_levels, current_title_levels, new_title_levels):
            _LOGGER.warning(
                f"Detected title of levels {new_title_levels} after current global levels"
                f" {current_global_levels} and current section levels {current_title_levels}"
            )
            error_codes.append(ErrorCodes.non_contiguous_titles)

        current_global_levels = new_title_levels
        current_titles_levels[new_section_type] = new_title_levels

        # Process ancestry for new title
        new_schema_level = max(
            min_titles_levels.get(new_section_type, 0),
            len(new_title_levels) - 1 if new_title_levels else -1,
        )

        if new_schema_level - current_schema_level >= 1:
            # Nothing to do we just add the new section below the existing one
            pass
        elif new_schema_level - current_schema_level <= 0:
            # Empty the ancestry tree until we reach the right ancestor
            while new_schema_level - current_schema_level <= 0:
                sections -= 1
                current_schema_level = sections - 2
        else:
            raise RuntimeError(f"unexpected title {title_text}, current level {sections}")

        sections += 1
        current_schema_level = sections - 2

        downstream_sections_types = _get_downstream_sections_types(new_section_type)
        for downstream_section_type in downstream_sections_types:
            min_titles_levels[downstream_section_type] = max(
                min_titles_levels.get(downstream_section_type, 0),
                len(new_title_levels) if new_title_levels else 0,
            )

        set_semantic_tag_data(
            SectionTitleSegmentationSpec,
            section_title_tag,
            SectionTitleSegmentationData(
                type=new_section_type.value,
                level=new_schema_level,
                number=title_info.number,
                title=title_info.text,
                error_codes=error_codes if error_codes else None,
            ),
        )

    return tag_list


@iter_func_to_list
def _fix_titles_containing_alineas(
    context: DocumentContext, elements: Sequence[ProtectedTagOrStr]
) -> Iterator[ProtectedTagOrStr]:
    for element in elements:
        if not is_semantic_tag(element, spec_in=[TextSpanSegmentationSpec]):
            yield element
            continue

        title_string = get_string(element)
        if not TITLE_NODE.pattern.match(title_string):
            yield element
            continue

        section_name, text = parse_title_text(title_string)
        result = split_at_first_verb(text)
        if result is None:
            yield element
            continue

        title_text, alinea_text = result
        # Return two segments: one for the title and one for the alinea
        if not title_text:
            title_text = section_name
        else:
            title_text = section_name + title_text

        # As we don't know exactly the split position in the original text,
        # we use an approximation of original position for source mapping.
        text_span_data = get_semantic_tag_data(TextSpanSegmentationSpec, element)
        yield make_semantic_tag(
            context.protected_soup,
            TextSpanSegmentationSpec,
            contents=[title_text],
            data=text_span_data,
        )
        yield make_semantic_tag(
            context.protected_soup,
            TextSpanSegmentationSpec,
            contents=[alinea_text],
            data=text_span_data,
        )


def _create_section_title_tags(
    context: DocumentContext,
    elements: Sequence[ProtectedTagOrStr],
) -> list[ProtectedTagOrStr]:
    return split_and_map_elements(
        elements,
        make_single_line_splitter_for_text_spans(is_title),
        lambda contents: make_semantic_tag(
            context.protected_soup,
            SectionTitleSegmentationSpec,
            contents=contents,
        ),
    )


@iter_func_to_list
def parse_sections(
    context: DocumentContext,
    elements: Sequence[ProtectedTagOrStr],
    level: int = 0,
) -> Iterator[ProtectedTagOrStr]:
    """
    Takes an input flow with already parsed section titles, and recursively
    creates sections that groups the section titles and their content together.

    For example, given the following input flow:

    <Title 1>
    <Title 1.1>
    <Content 1.1>
    <Title 2>
    <Content 2>

    the output will be:
    <Section 1>
        <Title 1>

        <Section 1.1>
            <Title 1.1>
            <Content 1.1>
        </Section 1.1>
    </Section 1>

    <Section 2>
        <Title 2>
        <Content 2>
    </Section 2>
    """
    elements = list(elements)
    pile: list[ProtectedTagOrStr] = []

    # 1. First, parse content encountered before the first sub-section title
    #
    # This is useful in 2 cases :
    # - when we have reached the leaf section level, and we need
    #       to parse alineas
    # - when there is content before the first section title (this is a special
    #       case and rarely happens).
    pile = []
    while elements and not is_semantic_tag(elements[0], spec_in=[SectionTitleSegmentationSpec]):
        pile.append(elements.pop(0))
    if pile:
        yield from parse_alineas(context, pile)
    # 2. Second, we parse sections at deeper levels than the current `level`.
    #
    # This is useful in 2 cases :
    # - when there is no title at the current level, and we simply need to
    #       go deeper in the hierarchy
    # - when there is a missing section title at the current level,
    #       e.g. if the flow looks like this (Title 1 is missing) :
    #       <Title 1.1>
    #       <Title 1.2>
    #       <Title 2>
    #       <Title 2.1>
    #       <Title 3>
    pile = []
    while elements:
        if is_semantic_tag(elements[0], spec_in=[SectionTitleSegmentationSpec]):
            element_level = get_semantic_tag_data(SectionTitleSegmentationSpec, elements[0]).level
            assert element_level is not None
            if element_level == level:
                break
            elif element_level > level:
                pile.append(elements.pop(0))
            else:
                raise RuntimeError(
                    f"Unexpected section title level {element_level} " f"at level {level}"
                )
        else:
            pile.append(elements.pop(0))
    if pile:
        yield from parse_sections(context, pile, level=level + 1)
    # 3. Finally parse sections at current level
    pile = []
    while elements:
        # Add section title to the pile
        pile.append(elements.pop(0))

        # Fill-in the pile until we find next section title
        # of the same level
        while elements:
            if is_semantic_tag(elements[0], spec_in=[SectionTitleSegmentationSpec]):
                element_level = get_semantic_tag_data(
                    SectionTitleSegmentationSpec, elements[0]
                ).level
                assert element_level is not None
                if element_level == level:
                    break
                elif element_level < level:
                    raise RuntimeError(f"Unexpected section title level {element_level} ")
            pile.append(elements.pop(0))

        if pile:
            section_title, section_children = pile[0], pile[1:]
            yield make_semantic_tag(
                context.protected_soup,
                SectionSegmentationSpec,
                contents=[section_title]
                + list(parse_sections(context, section_children, level=level + 1)),
            )
            pile = []


# ALINEA : "Constitue un alinéa toute phrase, tout mot, tout ensemble de phrases ou de
# mots commençant à la ligne, précédés ou non d’un tiret, d’un point, d’une
# numérotation ou de guillemets, sans qu’il y ait lieu d’établir des distinctions selon
# la nature du signe placé à la fin de la ligne précédente (point, deux-points ou
# point-virgule). Un tableau constitue un seul alinéa (définition complète dans le
# guide de légistique)."
# REF : https://www.legifrance.gouv.fr/contenu/Media/files/lexique-api-lgf.docx
@iter_func_to_list
def parse_alineas(
    context: DocumentContext, elements: Sequence[ProtectedTagOrStr]
) -> Iterator[ProtectedTagOrStr]:
    alinea_count = 1
    elements = chain_functions(
        context,
        elements,
        [parse_tables, parse_lists, parse_images],
    )

    # Recombine interrupted lines before processing elements.
    # e.g.
    #   This is an alinea that
    #   <page_separator>
    #   continues on the next page.
    elements = split_and_map_elements(
        elements,
        make_recombine_interrupted_lines_splitter(TextSpanSegmentationSpec),
        lambda grouped_elements: combine_text_spans(context, grouped_elements),
    )

    while elements:
        element = elements.pop(0)
        # table_of_contents can appear here if we are in an annexe (then it isn't really an
        # alinea but that's how the detection works for now).
        if is_semantic_tag(
            element, spec_in=[PageFooterSpec, TableOfContentsSpec, PageSeparatorSpec]
        ):
            yield element
            continue

        alinea_children: list[ProtectedTagOrStr] = []
        if is_semantic_tag(element, spec_in=[TableSegmentationSpec]):
            alinea_children = [element]
            while elements and is_semantic_tag(
                elements[0], spec_in=[TableDescriptionSegmentationSpec]
            ):
                alinea_children.append(elements[0])
                elements.pop(0)

        else:
            alinea_children = [element]
        yield make_semantic_tag(
            context.protected_soup,
            AlineaSegmentationSpec,
            contents=alinea_children,
            data=AlineaData(
                number=alinea_count,
            ),
        )
        alinea_count += 1
