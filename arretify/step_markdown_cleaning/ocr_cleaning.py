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

from arretify.regex_utils import (
    MatchProxy,
    PatternProxy,
    Settings,
    map_matches,
    normalize_string,
    safe_group,
    split_string_with_regex,
)
from arretify.utils.strings import merge_strings

_DECOMPOSED_WORD_PATTERN = PatternProxy(r"(?=\b)([a-zA-Z]\s)+[a-zA-Z](?=\b)")


_FRENCH_DICTIONARY = {"vu", "arrete", "arretent"}
"""Normalized words in the French dictionary that should be recomposed."""


_PUNCTUATION_LINE_PATTERN = PatternProxy(r"^[·.,;:!?'\s\-]*$")
"""Detect if the line contains only punctuation."""


# TODO-PROCESS-TAG
def clean_ocr(line: str) -> str:
    line = recompose_words(line)
    return line


def is_useful_line(line: str) -> bool:
    return not is_punctuation_line(line)


def is_punctuation_line(text: str) -> bool:
    """
    Our OCRized file might contain some blank lines or lines that only contain punctuation.
    """
    return bool(_PUNCTUATION_LINE_PATTERN.search(text))


def recompose_words(text: str) -> str:
    """
    When there is large letter spacing in text, OCR often produces results
    such as "v u" or "a r r e t e".
    This function recomposes such words by removing the spaces, but only if the resulting
    word is in our dictionary.
    """
    return merge_strings(
        map_matches(
            split_string_with_regex(_DECOMPOSED_WORD_PATTERN, text), _render_decomposed_word
        )
    )


def _render_decomposed_word(match: MatchProxy):
    decomposed = safe_group(match, 0)
    recomposed = re.sub(r"\s+", "", decomposed)
    recomposed_normalized = normalize_string(recomposed, Settings())
    if recomposed_normalized in _FRENCH_DICTIONARY:
        return recomposed
    else:
        return decomposed
