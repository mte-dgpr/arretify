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
