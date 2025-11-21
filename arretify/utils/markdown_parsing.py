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
import re
from typing import Sequence

import markdown
from bs4 import BeautifulSoup

from arretify.errors import ErrorCodes
from arretify.regex_utils import PatternProxy, repeated_with_separator
from arretify.semantic_tag_specs import ErrorSpec
from arretify.types import ProtectedTag, protect_soup
from arretify.utils.html_create import make_semantic_tag, make_tag

TABLE_LINE_PATTERN = PatternProxy(
    r"^\|" + repeated_with_separator(r"[^|\n]+", r"\|", (1, ...)) + r"\|$"
)
"""
Detect a markdown table line.
This pattern ensures that the line starts and ends with a pipe
and contains at least one cell in between.
"""

TABLE_HEADER_SEPARATOR_PATTERN = PatternProxy(
    r"^\|" + repeated_with_separator(r"[-:\s]+", r"\|", (1, ...)) + r"\|$"
)
"""
Detect a markdown table header separator.
This pattern ensures that the line starts and ends with a pipe
and contains at least two cells, with only characters -, : or whitespace in between.
"""

TABLE_DESCRIPTION_PATTERN = PatternProxy(r"^(\(\*+\))|^(\*+)")
"""Detect if the line is a table description, i.e. starts with "*" or "(*)"."""

BULLETPOINT_PATTERN_S = r"(\>|→|-|[a-zA-Z1-9][\)°])"
"""Detect if the line contains a >, →, - or a number or letter followed by ) or °."""

LIST_PATTERN = PatternProxy(rf"^(?P<indentation>\s*){BULLETPOINT_PATTERN_S}\s+")
"""Detect if the line starts with a bulletpoint with preceding indentation."""

IMAGE_PATTERN = PatternProxy(r"!\[[^\[\]]+\]\([^()]+\)")
"""Detect if the line starts with an image."""


def is_table_description(line: str, pile: Sequence[str]) -> bool:
    # Sentence starts with any number of * between parentheses or without parentheses
    match = TABLE_DESCRIPTION_PATTERN.match(line)
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


def parse_markdown_table(lines: Sequence[str]) -> ProtectedTag:
    markdown_str = "\n".join(lines)
    html_str = markdown.markdown(markdown_str, extensions=["tables"])
    soup = protect_soup(BeautifulSoup(html_str, features="html.parser"))
    table_result = soup.select("table")
    if len(table_result) != 1:
        return make_semantic_tag(
            soup,
            ErrorSpec,
            data=ErrorSpec.data_model(error_codes=[ErrorCodes.markdown_parsing]),
            contents=[markdown_str],
        )

    return make_tag(soup, "table", contents=list(table_result[0].contents))


def parse_markdown_image(line: str) -> ProtectedTag:
    html_str = markdown.markdown(line)
    soup = protect_soup(BeautifulSoup(html_str, features="html.parser"))
    image_element = soup.select("img")[0]
    return image_element
