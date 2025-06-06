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
    PatternProxy,
    MatchProxy,
    normalize_string,
    Settings,
    split_string_with_regex,
    map_matches,
    safe_group,
)
from arretify.utils.merge import merge_strings
from arretify.parsing_utils.source_mapping import (
    TextSegment,
    apply_to_segment,
)


_DECOMPOSED_WORD_PATTERN = PatternProxy(r"(?=\b)([a-zA-Z]\s)+[a-zA-Z](?=\b)")


_FRENCH_DICTIONARY = {"vu", "arrete"}
"""Normalized words in the French dictionary that should be recomposed."""


# TODO-PROCESS-TAG
def clean_ocr(line: TextSegment) -> TextSegment:
    line = apply_to_segment(line, recompose_words)
    return line


def recompose_words(text: str) -> str:
    """
    OCR often produces words with spaces between letters, such as "v u" or "a r r e t e".
    This function recomposes such words by removing the spaces, but only if the resulting
    word is in the French dictionary.
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
