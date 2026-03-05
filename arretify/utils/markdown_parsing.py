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

import markdown
from bs4 import BeautifulSoup

from arretify.regex_utils import PatternProxy
from arretify.types import ProtectedTag, protect_soup
from arretify.utils.strings import merge_strings

TABLE_DESCRIPTION_PATTERN = PatternProxy(r"^(\(\*+\))|^(\*+)|^(\(\d+\))")
"""Detect if the line is a table description, i.e. starts with "*" or "(*)" or "(1)"."""

BULLETPOINT_PATTERN_S = r"(\>|→|-|[a-zA-Z1-9][\)°])"
"""Detect if the line contains a >, →, - or a number or letter followed by ) or °."""

LIST_PATTERN = PatternProxy(rf"^(?P<indentation>\s*){BULLETPOINT_PATTERN_S}\s+")
"""Detect if the line starts with a bulletpoint with preceding indentation."""

IMAGE_PATTERN_S = r"!\[[^\[\]]+\]\([^()]+\)"
"""Detects a markdown image."""

LINK_PATTERN_S = r"\[[^\[\]]+\]\([^()]+\)"
"""Detects a markdown link."""


def is_table_description(line: str, table: ProtectedTag) -> bool:
    # Sentence starts with any number of * between parentheses or without parentheses
    match = TABLE_DESCRIPTION_PATTERN.match(line)
    if match:
        return True

    # Sentence that explains the name of one of the columns
    header_cells = table.select("thead th, thead td, tr:first-child th, tr:first-child td")
    if header_cells:
        column_names = []
        for cell in header_cells:
            column_strip = merge_strings(cell.stripped_strings)
            column_raw = re.sub(r"\([^)]*\)", "", column_strip).strip()
            if len(column_raw) > 0:
                column_names.append(column_raw)

        # For each column name, check if we have it followed by :
        for column_name in column_names:
            if re.match(rf".*{re.escape(column_name)} :", line, re.IGNORECASE):
                return True
    return False


def parse_markdown_element(line: str, selector: str) -> ProtectedTag:
    html_str = markdown.markdown(line)
    soup = protect_soup(BeautifulSoup(html_str, features="html.parser"))
    return soup.select(selector)[0]
