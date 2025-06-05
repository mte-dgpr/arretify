from typing import Callable, Dict, Iterable, List, Literal

from bs4 import Tag, BeautifulSoup

from arretify.html_schemas import HEADER_ELEMENTS_SCHEMAS
from arretify.parsing_utils.dates import DATE_NODE, render_date_regex_tree_match
from arretify.parsing_utils.source_mapping import TextSegments
from arretify.parsing_utils.patterns import join_split_pile_with_pattern
from arretify.regex_utils import (
    map_regex_tree_match,
    split_string_with_regex_tree,
    PatternProxy,
    join_with_or,
)
from arretify.utils.functional import flat_map_string
from arretify.utils.html import (
    make_data_tag,
    PageElementOrString,
    make_new_tag,
    wrap_in_tag,
)
from arretify.utils.markdown_parsing import (
    is_list,
    is_image,
    parse_markdown_image,
)
from .document_elements import is_document_element
from .basic_elements import (
    parse_list,
    list_indentation,
)
from .titles_detection import is_title


EMBLEMS_LIST = [
    r"liberte",
    r"egalite",
    r"fraternite",
    r"republique fran[cç]aise",
]

EMBLEM_PATTERN = PatternProxy(rf"^{join_with_or(EMBLEMS_LIST)}")
"""Detect all sentences starting with French emblems."""

ENTITIES_LIST = [
    r"gouvernement",
    r"ministeres?",
    r"prefecture",
    r"sous-prefecture",
    r"secretariat",
    r"sg",
    r"prefete?",
    r"academie",
    r"rectorat",
    r"direction",
    r"drire",
    r"deal",
    r"dreal",
    r"service",
    r"section",
    r"pole",
    r"bureau",
    r"mission",
    r"unite",
    r"installations? classees? pour la protection de l'environnement",
    r"affaires? suivies? par",
    r"cheff?e? de (bureau|mission)",
]

ENTITY_PATTERN = PatternProxy(rf"^{join_with_or(ENTITIES_LIST)}")
"""Detect all services taking the arretes."""

IDENTIFICATIONS_LIST = [
    r"réf",
    r"n°",
    r"n/ref",
    r"nor",
]

IDENTIFICATION_PATTERN = PatternProxy(rf"^{join_with_or(IDENTIFICATIONS_LIST)}")
"""Detect all references."""

ARRETE_TITLE_PATTERN = PatternProxy(
    r"^[\s-]*(a\s*r\s*r\s*e\s*t\s*e\s*n?\s*t?)(?![\s-]*(?:.*?\.{5}\s+\d+)$)"
)
"""Detect if the sentence starts with "arrete" without ending points for table of contents."""

HONORARIES_LIST = [
    r"l[ea] presidente?",
    r"l[ea] ministre",
    r"la prefecture",
    r"l[ea] prefete?",
    r"commissaire",
    r"l[ea] rect(eur|rice)",
    r"recteur",
    r"l[ea] direct(eur|rice)",
    r"commandeur",
    r"chevalier",
    r"officier",
    r"chancelier",
]

HONORARY_PATTERN = PatternProxy(rf"^{join_with_or(HONORARIES_LIST)}")
"""Detect all honorary titles."""

VISA_PATTERN = PatternProxy(r"^(v\s*u|-\s*v\s*u)(\s*:\s*|\b)(?P<contents>.*)")
"""Detect if the sentence starts with "vu"."""

MOTIF_PATTERN = PatternProxy(r"^(considerant|-\s*considerant)(\s*:\s*|\b)(?P<contents>.*)")
"""Detect if the sentence starts with "considerant"."""

SUPPLEMENTARY_MOTIF_INFORMATIONS_LIST = [
    r"le (demandeur|petitionnaire) entendu",
    r"l'exploitant entendu",
    r"apres communication",
    r"sur (?:la )?proposition",
]

SUPPLEMENTARY_MOTIF_INFORMATION_PATTERN = PatternProxy(
    rf"^{join_with_or(SUPPLEMENTARY_MOTIF_INFORMATIONS_LIST)}"
)
"""Detect all other information that can be part of the motifs."""

HEADER_ELEMENTS_PATTERNS: Dict[str, PatternProxy] = {
    "emblem": EMBLEM_PATTERN,
    "entity": ENTITY_PATTERN,
    "identification": IDENTIFICATION_PATTERN,
    "arrete_title": ARRETE_TITLE_PATTERN,
    "honorary": HONORARY_PATTERN,
    "visa": VISA_PATTERN,
    "motif": MOTIF_PATTERN,
    "supplementary_motif_info": SUPPLEMENTARY_MOTIF_INFORMATION_PATTERN,
}

HEADER_ELEMENTS_PROBES: Dict[str, Callable] = {
    "emblem": lambda line: bool(EMBLEM_PATTERN.match(line)),
    "entity": lambda line: bool(ENTITY_PATTERN.match(line)),
    "identification": lambda line: bool(IDENTIFICATION_PATTERN.match(line)),
    "arrete_title": lambda line: bool(ARRETE_TITLE_PATTERN.match(line)),
    "honorary": lambda line: bool(HONORARY_PATTERN.match(line)),
    "visa": lambda line: bool(VISA_PATTERN.match(line)),
    "motif": lambda line: bool(MOTIF_PATTERN.match(line)),
    "supplementary_motif_info": lambda line: bool(
        SUPPLEMENTARY_MOTIF_INFORMATION_PATTERN.match(line)
    ),
    "document_element": is_document_element,
    "title": is_title,
}
"""Header elements probes."""


def _make_negative_probe(header_element_name: str):

    next_probes = [
        value for key, value in HEADER_ELEMENTS_PROBES.items() if key != header_element_name
    ]

    def _probe(line: str):
        return any([probe(line) for probe in next_probes])

    return _probe


def _wrap_in_div(soup: BeautifulSoup, lines: TextSegments) -> Tag:
    return make_new_tag(soup, "div", contents=[line.contents for line in lines])


def parse_header_beginning(
    soup: BeautifulSoup,
    header: Tag,
    lines: TextSegments,
):
    is_first_header_element = _make_negative_probe("")

    while lines and not is_first_header_element(lines[0].contents):
        if is_image(lines[0].contents):
            header.append(parse_markdown_image(lines.pop(0).contents))
        else:
            header.append(_wrap_in_div(soup, [lines.pop(0)]))

    return lines


def _parse_header_element(
    soup: BeautifulSoup,
    header: Tag,
    lines: TextSegments,
    header_element_name: str,
    join_split_with_pattern: bool = True,
) -> TextSegments:
    pile: List[str] = []
    is_next_header_element = _make_negative_probe(header_element_name)
    header_element_pattern = HEADER_ELEMENTS_PATTERNS[header_element_name]
    header_element_schema = HEADER_ELEMENTS_SCHEMAS[header_element_name]

    while lines and not is_next_header_element(lines[0].contents):

        if is_image(lines[0].contents):
            header.append(parse_markdown_image(lines.pop(0).contents))
        else:
            pile.append(lines.pop(0).contents)

    elements: List[PageElementOrString]
    if join_split_with_pattern:
        elements = join_split_pile_with_pattern(pile, header_element_pattern)
    else:
        elements = [line for line in pile]

    if elements:

        header_element = make_data_tag(
            soup,
            header_element_schema,
            contents=wrap_in_tag(soup, elements, "div"),
        )
        header.append(header_element)

    return lines


def parse_emblem_element(
    soup: BeautifulSoup,
    header: Tag,
    lines: TextSegments,
) -> TextSegments:
    return _parse_header_element(
        soup,
        header,
        lines,
        "emblem",
    )


def parse_entity_element(
    soup: BeautifulSoup,
    header: Tag,
    lines: TextSegments,
) -> TextSegments:
    return _parse_header_element(
        soup,
        header,
        lines,
        "entity",
    )


def parse_identification_element(
    soup: BeautifulSoup,
    header: Tag,
    lines: TextSegments,
) -> TextSegments:
    return _parse_header_element(
        soup,
        header,
        lines,
        "identification",
    )


def _parse_arrete_title_info(
    soup: BeautifulSoup,
    children: Iterable[PageElementOrString],
) -> List[PageElementOrString]:
    children = list(
        flat_map_string(
            children,
            lambda string: map_regex_tree_match(
                split_string_with_regex_tree(DATE_NODE, string),
                lambda date_match: render_date_regex_tree_match(soup, date_match),
                allowed_group_names=["__date"],
            ),
        )
    )
    return children


def parse_arrete_title_element(
    soup: BeautifulSoup,
    header: Tag,
    lines: TextSegments,
):
    pile: List[str] = []
    header_element_name = "arrete_title"
    is_next_header_element = _make_negative_probe(header_element_name)

    while lines and not is_next_header_element(lines[0].contents):

        if is_image(lines[0].contents):
            header.append(parse_markdown_image(lines.pop(0).contents))
        else:
            pile.append(lines.pop(0).contents)

    if pile:

        header_element = make_data_tag(
            soup,
            HEADER_ELEMENTS_SCHEMAS[header_element_name],
            contents=[
                make_new_tag(
                    soup,
                    "h1",
                    contents=_parse_arrete_title_info(soup, [" ".join(pile)]),
                )
            ],
        )
        header.append(header_element)

    return lines


def parse_honorary_element(
    soup: BeautifulSoup,
    header: Tag,
    lines: TextSegments,
) -> TextSegments:
    return _parse_header_element(
        soup,
        header,
        lines,
        "honorary",
    )


def _parse_visas_or_motifs(
    soup: BeautifulSoup,
    header: Tag,
    lines: TextSegments,
    header_element_name: str,
) -> TextSegments:
    pile: List[PageElementOrString]
    is_next_header_element = _make_negative_probe(header_element_name)

    if not lines or is_next_header_element(lines[0].contents):
        return lines

    header_element_pattern = HEADER_ELEMENTS_PATTERNS[header_element_name]
    header_element_schema = HEADER_ELEMENTS_SCHEMAS[header_element_name]

    has_more = bool(header_element_pattern.match(lines[0].contents))
    # simple : "Vu blabla" ou "- vu blabla"
    # bullet_list : "- vu blabla" ou "Vu \n - blabla"
    # list : "Vu:\n blabla"
    flavor: Literal["simple", "bullet_list", "list"] | None = None

    section_match = header_element_pattern.match(lines[0].contents)
    if section_match and section_match.group("contents"):
        flavor = "simple"
    else:
        # Add the "Vu :" to the header
        header.append(_wrap_in_div(soup, [lines.pop(0)]))
        if is_list(lines[0].contents):
            flavor = "bullet_list"
        else:
            flavor = "list"

    has_more = True
    if flavor == "simple":
        while has_more:
            pile = [lines.pop(0).contents]
            while (
                lines
                and is_list(lines[0].contents)
                and not header_element_pattern.match(lines[0].contents)
            ):
                lines, ul_element = parse_list(soup, lines)
                pile.append(ul_element)
            header.append(make_data_tag(soup, header_element_schema, contents=pile))

            # Consume lines until we find the next visa, or the beginning of the next header element
            while True:
                if not lines:
                    has_more = False
                    break
                elif header_element_pattern.match(lines[0].contents):
                    break
                elif is_next_header_element(lines[0].contents):
                    has_more = False
                    break
                elif is_image(lines[0].contents):
                    header.append(parse_markdown_image(lines.pop(0).contents))
                else:
                    header.append(_wrap_in_div(soup, [lines.pop(0)]))

    elif flavor == "list":
        while has_more:
            pile = [lines.pop(0).contents]
            while lines and is_list(lines[0].contents):
                lines, ul_element = parse_list(soup, lines)
                pile.append(ul_element)
            header.append(make_data_tag(soup, header_element_schema, contents=pile))

            # Consume lines until we find the next visa, or the beginning of the next header element
            if not lines or is_next_header_element(lines[0].contents):
                has_more = False
                break

    elif flavor == "bullet_list":
        indentation_0 = list_indentation(lines[0].contents)
        while has_more:
            pile = [lines.pop(0).contents]
            while (
                lines
                and is_list(lines[0].contents)
                and list_indentation(lines[0].contents) > indentation_0
            ):
                lines, ul_element = parse_list(soup, lines)
                pile.append(ul_element)
            header.append(make_data_tag(soup, header_element_schema, contents=pile))

            # Consume lines until we find the next visa, or the beginning of the next header element
            while True:
                if not lines or is_next_header_element(lines[0].contents):
                    has_more = False
                    break
                elif is_list(lines[0].contents):
                    break
                elif is_image(lines[0].contents):
                    header.append(parse_markdown_image(lines.pop(0).contents))
                else:
                    header.append(_wrap_in_div(soup, [lines.pop(0)]))

    return lines


def parse_visa_element(
    soup: BeautifulSoup,
    header: Tag,
    lines: TextSegments,
) -> TextSegments:
    return _parse_visas_or_motifs(
        soup,
        header,
        lines,
        "visa",
    )


def parse_motif_element(
    soup: BeautifulSoup,
    header: Tag,
    lines: TextSegments,
) -> TextSegments:
    return _parse_visas_or_motifs(
        soup,
        header,
        lines,
        "motif",
    )


def parse_supplementary_motif_info_element(
    soup: BeautifulSoup,
    header: Tag,
    lines: TextSegments,
) -> TextSegments:
    return _parse_header_element(
        soup,
        header,
        lines,
        "supplementary_motif_info",
    )
