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
from typing import Dict, List, Optional
import logging

from bs4 import (
    BeautifulSoup,
    Tag,
)

from arretify.types import SectionType
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
from .basic_elements import parse_basic_elements
from .document_elements import (
    is_document_element,
    parse_document_elements,
)
from .titles_detection import (
    is_title,
    parse_title_info,
    is_next_title,
)


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
        title_element_data: Dict[str, str | None] = dict()

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

            # Parse alineas until a new section is detected
            # ALINEA : "Constitue un alinéa toute phrase, tout mot, tout ensemble de phrases ou de
            # mots commençant à la ligne, précédés ou non d’un tiret, d’un point, d’une
            # numérotation ou de guillemets, sans qu’il y ait lieu d’établir des distinctions selon
            # la nature du signe placé à la fin de la ligne précédente (point, deux-points ou
            # point-virgule). Un tableau constitue un seul alinéa (définition complète dans le
            # guide de légistique)."
            # REF : https://www.legifrance.gouv.fr/contenu/Media/files/lexique-api-lgf.docx
            while lines and not (
                is_title(lines[0].contents) or is_document_element(lines[0].contents)
            ):
                alinea_count += 1
                alinea_element = make_data_tag(
                    soup,
                    ALINEA_SCHEMA,
                    data=dict(number=str(alinea_count)),
                )
                section_element.append(alinea_element)
                parse_basic_elements(soup, alinea_element, lines)

    return lines


def _get_downstream_sections_types(section_type):
    ordered_sections_types = [section_type for section_type in SectionType]
    section_index = ordered_sections_types.index(section_type)
    return ordered_sections_types[section_index + 1 :]
