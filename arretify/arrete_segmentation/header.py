from typing import List, Callable, Literal

from bs4 import Tag, BeautifulSoup

from arretify.utils.html import (
    make_data_tag,
    PageElementOrString,
    wrap_in_tag,
    make_new_tag,
)
from arretify.regex_utils import (
    split_string_with_regex,
    merge_matches_with_siblings,
    PatternProxy,
)
from arretify.html_schemas import (
    ENTITY_SCHEMA,
    IDENTIFICATION_SCHEMA,
    VISA_SCHEMA,
    MOTIF_SCHEMA,
)
from arretify.types import DataElementSchema
from arretify.parsing_utils.source_mapping import (
    TextSegments,
    TextSegment,
)
from .sentence_rules import (
    is_arrete,
    is_entity,
    is_liste,
    is_motif,
    is_visa,
    VISA_PATTERN,
    MOTIF_PATTERN,
    SERVICES_PATTERN,
)
from .section_rules import is_body_section
from .basic_elements import parse_list, list_indentation


def _process_identification_pile(
    pile: List[str],
) -> List[PageElementOrString]:
    return [" ".join(pile)]


def _process_entity_pile(
    pile: List[str],
) -> List[PageElementOrString]:
    # Combine all lines of current pile
    entity_line = " ".join(pile)

    # Split by entity names
    return list(
        merge_matches_with_siblings(
            split_string_with_regex(
                SERVICES_PATTERN,
                entity_line,
            ),
            "following",
        )
    )


def parse_header(
    soup: BeautifulSoup,
    header: Tag,
    lines: TextSegments,
) -> TextSegments:
    string_pile: List[str] = []

    # Find the first useful line
    while not (
        is_entity(lines[0].contents)
        or is_arrete(lines[0].contents)
        or is_visa(lines[0].contents)
        or is_motif(lines[0].contents)
        or is_body_section(lines[0].contents)
    ):
        # TODO-PROCESS-TAG
        # Here we could deal with cases such as Rapport d'inspection, Lettre de décision...
        lines.pop(0)

    # -------- Entity
    string_pile = []
    while not (
        is_arrete(lines[0].contents)
        or is_visa(lines[0].contents)
        or is_motif(lines[0].contents)
        or is_body_section(lines[0].contents)
    ):
        string_pile.append(lines.pop(0).contents)

    header.append(
        make_data_tag(
            soup,
            ENTITY_SCHEMA,
            contents=wrap_in_tag(soup, _process_entity_pile(string_pile), "div"),
        )
    )

    # -------- Identification
    string_pile = []
    while not (
        is_visa(lines[0].contents)
        or is_motif(lines[0].contents)
        or is_body_section(lines[0].contents)
    ):
        # Discard entity in subsection identification
        if is_entity(lines[0].contents):
            # TODO-PROCESS-TAG
            lines.pop(0)
        else:
            string_pile.append(lines.pop(0).contents)

    header.append(
        make_data_tag(
            soup,
            IDENTIFICATION_SCHEMA,
            contents=wrap_in_tag(soup, _process_identification_pile(string_pile), "h1"),
        )
    )

    # -------- Visas and motifs
    def _is_header_end(line: TextSegment):
        return is_arrete(line.contents) or is_body_section(line.contents)

    # Add lines until we find first visa
    while (
        not is_visa(lines[0].contents)
        and not is_motif(lines[0].contents)
        and not _is_header_end(lines[0])
    ):
        header.append(_wrap_in_div(soup, [lines.pop(0)]))

    # Start visas parsing
    if is_visa(lines[0].contents):
        lines = _parse_visas_or_motifs(
            soup,
            header,
            lines,
            VISA_PATTERN,
            VISA_SCHEMA,
            lambda line: is_motif(line.contents) or _is_header_end(line),
        )

    # Add lines until we find first motif
    while not is_motif(lines[0].contents) and not _is_header_end(lines[0]):
        header.append(_wrap_in_div(soup, [lines.pop(0)]))

    # Start motifs parsing
    if is_motif(lines[0].contents):
        lines = _parse_visas_or_motifs(
            soup,
            header,
            lines,
            MOTIF_PATTERN,
            MOTIF_SCHEMA,
            _is_header_end,
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
    flavor: Literal["simple", "bullet_list", "list"] | None = None

    section_match = section_pattern.match(lines[0].contents)
    if section_match and section_match.group("contents"):
        flavor = "simple"
    else:
        # Add the "Vu :" to the header
        header.append(_wrap_in_div(soup, [lines.pop(0)]))
        if is_liste(lines[0].contents):
            flavor = "bullet_list"
        else:
            flavor = "list"

    has_more = True
    if flavor == "simple":
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

    elif flavor == "list":
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

    elif flavor == "bullet_list":
        indentation_0 = list_indentation(lines[0].contents)
        while has_more:
            pile = [lines.pop(0).contents]
            while True:
                if (
                    is_liste(lines[0].contents)
                    and list_indentation(lines[0].contents) > indentation_0
                ):
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
    return make_new_tag(soup, "div", contents=[line.contents for line in lines])
