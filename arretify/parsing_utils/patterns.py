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
from typing import Sequence

from arretify.regex_utils import (
    PatternProxy,
    Settings,
    merge_matches_with_siblings,
    split_string_with_regex,
)
from arretify.types import ProtectedTagOrStr

ET_VIRGULE_PATTERN_S = r"(\s*(,|,?et)\s*)"

LEADING_TRAILING_WHITESPACE_PATTERN = PatternProxy(r"^[\s]+|[\s]+$")
"""Detect leading and trailing whitespaces."""

LEADING_TRAILING_PUNCTUATION_PATTERN = PatternProxy(r"^[\s.]+|[\s.]+$")
"""Detect leading and trailing points or whitespaces."""

LETTER_PATTERN_S = r"[a-zA-Z]"

SENTENCE_END_PATTERN_S = r"[.!?]"

SENTENCE_END_AT_LINE_END_PATTERN = PatternProxy(SENTENCE_END_PATTERN_S + r"\s*$")

SENTENCE_CONTINUES_AT_LINE_START_PATTERN = PatternProxy(r"^\s*[a-z]", Settings(ignore_case=False))


def join_split_pile_with_pattern(
    pile: Sequence[str],
    pattern: PatternProxy,
) -> Sequence[ProtectedTagOrStr]:
    return list(
        merge_matches_with_siblings(
            split_string_with_regex(
                pattern,
                " ".join(pile),
            ),
            "following",
        )
    )


def is_continuing_sentence(part1: str, part2: str) -> bool:
    return (
        SENTENCE_END_AT_LINE_END_PATTERN.search(part1) is None
        and SENTENCE_CONTINUES_AT_LINE_START_PATTERN.search(part2) is not None
    )
