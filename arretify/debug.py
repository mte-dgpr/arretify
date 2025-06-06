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
from typing import Iterable, List

from bs4 import BeautifulSoup

from .utils.functional import flat_map_string
from .regex_utils import (
    split_string_with_regex,
    map_matches,
    PatternProxy,
)
from .utils.html import make_data_tag
from .html_schemas import DEBUG_KEYWORD_SCHEMA
from .types import PageElementOrString


def insert_debug_keywords(
    soup: BeautifulSoup,
    children: Iterable[PageElementOrString],
    query: str,
) -> List[PageElementOrString]:
    pattern = PatternProxy(query)
    return list(
        flat_map_string(
            children,
            lambda string: map_matches(
                split_string_with_regex(pattern, string),
                lambda match: make_data_tag(
                    soup,
                    DEBUG_KEYWORD_SCHEMA,
                    contents=[str(match.group(0))],
                    data=dict(query=query),
                ),
            ),
        )
    )
