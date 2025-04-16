from typing import List, Optional

from bs4 import BeautifulSoup, Tag

from arretify.settings import LOGGER
from arretify.utils.html import make_data_tag
from arretify.html_schemas import (
    SECTION_SCHEMA,
    SECTION_TITLE_SCHEMAS,
    ALINEA_SCHEMA,
    ERROR_SCHEMA,
)
from arretify.errors import ErrorCodes
from arretify.parsing_utils.source_mapping import (
    TextSegments,
)
from .types import GroupParsingContext
from .basic_elements import parse_basic_elements
from .section_titles import (
    is_body_section,
    parse_section_info,
    are_sections_contiguous,
)
from .appendix import is_appendix_title


def parse_main_content(soup: BeautifulSoup, main_content: Tag, lines: TextSegments):
    # Ancestry order from root to the current section in the parsing context
    body_sections: List[Tag] = [main_content]

    # Consume lines until we detect the first section
    while not is_body_section(lines[0].contents):
        # TODO-PROCESS-TAG
        lines.pop(0)

    # Parse one section at a time
    current_levels: Optional[List[int]] = None
    current_level = len(body_sections) - 2

    while lines and not is_appendix_title(lines[0].contents):

        section_info = parse_section_info(lines[0].contents)

        section_element = make_data_tag(
            soup,
            SECTION_SCHEMA,
            data=dict(
                type=section_info.type.value,
                number=section_info.number,
                title=section_info.text,
            ),
        )
        new_levels = section_info.levels

        # Process ancestry for new section
        new_level = len(new_levels) - 1 if new_levels else -1

        if new_level - current_level >= 1:
            # Nothing to do we just add the new section below the existing one
            pass
        elif new_level - current_level <= 0:
            # Empty the ancestry tree until we reach the right ancestor
            while new_level - current_level <= 0:
                body_sections.pop()
                current_level = len(body_sections) - 2
        else:
            raise RuntimeError(
                f"unexpected title {lines[0].contents}, current level {len(body_sections)}"
            )

        body_sections[-1].append(section_element)
        body_sections.append(section_element)

        current_level = len(body_sections) - 2

        # Add a tag if the sections are not contiguous
        title_contents = lines.pop(0).contents

        if not are_sections_contiguous(current_levels, new_levels):
            LOGGER.warn(
                f"Detected title of levels {new_levels} after title of levels {current_levels}"
            )
            error_element = make_data_tag(
                soup,
                ERROR_SCHEMA,
                data=dict(error_code=ErrorCodes.non_contiguous_sections.value),
                contents=[title_contents],
            )
            section_element.append(error_element)
        else:
            title_element = make_data_tag(
                soup,
                SECTION_TITLE_SCHEMAS[new_level],
                contents=[title_contents],
            )
            section_element.append(title_element)

        current_levels = new_levels

        # Parse alineas until a new section is detected.
        # ALINEA : "Constitue un alinéa toute phrase, tout mot, tout ensemble de phrases
        # ou de mots commençant à la ligne, précédés ou non d’un tiret, d’un point,
        # d’une numérotation ou de guillemets, sans qu’il y ait lieu d’établir des distinctions
        # selon la nature du signe placé à la fin de la ligne précédente
        # (point, deux-points ou point-virgule).
        # Un tableau constitue un seul alinéa (définition complète dans le guide de légistique)."
        # REF : https://www.legifrance.gouv.fr/contenu/Media/files/lexique-api-lgf.docx
        section_context = GroupParsingContext(alinea_count=0)

        while lines and not (
            is_body_section(lines[0].contents) or is_appendix_title(lines[0].contents)
        ):
            section_context.alinea_count += 1
            alinea_element = make_data_tag(
                soup,
                ALINEA_SCHEMA,
                data=dict(number=str(section_context.alinea_count)),
            )
            section_element.append(alinea_element)
            parse_basic_elements(soup, alinea_element, lines)

    return lines
