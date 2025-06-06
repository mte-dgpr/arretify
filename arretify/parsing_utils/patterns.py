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
from typing import List

from arretify.regex_utils import (
    PatternProxy,
    split_string_with_regex,
    merge_matches_with_siblings,
)
from arretify.utils.html import PageElementOrString


ET_VIRGULE_PATTERN_S = r"(\s*(,|,?et)\s*)"

LEADING_TRAILING_PUNCTUATION_PATTERN = PatternProxy(r"^[\s.]+|[\s.]+$")
"""Detect leading and trailing points or whitespaces."""

LETTER_PATTERN_S = r"[a-zA-Z]"


def join_split_pile_with_pattern(
    pile: List[str],
    pattern: PatternProxy,
) -> List[PageElementOrString]:
    return list(
        merge_matches_with_siblings(
            split_string_with_regex(
                pattern,
                " ".join(pile),
            ),
            "following",
        )
    )
