from typing import List
from enum import Enum
from dataclasses import dataclass

from bs4 import Tag, BeautifulSoup

from .sentence_rules import (
    is_arrete, is_entity, is_liste, 
    is_table_description, is_line_with_semicolumn
)
from bench_convertisseur_xml.utils.html import make_data_tag, PageElementOrString, wrap_in_tag
from bench_convertisseur_xml.utils.markdown import parse_markdown_table, is_table_line
from bench_convertisseur_xml.html_schemas import (
    SECTION_SCHEMA, SECTION_TITLE_SCHEMAS, ALINEA_SCHEMA
)
from bench_convertisseur_xml.parsing_utils.source_mapping import TextSegments
from .config import BodySection
from .parse_section_info import parse_section_info
from .parse_basic_elements import parse_basic_elements
from .sentence_rules import is_blockquote_start


@dataclass
class _SectionParsingContext:
    alinea_count: int


def parse_main_content(soup: BeautifulSoup, main_content: Tag, lines: TextSegments, authorized_sections):
    pile: List[PageElementOrString] = []
    body_sections: List[Tag] = [main_content]

    # Consume lines until we detect the first section
    while lines:
        section_info = parse_section_info(lines[0], authorized_sections=authorized_sections)
        if section_info['type'] == BodySection.NONE:
            lines.pop(0)
            continue
        else:
            break

    while lines:
        section_info = parse_section_info(lines[0], authorized_sections=authorized_sections)
        section_element = make_data_tag(soup, SECTION_SCHEMA, data=dict(
            type=section_info['type'].value,
            number=section_info["number"],
            title=section_info["text"],
        ))

        new_section_level = section_info["level"]
        if new_section_level - (len(body_sections) - 2) >= 1:
            # Nothing to do we just add the new section below the existing one
            pass
        elif new_section_level - (len(body_sections) - 2) <= 0:
            while new_section_level - (len(body_sections) - 2) <= 0:
                body_sections.pop()
        else:
            raise RuntimeError(f'unexpected title {section_info}, current level {len(body_sections)}')

        section_context = _SectionParsingContext(alinea_count=0)

        body_sections[-1].append(section_element)
        body_sections.append(section_element)

        title_element = make_data_tag(
            soup, 
            SECTION_TITLE_SCHEMAS[new_section_level], 
            contents=[lines.pop(0).contents]
        )
        section_element.append(title_element)

        # Parse alineas until a new section is detected.
        # ALINEA : "Constitue un alinéa toute phrase, tout mot, tout ensemble de phrases 
        # ou de mots commençant à la ligne, précédés ou non d’un tiret, d’un point, 
        # d’une numérotation ou de guillemets, sans qu’il y ait lieu d’établir des distinctions 
        # selon la nature du signe placé à la fin de la ligne précédente (point, deux-points ou point-virgule). 
        # Un tableau constitue un seul alinéa (définition complète dans le guide de légistique)."
        # REF : https://www.legifrance.gouv.fr/contenu/Media/files/lexique-api-lgf.docx
        while lines:
            section_info = parse_section_info(lines[0], authorized_sections=authorized_sections)
            if section_info['type'] != BodySection.NONE:
                break

            section_context.alinea_count += 1
            alinea_element = make_data_tag(
                soup, 
                ALINEA_SCHEMA, 
                data=dict(number=str(section_context.alinea_count))
            )
            section_element.append(alinea_element)
            parse_basic_elements(soup, alinea_element, lines)