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
from bs4 import Tag, BeautifulSoup

from arretify.parsing_utils.source_mapping import TextSegments
from .document_elements import (
    is_document_element,
    parse_document_elements,
)
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
from .titles_detection import is_title


def parse_header(
    soup: BeautifulSoup,
    header: Tag,
    lines: TextSegments,
) -> TextSegments:
    # Add lines until we find first meaningful line
    lines = parse_header_beginning(soup, header, lines)

    while lines and not is_title(lines[0].contents):

        # Document elements
        lines = parse_document_elements(soup, header, lines)

        while lines and not (is_title(lines[0].contents) or is_document_element(lines[0].contents)):

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
