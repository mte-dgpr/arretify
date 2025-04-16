import re
from typing import List, cast

import markdown
from bs4 import BeautifulSoup

from arretify.errors import ErrorCodes
from arretify.utils.html import (
    PageElementOrString,
    make_data_tag,
)
from arretify.html_schemas import ERROR_SCHEMA
from arretify.regex_utils import PatternProxy


TABLE_LINE_PATTERN = PatternProxy(r"(\|)")
"""Detect if the line contains a table, i.e. any "|" character."""

TABLE_DESCRIPTION_PATTERN = PatternProxy(r"^(\(\*+\))|^(\*+)")
"""Detect if the line is a table description, i.e. starts with "*" or "(*)"."""

LIST_PATTERN = PatternProxy(r"^(?P<indentation>\s*)(-\s|[a-zA-Z1-9][\)°]\s+)")
"""Detect if the line starts with - or a number or letter followed by )."""

IMAGE_PATTERN = PatternProxy(r"!\[[^\[\]]+\]\([^()]+\)")
"""Detect if the line starts with an image."""


def is_table_line(line: str) -> bool:
    """Detect if the line contains a table, i.e. any "|" character."""
    return bool(re.search(r"(\|)", line, re.IGNORECASE))


def is_table_description(line: str, pile: List[PageElementOrString]) -> bool:
    # Sentence starts with any number of * between parentheses or without parentheses
    match = TABLE_DESCRIPTION_PATTERN.search(line)
    if match:
        return True

    # Sentence that explains the name of one of the columns
    pile_bottom = pile[0] if len(pile) >= 1 else None
    if isinstance(pile_bottom, str):
        column_names = []
        columns_split = pile_bottom.split("|")
        for column_split in columns_split:
            column_strip = column_split.strip()
            column_raw = re.sub(r"\([^)]*\)", "", column_strip).strip()
            if len(column_raw) > 0:
                column_names.append(column_raw)

        # For each column name, check if we have it followed by :
        for column_name in column_names:
            if re.match(rf".*{re.escape(column_name)} :", line, re.IGNORECASE):
                return True
    return False


def is_list(line: str) -> bool:
    """Detect if the sentence is a list element."""
    return bool(LIST_PATTERN.match(line))


def is_image(line: str) -> bool:
    """Detect if the sentence starts with an image."""
    return bool(IMAGE_PATTERN.search(line))


def parse_markdown_table(elements: List[PageElementOrString]):
    if [element for element in elements if not isinstance(element, str)]:
        raise ValueError("got unexpected non-string element to parse markdown from")

    markdown_str = "\n".join(cast(List[str], elements))
    html_str = markdown.markdown(markdown_str, extensions=["tables"])
    soup = BeautifulSoup(html_str, features="html.parser")
    table_result = soup.select("table")
    if len(table_result) != 1:
        return make_data_tag(
            soup,
            ERROR_SCHEMA,
            data=dict(error_code=ErrorCodes.markdown_parsing.value),
            contents=[markdown_str],
        )

    table_element = soup.new_tag("table")
    table_element.extend(list(table_result[0].children))
    return table_element


def parse_markdown_image(element: PageElementOrString):
    if not isinstance(element, str):
        raise ValueError("got unexpected non-string element to parse markdown from")

    html_str = markdown.markdown(element)
    soup = BeautifulSoup(html_str, features="html.parser")
    image_element = soup.select("img")[0]

    return image_element
