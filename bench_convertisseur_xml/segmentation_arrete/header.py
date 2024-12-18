from typing import List
from enum import Enum

from bs4 import Tag, BeautifulSoup

from .sentence_rules import (
    is_arrete, is_entity, is_liste, is_motif,
    is_visa
)
from .config import BodySection, HeaderSection, section_from_name
from .parse_section import parse_section
from .parse_list import parse_list
from bench_convertisseur_xml.utils.html import make_data_tag, PageElementOrString, wrap_in_paragraphs, make_new_tag
from bench_convertisseur_xml.html_schemas import ENTITY_SCHEMA, IDENTIFICATION_SCHEMA, VISA_SCHEMA, MOTIFS_SCHEMA


def _is_body_section(line: str, authorized_sections) -> bool:
    new_section_info = parse_section(line, authorized_sections=authorized_sections)
    return new_section_info['type'] in {BodySection.TITLE, BodySection.CHAPTER, BodySection.ARTICLE, BodySection.SUB_ARTICLE}


def parse_header(soup: BeautifulSoup, header: Tag, lines: List[str], authorized_sections):
    pile: List[PageElementOrString] = []

    # Find the first entity line
    while not is_entity(lines[0]):
        lines.pop(0)

    # -------- Entity
    pile = []
    while True:
        if is_arrete(lines[0]):
            break
        else:
            pile.append(lines.pop(0))
    header.append(
        make_data_tag(soup, ENTITY_SCHEMA, contents=wrap_in_paragraphs(soup, pile))
    )
    
    # -------- Identification
    pile = []
    while True:
        if is_arrete(lines[0]):
            pile.append(lines.pop(0))
        # Discard entity in subsection identification
        elif is_entity(lines[0]):
            lines.pop(0)
        # Multi-line identification
        elif is_visa(lines[0]) or is_motif(lines[0]) or _is_body_section(lines[0], authorized_sections):
            break
        else:
            pile.append(lines.pop(0))

    header.append(make_data_tag(soup, IDENTIFICATION_SCHEMA, contents=wrap_in_paragraphs(soup, pile)))

    # -------- Visas
    while is_visa(lines[0]):
        pile = [lines.pop(0)]
        while True:
            if is_liste(lines[0]):
                lines, ul_element = parse_list(soup, lines)
                pile.append(ul_element)
            else:
                break
        header.append(make_data_tag(soup, VISA_SCHEMA, contents=pile))

        # Consume lines until we find the next visa, or the beginning of the next section
        while not is_visa(lines[0]):
            if is_motif(lines[0]) or is_arrete(lines[0]) or _is_body_section(lines[0], authorized_sections):
                break
            else:
                header.append(make_new_tag(soup, 'div', contents=[lines.pop(0)]))
        
    # -------- Motifs
    while is_motif(lines[0]):
        pile = [lines.pop(0)]
        while True:
            if is_liste(lines[0]):
                lines, ul_element = parse_list(soup, lines)
                pile.append(ul_element)
            else:
                break
        header.append(make_data_tag(soup, MOTIFS_SCHEMA, contents=pile))

        while not is_motif(lines[0]):
            if is_arrete(lines[0]) or _is_body_section(lines[0], authorized_sections):
                break
            else:
                header.append(make_new_tag(soup, 'div', contents=[lines.pop(0)]))

    return lines