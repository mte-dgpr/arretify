import re
from typing import List, cast, Callable, Literal
from enum import Enum

from bs4 import Tag, BeautifulSoup

from .sentence_rules import (
    is_arrete, is_entity, is_liste, is_motif, is_visa, VISA_PATTERN, MOTIF_PATTERN, LIST_PATTERN
)
from .config import (
    SERVICE_PATTERNS, REFERENCE_PATTERNS, BodySection
)
from .parse_section_info import parse_section_info, AuthorizedSections
from .parse_basic_elements import parse_list, list_indentation
from bench_convertisseur_xml.utils.html import make_data_tag, PageElementOrString, wrap_in_tag, make_new_tag
from bench_convertisseur_xml.regex_utils import split_string_with_regex, merge_matches_with_siblings, join_with_or, PatternProxy
from bench_convertisseur_xml.html_schemas import ENTITY_SCHEMA, IDENTIFICATION_SCHEMA, VISA_SCHEMA, MOTIF_SCHEMA
from bench_convertisseur_xml.types import DataElementSchema
from bench_convertisseur_xml.parsing_utils.source_mapping import TextSegments, TextSegment


SERVICE_AND_REFERENCE_PATTERN = PatternProxy(
    join_with_or(SERVICE_PATTERNS + REFERENCE_PATTERNS),
)

def _is_body_section(line: TextSegment, authorized_sections) -> bool:
    new_section_info = parse_section_info(line, authorized_sections=authorized_sections)
    return new_section_info['type'] in {BodySection.TITLE, BodySection.CHAPTER, BodySection.ARTICLE, BodySection.SUB_ARTICLE}


def _process_identification_pile(pile: List[str]):
    return [" ".join(pile)]


def _process_entity_pile(pile: List[str]) -> List[PageElementOrString]:
    # Combine all lines of current pile
    entity_line = " ".join(pile)

    # Split by entity names
    return list(
        merge_matches_with_siblings(
            split_string_with_regex(
                SERVICE_AND_REFERENCE_PATTERN,
                entity_line,
            ), 'following'
        )
    )


def parse_header(
    soup: BeautifulSoup, 
    header: Tag, 
    lines: TextSegments, 
    authorized_sections: AuthorizedSections
) -> TextSegments:
    pile: List[PageElementOrString] = []
    string_pile: List[str] = []

    # Find the first entity line
    while not is_entity(lines[0].contents):
        lines.pop(0)

    # -------- Entity
    string_pile = []
    while True:
        if is_arrete(lines[0].contents):
            break
        # Multi-line entity
        string_pile.append(lines.pop(0).contents)

    header.append(
        make_data_tag(
            soup, 
            ENTITY_SCHEMA, 
            contents=wrap_in_tag(
                soup, 
                _process_entity_pile(string_pile), 
                'div'
            )
        )
    )
    
    # -------- Identification
    string_pile = []
    while True:
        if is_arrete(lines[0].contents):
            string_pile.append(lines.pop(0).contents)
        # Discard entity in subsection identification
        elif is_entity(lines[0].contents):
            lines.pop(0)
        elif (
            VISA_PATTERN.match(lines[0].contents) 
            or MOTIF_PATTERN.match(lines[0].contents) 
            or _is_body_section(lines[0], authorized_sections)
        ):
            break
        # Multi-line identification
        else:
            string_pile.append(lines.pop(0).contents)

    # Specific process for the identification
    header.append(
        make_data_tag(
            soup, 
            IDENTIFICATION_SCHEMA, 
            contents=wrap_in_tag(
                soup, 
                _process_identification_pile(string_pile), 
                'h1'
            )
        )
    )

    # -------- Visas and motifs
    def _is_header_end(line: TextSegment):
        return is_arrete(line.contents) or _is_body_section(line, authorized_sections)
    
    while (
        not is_visa(lines[0].contents)
        and not is_motif(lines[0].contents)
        and not _is_header_end(lines[0])
    ):
        header.append(
            _wrap_in_div(soup, [lines.pop(0)])
        )

    if is_visa(lines[0].contents):
        lines = _parse_visas_or_motifs(
            soup, 
            header, 
            lines,
            VISA_PATTERN, 
            VISA_SCHEMA, 
            lambda line : is_motif(line.contents) or _is_header_end(line),
        )

    while (
        not is_motif(lines[0].contents)
        and not _is_header_end(lines[0])
    ):
        header.append(_wrap_in_div(soup, [lines.pop(0)]))
    
    if is_motif(lines[0].contents):
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
    lines: TextSegments,
    section_pattern: PatternProxy,
    section_schema: DataElementSchema,
    is_next_section: Callable[[TextSegment], bool],
):
    pile: List[PageElementOrString]
    has_more = bool(section_pattern.match(lines[0].contents))
    # simple : "Vu blabla" ou "- vu blabla"
    # bullet_list : "- vu blabla" ou "Vu \n - blabla"
    # list : "Vu:\n blabla"
    flavor: Literal['simple', 'bullet_list', 'list'] | None = None

    section_match = section_pattern.match(lines[0].contents)
    if section_match and section_match.group('contents'):
        flavor = 'simple'
    else:
        # Add the "Vu :" to the header
        header.append(_wrap_in_div(soup, [lines.pop(0)]))
        if is_liste(lines[0].contents):
            flavor = 'bullet_list'
        else:
            flavor = 'list'

    has_more = True
    if flavor == 'simple':
        while has_more:
            pile = [lines.pop(0).contents]
            while True:
                if is_liste(lines[0].contents) and not section_pattern.match(lines[0].contents):
                    lines, ul_element = parse_list(soup, lines)
                    pile.append(ul_element)
                else:
                    break
            header.append(make_data_tag(soup, section_schema, contents=pile))

            # Consume lines until we find the next visa, or the beginning of the next section
            while True:
                if section_pattern.match(lines[0].contents):
                    break
                elif is_next_section(lines[0]):
                    has_more = False
                    break
                else:
                    header.append(_wrap_in_div(soup, [lines.pop(0)]))

    elif flavor == 'list':
        while has_more:
            pile = [lines.pop(0).contents]
            while True:
                if is_liste(lines[0].contents):
                    lines, ul_element = parse_list(soup, lines)
                    pile.append(ul_element)
                else:
                    break
            header.append(make_data_tag(soup, section_schema, contents=pile))

            # Consume lines until we find the next visa, or the beginning of the next section
            if is_next_section(lines[0]):
                has_more = False

    elif flavor == 'bullet_list':
        indentation_0 = list_indentation(lines[0].contents)
        while has_more:
            pile = [lines.pop(0).contents]
            while True:
                if is_liste(lines[0].contents) and list_indentation(lines[0].contents) > indentation_0:
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
                elif is_liste(lines[0].contents):
                    break
                else:
                    header.append(_wrap_in_div(soup, [lines.pop(0)]))

    return lines


def _wrap_in_div(soup: BeautifulSoup, lines: TextSegments):
    return make_new_tag(soup, 'div', contents=[line.contents for line in lines])