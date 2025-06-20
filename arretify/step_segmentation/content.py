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
from typing import Dict, List, Optional, Iterator
import logging

from bs4 import (
    BeautifulSoup,
    Tag,
)

from arretify.types import SectionType, DataElementDataDict, PageElementOrString
from arretify.utils.html import (
    make_data_tag,
    render_str_list_attribute,
)
from arretify.html_schemas import (
    SECTION_SCHEMA,
    SECTION_TITLE_SCHEMAS,
    ALINEA_SCHEMA,
)
from arretify.parsing_utils.source_mapping import TextSegments
from arretify.errors import ErrorCodes
from .basic_elements import parse_basic_elements, render_basic_elements, _parse_inline_quotes
from .document_elements import (
    is_document_element,
    parse_document_elements,
)
from .titles_detection import (
    is_title,
    parse_title_info,
    is_next_title,
)
from .core import Element, ElementFlow


_LOGGER = logging.getLogger(__name__)


def parse_content(
    soup: BeautifulSoup,
    content: Tag,
    lines: TextSegments,
    exit_on_appendix: bool = True,
) -> TextSegments:
    # Ancestry order from root to the current section in the parsing context
    sections: List[Tag] = [content]

    # List of integers from previous section title
    current_global_levels: Optional[List[int]] = None

    # Previous list of integers extracted from the lastly seen section title for each section type
    current_titles_levels: Dict[SectionType, Optional[List[int]]] = {}

    # Considering the usual section types hierarchy, this dictionary helps improving the
    # hierarchy within the document, e.g. when finding titles, chapters and articles all having
    # only one number in their numberings, it adds minimal level for selecting the correct schema
    min_titles_levels: Dict[SectionType, int] = {}

    # Used to select the schema level for titles
    current_schema_level = -1

    while lines:

        # Parse title info
        title_info = parse_title_info(lines[0].contents)
        new_section_type = title_info.section_type

        # Appendix is considered as a different part of the document
        if exit_on_appendix and new_section_type == SectionType.ANNEXE:
            break

        # Create element encompassing contents of this new section
        section_element = make_data_tag(
            soup,
            SECTION_SCHEMA,
            data=dict(
                type=new_section_type.value,
                number=title_info.number,
                title=title_info.text,
            ),
        )

        # Add a tag if the titles are not contiguous
        current_title_levels = current_titles_levels.get(new_section_type)
        new_title_levels = title_info.levels
        title_element_data: DataElementDataDict = dict()

        if not is_next_title(current_global_levels, current_title_levels, new_title_levels):

            _LOGGER.warning(
                f"Detected title of levels {new_title_levels} after current global levels"
                f" {current_global_levels} and current section levels {current_title_levels}"
            )

            title_element_data["error_codes"] = render_str_list_attribute(
                [ErrorCodes.non_contiguous_titles.value]
            )

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
                sections.pop()
                current_schema_level = len(sections) - 2
        else:
            raise RuntimeError(
                f"unexpected title {lines[0].contents}, current level {len(sections)}"
            )

        sections[-1].append(section_element)
        sections.append(section_element)

        current_schema_level = len(sections) - 2

        downstream_sections_types = _get_downstream_sections_types(new_section_type)
        for downstream_section_type in downstream_sections_types:
            min_titles_levels[downstream_section_type] = max(
                min_titles_levels.get(downstream_section_type, 0),
                len(new_title_levels) if new_title_levels else 0,
            )

        # Add the title contents in this new section
        title_contents = lines.pop(0).contents
        title_element = make_data_tag(
            soup,
            SECTION_TITLE_SCHEMAS[new_schema_level],
            contents=[title_contents],
            data=title_element_data,
        )
        section_element.append(title_element)

        # Within a section to number alineas
        alinea_count = 0

        # Parse elements that can be found across the document
        while lines and not is_title(lines[0].contents):
            lines = parse_document_elements(soup, section_element, lines)

            section_pile: TextSegments = []
            while lines and not (
                is_title(lines[0].contents) or is_document_element(lines[0].contents)
            ):
                section_pile.append(lines.pop(0))

            element_flow = parse_basic_elements(section_pile)
            element_flow = parse_alineas(element_flow)

            for alinea_element in element_flow:
                assert isinstance(alinea_element, Element)
                assert alinea_element.name == "alinea"
                alinea_count += 1
                section_element.append(render_alinea(soup, alinea_element, alinea_count))

    return lines


def _get_downstream_sections_types(section_type):
    ordered_sections_types = [section_type for section_type in SectionType]
    section_index = ordered_sections_types.index(section_type)
    return ordered_sections_types[section_index + 1 :]


# Parse alineas until a new section is detected
# ALINEA : "Constitue un alinéa toute phrase, tout mot, tout ensemble de phrases ou de
# mots commençant à la ligne, précédés ou non d’un tiret, d’un point, d’une
# numérotation ou de guillemets, sans qu’il y ait lieu d’établir des distinctions selon
# la nature du signe placé à la fin de la ligne précédente (point, deux-points ou
# point-virgule). Un tableau constitue un seul alinéa (définition complète dans le
# guide de légistique)."
# REF : https://www.legifrance.gouv.fr/contenu/Media/files/lexique-api-lgf.docx
def parse_alineas(
    element_flow_: ElementFlow,
) -> Iterator[Element]:
    element_flow = list(element_flow_)
    while element_flow:
        element_or_text_segments = element_flow.pop(0)
        if isinstance(element_or_text_segments, Element):
            contents: List[Element | TextSegments] = [element_or_text_segments]
            if element_or_text_segments.name == "table":
                while (
                    element_flow
                    and isinstance(element_flow[0], Element)
                    and element_flow[0].name == "table_description"
                ):
                    contents.append(element_flow.pop(0))

            yield Element(
                name="alinea",
                contents=contents,
            )
        else:
            for line in element_or_text_segments:
                yield Element(name="alinea", contents=[[line]])


def render_alinea(
    soup: BeautifulSoup,
    element: Element,
    alinea_number: int,
) -> Tag:
    contents: List[PageElementOrString] = []
    for element_or_text_segments in element.contents:
        if isinstance(element_or_text_segments, Element):
            contents.extend(render_basic_elements(soup, element_or_text_segments))
        else:
            assert (
                len(element_or_text_segments) == 1
            ), "Alinea element should contain exactly one TextSegments"
            contents.extend(_parse_inline_quotes(soup, element_or_text_segments[0].contents))

    return make_data_tag(
        soup,
        ALINEA_SCHEMA,
        data=dict(number=str(alinea_number)),
        contents=contents,
    )
