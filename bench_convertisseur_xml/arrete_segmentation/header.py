import re
from typing import List, cast, Callable, Literal
from enum import Enum

from bs4 import Tag, BeautifulSoup

from .sentence_rules import (
    is_arrete, is_entity, is_liste, is_motif, is_visa, VISA_PATTERN, MOTIF_PATTERN, LIST_PATTERN
)
from .config import (
    SERVICE_AND_REFERENCE_PATTERN, BodySection
)
from .parse_section import parse_section
from .parse_list import parse_list, clean_bullet_list, list_indentation
from bench_convertisseur_xml.utils.html import make_data_tag, PageElementOrString, wrap_in_tag, make_new_tag
from bench_convertisseur_xml.regex_utils import split_string_with_regex, merge_matches_with_siblings
from bench_convertisseur_xml.html_schemas import ENTITY_SCHEMA, IDENTIFICATION_SCHEMA, VISA_SCHEMA, MOTIF_SCHEMA
from bench_convertisseur_xml.types import DataElementSchema


def _is_body_section(line: str, authorized_sections) -> bool:
    new_section_info = parse_section(line, authorized_sections=authorized_sections)
    return new_section_info['type'] in {BodySection.TITLE, BodySection.CHAPTER, BodySection.ARTICLE, BodySection.SUB_ARTICLE}


def _process_identification_pile(pile: List[str]):
    return [" ".join(pile)]


def _process_entity_pile(pile: List[str]) -> List[str]:
    # Combine all lines of current pile
    entity_line = " ".join(pile)

    # Split by entity names
    return cast(List[str], list(merge_matches_with_siblings(split_string_with_regex(
        SERVICE_AND_REFERENCE_PATTERN,
        entity_line,
    ), 'following')))


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
        # Multi-line entity
        pile.append(lines.pop(0))

    pile = _process_entity_pile(pile)

    header.append(
        make_data_tag(soup, ENTITY_SCHEMA, contents=wrap_in_tag(soup, pile, 'div'))
    )
    
    # -------- Identification
    pile = []
    while True:
        if is_arrete(lines[0]):
            pile.append(lines.pop(0))
        # Discard entity in subsection identification
        elif is_entity(lines[0]):
            lines.pop(0)
        elif VISA_PATTERN.match(lines[0]) or MOTIF_PATTERN.match(lines[0]) or _is_body_section(lines[0], authorized_sections):
            break
        # Multi-line identification
        else:
            pile.append(lines.pop(0))

    # Specific process for the identification
    pile = _process_identification_pile(pile)

    header.append(make_data_tag(soup, IDENTIFICATION_SCHEMA, contents=wrap_in_tag(soup, pile, 'h1')))

    # -------- Visas and motifs
    def _is_header_end(line: str):
        return is_arrete(line) or _is_body_section(line, authorized_sections)
    
    while (
        not is_visa(lines[0])
        and not is_motif(lines[0])
        and not _is_header_end(lines[0])
    ):
        header.append(make_new_tag(soup, 'div', contents=[lines.pop(0)]))

    if is_visa(lines[0]):
        lines = _parse_visas_or_motifs(
            soup, 
            header, 
            lines, 
            VISA_PATTERN, 
            VISA_SCHEMA, 
            lambda line : is_motif(line) or _is_header_end(line),
        )

    while (
        not is_motif(lines[0])
        and not _is_header_end(lines[0])
    ):
        header.append(make_new_tag(soup, 'div', contents=[lines.pop(0)]))
    
    if is_motif(lines[0]):
        lines = _parse_visas_or_motifs(
            soup, 
            header, 
            lines, 
            MOTIF_PATTERN, 
            MOTIF_SCHEMA, 
            lambda line : _is_header_end(line),
        )

    return lines


def _parse_visas_or_motifs(
    soup: BeautifulSoup, 
    header: Tag, 
    lines: List[str],
    section_pattern: re.Pattern,
    section_schema: DataElementSchema,
    is_next_section: Callable[[str], bool],
):
    pile: List[PageElementOrString]
    has_more = bool(section_pattern.match(lines[0]))
    # simple : "Vu blabla" ou "- vu blabla"
    # bullet_list : "- vu blabla" ou "Vu \n - blabla"
    # list : "Vu:\n blabla"
    flavor: Literal['simple', 'bullet_list', 'list'] | None = None

    section_match = section_pattern.match(lines[0])
    if section_match and section_match.group('contents'):
        flavor = 'simple'
    else:
        # Add the "Vu :" to the header
        header.append(make_new_tag(soup, 'div', contents=[lines.pop(0)]))
        if is_liste(lines[0]):
            flavor = 'bullet_list'
        else:
            flavor = 'list'

    has_more = True
    if flavor == 'simple':
        while has_more:
            pile = [lines.pop(0)]
            while True:
                if is_liste(lines[0]) and not section_pattern.match(lines[0]):
                    lines, ul_element = parse_list(soup, lines)
                    pile.append(ul_element)
                else:
                    break
            header.append(make_data_tag(soup, section_schema, contents=pile))

            # Consume lines until we find the next visa, or the beginning of the next section
            while True:
                if section_pattern.match(lines[0]):
                    break
                elif is_next_section(lines[0]):
                    has_more = False
                    break
                else:
                    header.append(make_new_tag(soup, 'div', contents=[lines.pop(0)]))

    elif flavor == 'list':
        while has_more:
            pile = [lines.pop(0)]
            while True:
                if is_liste(lines[0]):
                    lines, ul_element = parse_list(soup, lines)
                    pile.append(ul_element)
                else:
                    break
            header.append(make_data_tag(soup, section_schema, contents=pile))

            # Consume lines until we find the next visa, or the beginning of the next section
            if is_next_section(lines[0]):
                has_more = False

    elif flavor == 'bullet_list':
        indentation_0 = list_indentation(lines[0])
        while has_more:
            pile = [lines.pop(0)]
            while True:
                if is_liste(lines[0]) and list_indentation(lines[0]) > indentation_0:
                    lines, ul_element = parse_list(soup, lines)
                    pile.append(ul_element)
                else:
                    break
            header.append(make_data_tag(soup, section_schema, contents=pile))

            # Consume lines until we find the next visa, or the beginning of the next section
            while True:
                if is_next_section(lines[0]):
                    has_more = False
                    break
                elif is_liste(lines[0]):
                    break
                else:
                    header.append(make_new_tag(soup, 'div', contents=[lines.pop(0)]))

    return lines