from bs4 import Tag, BeautifulSoup

from arretify.parsing_utils.source_mapping import TextSegments
from .header_elements import (
    parse_header_beginning,
    parse_emblem_element,
    parse_entity_element,
    parse_identification_element,
    parse_arrete_title_element,
    parse_honorary_element,
    parse_visa_element,
    parse_motif_element,
    parse_supplementary_motif_info_element,
)
from .section_titles import is_body_section


def parse_header(
    soup: BeautifulSoup,
    header: Tag,
    lines: TextSegments,
) -> TextSegments:
    # Add lines until we find first meaningful line
    lines = parse_header_beginning(soup, header, lines)

    while lines and not is_body_section(lines[0].contents):

        # Emblem
        lines = parse_emblem_element(soup, header, lines)

        # Entity
        lines = parse_entity_element(soup, header, lines)

        # Identification
        lines = parse_identification_element(soup, header, lines)

        # Arrete title
        lines = parse_arrete_title_element(soup, header, lines)

        # Honorary
        lines = parse_honorary_element(soup, header, lines)

        # Visas
        lines = parse_visa_element(soup, header, lines)

        # Motifs
        lines = parse_motif_element(soup, header, lines)

        # Supplementary motif info
        lines = parse_supplementary_motif_info_element(soup, header, lines)

    return lines
