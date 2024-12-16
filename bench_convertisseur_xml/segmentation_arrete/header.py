from typing import List
from enum import Enum

from bs4 import Tag, BeautifulSoup

from .sentence_rules import (
    is_arrete, is_continuing_sentence, is_entity, is_liste, is_motif, is_not_information,
    is_visa
)
from .config import BodySection, HeaderSection, section_from_name
from .parse_section import parse_section
from bench_convertisseur_xml.utils.markdown import clean_markdown
from bench_convertisseur_xml.utils.html import make_element, PageElementOrString, wrap_in_paragraphs
from bench_convertisseur_xml.html_schemas import DIV_SCHEMA, ENTITY_SCHEMA, IDENTIFICATION_SCHEMA, VISA_SCHEMA, MOTIFS_SCHEMA, PARAGRAPH_SCHEMA


def _ensure_ul_element(soup: BeautifulSoup, container: PageElementOrString | str, string: str):
    if not isinstance(container, Tag):
        ul = soup.new_tag('ul')
        li = soup.new_tag('li')
        li.append(container)
        ul.append(li)
    else:
        ul = container
    li = soup.new_tag('li')
    li.append(string)
    ul.append(li)
    return ul


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
        make_element(soup, ENTITY_SCHEMA, contents=wrap_in_paragraphs(soup, pile))
    )
    
    # -------- Identification
    pile = []
    while True:
        if is_arrete(lines[0]) or is_continuing_sentence(lines[0]):
            pile.append(lines.pop(0))
        # Discard entity in subsection identification
        elif is_entity(lines[0]):
            lines.pop(0)
        # Multi-line identification
        elif is_visa(lines[0]) or is_motif(lines[0]) or _is_body_section(lines[0], authorized_sections):
            break
        else:
            pile.append(lines.pop(0))

    header.append(make_element(soup, IDENTIFICATION_SCHEMA, contents=wrap_in_paragraphs(soup, pile)))

    # -------- Visas
    pile = []
    while True:
        if is_visa(lines[0]):
            pile.append(lines.pop(0))
        elif is_continuing_sentence(lines[0]):
            # TODO : Improve code for lists
            if isinstance(pile[-1], str):
                pile[-1] = pile[-1] + ' ' + lines.pop(0)
            else:
                pile[-1].append(lines.pop(0))
        elif is_liste(lines[0]):
            pile[-1] = _ensure_ul_element(soup, pile[-1], lines.pop(0))
        elif is_motif(lines[0]) or is_arrete(lines[0]) or _is_body_section(lines[0], authorized_sections):
            break
        else:
            raise RuntimeError(f'Unexpected line : {lines[0]}')
    header.append(make_element(soup, VISA_SCHEMA, contents=wrap_in_paragraphs(soup, pile)))
        
    # -------- Motifs
    pile = []
    while True:
        if is_motif(lines[0]):
            pile.append(lines.pop(0))
        elif is_continuing_sentence(lines[0]):
            # TODO : Improve code for lists
            if isinstance(pile[-1], str):
                pile[-1] = pile[-1] + ' ' + lines.pop(0)
            else:
                pile[-1].append(lines.pop(0))
        elif is_liste(lines[0]):
            pile[-1] = _ensure_ul_element(soup, pile[-1], lines.pop(0))
        elif is_arrete(lines[0]) or _is_body_section(lines[0], authorized_sections):
            break
        else:
            raise RuntimeError(f'Unexpected line : {lines[0]}')
    header.append(make_element(soup, MOTIFS_SCHEMA, contents=wrap_in_paragraphs(soup, pile)))

    return lines