from typing import List
from enum import Enum

from bs4 import Tag, BeautifulSoup

from .sentence_rules import (
    is_arrete, is_continuing_sentence, is_entity, is_liste, is_motif, is_not_information, is_table,
    is_visa
)
from .config import BodySection, HeaderSection, section_from_name
from .utils import clean_markdown
from .parse_section import parse_section
from bench_convertisseur_xml.utils.html import make_element, PageElementOrString
from bench_convertisseur_xml.types import ElementSchema

HEADER_SCHEMA = ElementSchema(
    name="header",
    tag_name="header",
    classes=["dsr-header"],
    data_keys=[],
)

DIV_SCHEMA = ElementSchema(
    name="div",
    tag_name="div",
    classes=[],
    data_keys=[],
)

ENTITY_SCHEMA = ElementSchema(
    name="entity",
    tag_name="div",
    classes=["dsr-entity"],
    data_keys=[],
)

IDENTIFICATION_SCHEMA = ElementSchema(
    name="identification",
    tag_name="div",
    classes=["dsr-identification"],
    data_keys=[],
)

VISA_SCHEMA = ElementSchema(
    name="visa",
    tag_name="div",
    classes=["dsr-visa"],
    data_keys=[],
)

MOTIFS_SCHEMA = ElementSchema(
    name="motifs",
    tag_name="div",
    classes=["dsr-motifs"],
    data_keys=[],
)


def _process_pile(soup: BeautifulSoup, pile: List[str]):
    """Traite la pile de lignes et les ajoute à la section XML"""
    # Si la ligne n'est pas vide
    return [
        make_element(soup, DIV_SCHEMA, contents=[line]) if isinstance(line, str) else line
        for line in pile if (not isinstance(line, str) or line.strip())
    ]


def _ensure_ul_element(soup: BeautifulSoup, container: Tag | str, string: str):
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


def _is_body_section(line: str, authorized_sections):
    new_section_info = parse_section(line, authorized_sections=authorized_sections)
    new_section_name = new_section_info["section_name"]
    new_section_type = section_from_name(new_section_name)
    new_section_type not in {BodySection.TITLE, BodySection.CHAPTER, BodySection.ARTICLE, BodySection.SUB_ARTICLE}


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
        make_element(soup, ENTITY_SCHEMA, contents=_process_pile(soup, pile))
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
        elif is_continuing_sentence(lines[0]):
            pile.append(lines.pop(0))
        elif is_visa(lines[0]) or is_motif(lines[0]):
            break
        else:
            raise RuntimeError(f'Unexpected line : {lines[0]}')
    header.append(make_element(soup, IDENTIFICATION_SCHEMA, contents=_process_pile(soup, pile)))

    # -------- Visas
    pile = []
    while True:
        if is_visa(lines[0]):
            pile.append(lines.pop(0))
        elif is_continuing_sentence(lines[0]):
            pile[-1] = pile[-1] + ' ' + lines.pop(0)
        elif is_liste(lines[0]):
            pile[-1] = _ensure_ul_element(soup, pile[-1], lines.pop(0))
        elif is_motif(lines[0]) or is_arrete(lines[0]) or _is_body_section(lines[0], authorized_sections):
            break
        else:
            raise RuntimeError(f'Unexpected line : {lines[0]}')
    header.append(make_element(soup, VISA_SCHEMA, contents=_process_pile(soup, pile)))
        
    # -------- Motifs
    pile = []
    while True:
        if is_motif(lines[0]):
            pile.append(lines.pop(0))
        elif is_continuing_sentence(lines[0]):
            pile[-1] = pile[-1] + ' ' + lines.pop(0)
        elif is_liste(lines[0]):
            pile[-1] = _ensure_ul_element(soup, pile[-1], lines.pop(0))
        elif is_arrete(lines[0]) or _is_body_section(lines[0], authorized_sections):
            break
        else:
            raise RuntimeError(f'Unexpected line : {lines[0]}')
    header.append(make_element(soup, MOTIFS_SCHEMA, contents=_process_pile(soup, pile)))

    return lines