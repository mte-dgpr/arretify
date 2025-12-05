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
import unicodedata
from typing import Sequence

from .types import PatternString, QuantifierRange, Settings

NAMED_GROUP_PATTERN = re.compile(r"\?P\<(?P<name>\w+)\>")
NAME_WITH_INDEX_PATTERN = re.compile(r"(\w+?)(?P<index>\d+)")


def sub_with_match(string: str, match: re.Match, group: int | str = 0) -> str:
    return string[: match.start(group)] + string[match.end(group) :]


def without_named_groups(pattern_string: str) -> PatternString:
    return NAMED_GROUP_PATTERN.sub("", pattern_string)


def join_with_or(pattern_strings: Sequence[str]) -> PatternString:
    for i, pattern_string in enumerate(pattern_strings):
        # We check for this, because if one pattern is a prefix of another,
        # the regex engine will always match the shorter one first.
        # So we prevent users from unintentionally letting this happen.
        for other in pattern_strings[i + 1 :]:
            if other.startswith(pattern_string):
                raise ValueError(
                    "Cannot join patterns with 'or' if one pattern is a prefix of another. "
                    f"Conflict between '{pattern_string}' and '{other}'"
                )
    return "|".join(pattern_strings)


def named_group(pattern_string: str, group_name: str) -> PatternString:
    return f"(?P<{group_name}>{pattern_string})"


def repeated_with_separator(
    pattern_string: str,
    separator: str,
    quantifier: QuantifierRange,
) -> PatternString:
    quantifier_str = quantifier_to_string(
        (
            max(quantifier[0] - 1, 0),
            max(quantifier[1] - 1, 0) if isinstance(quantifier[1], int) else Ellipsis,
        )
    )
    pattern_string = f"({pattern_string})(({separator})({pattern_string})){quantifier_str}"
    if quantifier[0] == 0:
        pattern_string = f"({pattern_string})?"

    return pattern_string


def remove_accents(s: str) -> str:
    return "".join((c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn"))


def normalize_quotes(text: str):
    return (
        text.replace("’", "'")
        .replace("“", '"')
        .replace("”", '"')
        .replace("«", '"')
        .replace("»", '"')
    )


def normalize_dashes(text: str) -> str:
    return text.replace("–", "-").replace("—", "-")


def lookup_normalized_version(
    choices: Sequence[str],
    text: str,
    settings: Settings | None = None,
) -> str:
    """
    Lookup in `choices` to find the entry that matches `text` after normalization.

    Example:
        >>> lookup_normalized_version(
            ["Café", "Restaurant"],
            "cafe",
            Settings(ignore_accents=True, ignore_case=True),
        )
        "Café"
    """
    if settings is None:
        settings = Settings()
    matches: list[str] = []
    for choice in choices:
        if normalize_string(choice, settings) == normalize_string(text, settings):
            matches.append(choice)
            break

    if not matches:
        raise KeyError(f"No match found for {text}")

    return matches[0]


def normalize_string(string: str, settings: Settings) -> str:
    if settings.ignore_case:
        string = string.lower()
    if settings.ignore_accents:
        string = remove_accents(string)
    if settings.normalize_quotes:
        string = normalize_quotes(string)
    if settings.normalize_dashes:
        string = normalize_dashes(string)
    return string


def quantifier_to_string(quantifier: QuantifierRange) -> str:
    """
    Convert a range to a quantifier string.
    For example, (2, 5) becomes {2,5} and (2, inf) becomes {2,}.
    """
    quantifier_min, quantifier_max = quantifier
    if quantifier_min < 0:
        raise ValueError("Quantifier min must be >= 0")
    if quantifier_max is not Ellipsis and quantifier_min > quantifier_max:
        raise ValueError("Quantifier min must be <= quantifier max")

    if quantifier_max == Ellipsis:
        if quantifier_min == 0:
            return "*"
        elif quantifier_min == 1:
            return "+"
        else:
            return f"{{{quantifier_min},}}"
    elif quantifier_min == quantifier_max:
        return f"{{{quantifier_min}}}"
    else:
        return f"{{{quantifier_min},{quantifier_max}}}"
