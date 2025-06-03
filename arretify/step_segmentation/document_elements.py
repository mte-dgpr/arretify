from typing import List

from bs4 import Tag, BeautifulSoup

from arretify.parsing_utils.source_mapping import TextSegments
from arretify.regex_utils import (
    PatternProxy,
    join_with_or,
)
from arretify.utils.html import (
    PageElementOrString,
    make_data_tag,
    wrap_in_tag,
)
from arretify.utils.markdown_parsing import is_image
from arretify.html_schemas import (
    FOOTER_SCHEMA,
    TABLE_OF_CONTENTS_SCHEMA,
)


FOOTERS_LIST = [
    # "X/Y"
    r"\d+/\d+\s*",
    # "Page X/Y"
    r"page\s+\d+/\d+\s*",
    # "Page X sur Y"
    r"page\s+\d+\s+sur\s+\d+\s*",
    # "Page X"
    r"page\s+\d+",
]

FOOTER_PATTERN = PatternProxy(rf"^{join_with_or(FOOTERS_LIST)}")
"""Detect footer for numbering pages."""

TABLE_OF_CONTENTS_PAGING_PATTERN_S = r"\.{5}\s+(page\s+)?\d+"
"""Detect table of contents paging pattern, e.g. "..... page 1" or "..... 1"."""

TABLE_OF_CONTENTS_LIST = [
    r"sommaire",
    r"table des matieres",
    r"liste des (chapitres|articles)",
    rf".*?\s+{TABLE_OF_CONTENTS_PAGING_PATTERN_S}$",
]

TABLE_OF_CONTENTS_PATTERN = PatternProxy(rf"^{join_with_or(TABLE_OF_CONTENTS_LIST)}")
"""Detect all table of contents starting sentences."""


def _is_footer(line: str) -> bool:
    """Detect footer for numbering pages."""
    return bool(FOOTER_PATTERN.match(line))


def _is_table_of_contents(line: str) -> bool:
    """Detect if the line is a table of contents."""
    return bool(TABLE_OF_CONTENTS_PATTERN.match(line))


def is_document_element(line: str) -> bool:
    """Detect if the line is a document element.

    Note: Image strings can be very long, and table of contents pattern look at the end of the
    sentence. So, we make sure we do not have an image in the line before checking for other
    document elements.
    """
    return not is_image(line) and (_is_footer(line) or _is_table_of_contents(line))


def _parse_footer(
    soup: BeautifulSoup,
    content: Tag,
    lines: TextSegments,
) -> TextSegments:
    """Parse footer."""
    while lines and _is_footer(lines[0].contents):
        footer_element = make_data_tag(soup, FOOTER_SCHEMA, contents=[lines.pop(0).contents])
        content.append(footer_element)

    return lines


def _parse_table_of_contents(
    soup: BeautifulSoup,
    tag: Tag,
    lines: TextSegments,
) -> TextSegments:
    """Parse table of contents."""
    pile: List[PageElementOrString] = []

    while lines and _is_table_of_contents(lines[0].contents):
        pile.append(lines.pop(0).contents)

    if pile:

        toc_element = make_data_tag(
            soup,
            TABLE_OF_CONTENTS_SCHEMA,
            contents=wrap_in_tag(soup, pile, "div"),
        )
        tag.append(toc_element)

    return lines


def parse_document_elements(
    soup: BeautifulSoup,
    tag: Tag,
    lines: TextSegments,
) -> TextSegments:
    """Parse document elements."""
    while lines and is_document_element(lines[0].contents):

        # Footer
        lines = _parse_footer(soup, tag, lines)

        # Table of contents
        lines = _parse_table_of_contents(soup, tag, lines)

    return lines
