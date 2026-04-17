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
import logging
from typing import Optional, Sequence, Tuple

from arretify.parsing_utils.numbering import (
    EME_PATTERN_S,
    NUMBERING_PATTERN_S,
    NUMBERS_PATTERN_S,
    ORDINAL_PATTERN,
    ORDINAL_PATTERN_S,
    are_levels_contiguous,
    ordinal_str_to_int,
    str_to_levels,
)
from arretify.parsing_utils.patterns import LEADING_TRAILING_PUNCTUATION_PATTERN
from arretify.regex_utils import Settings, join_with_or, regex_tree
from arretify.regex_utils.helpers import lookup_normalized_version
from arretify.regex_utils.regex_tree.types import MatchDict
from arretify.types import SectionType
from arretify.utils.html_split_merge import regex_tree_match

from .types import TitleInfo

_LOGGER = logging.getLogger(__name__)


TITLE_PUNCTUATION_PATTERN_S = r"[.\s\-:]"

SECTION_TYPES_LIST = [
    (SectionType.ANNEXE, SectionType.ANNEXE.value),
    (SectionType.TITRE, SectionType.TITRE.value),
    (SectionType.CHAPITRE, SectionType.CHAPITRE.value),
    (SectionType.ARTICLE, SectionType.ARTICLE.value),
    (SectionType.ARTICLE, "art."),
]
"""List of section types that we want to detect."""


SECTION_TYPE_SETTINGS = Settings()


TITLE_NODE = regex_tree.Group(
    regex_tree.Branching(
        [
            # Variant 1 : This regex matches section names in arretes such as
            # Annexe 1
            # Titre 1
            # Titre I - TITRE
            # Titre 1. TITRE
            # Titre 2 TITRE
            # Chapitre 1.2 - CHAPITRE
            # Chapitre A. CHAPITRE
            # Article 1.2.3 - Article
            # Article 1.2.3
            # Article 1.2.3. - Article.
            regex_tree.Sequence(
                [
                    # Section name
                    regex_tree.Literal(
                        rf"^(?P<section_type>{join_with_or([
                            section_type_str for
                            _, section_type_str in SECTION_TYPES_LIST
                        ])})",
                        settings=SECTION_TYPE_SETTINGS,
                    ),
                    regex_tree.Branching(
                        [
                            # Title has no numbering
                            regex_tree.Sequence(
                                [
                                    # Punctuation before the end of the line
                                    rf"(?P<punc_before>{TITLE_PUNCTUATION_PATTERN_S}*)$",
                                ]
                            ),
                            # Title has numbering
                            regex_tree.Sequence(
                                [
                                    # Punctuation between section name and numbering
                                    rf"(?P<punc_before>\s*{TITLE_PUNCTUATION_PATTERN_S}\s*)",
                                    # Numbering pattern
                                    regex_tree.Branching(
                                        [
                                            rf"(?P<number>{ORDINAL_PATTERN_S})",
                                            rf"(?P<number>(\d|I|i))(?P<eme>{EME_PATTERN_S})",
                                            rf"(?P<number>{NUMBERING_PATTERN_S}([.\-]{NUMBERS_PATTERN_S})*\.?)",  # noqa
                                        ],
                                    ),
                                    # Punctuation between numbering and text
                                    rf"(?P<punc_after>{TITLE_PUNCTUATION_PATTERN_S}*)",
                                    # Text group
                                    r"(?P<text>.*?)$",
                                ]
                            ),
                        ],
                    ),
                ],
            ),
            # Variant 2 : This regex matches section names in arretes such as
            # 1.2 - CHAPITRE
            # 1.2.3 - Article
            # 1.2.3. - Article.
            regex_tree.Sequence(
                [
                    # Numbering pattern with at least two numbers
                    rf"(?P<number>{NUMBERING_PATTERN_S}([.\-]{NUMBERS_PATTERN_S})+\.?)",
                    # Punctuation between numbering and text
                    rf"(?P<punc_after>{TITLE_PUNCTUATION_PATTERN_S}*)",
                    # Text group
                    r"(?P<text>.*?)$",
                ],
            ),
            # Variant 3 : This regex matches section names in arretes such as
            # 1 TITRE
            # 1 - Article
            regex_tree.Sequence(
                [
                    # Numbering pattern with only one integer
                    rf"^(?P<number>{NUMBERS_PATTERN_S}\.?)",
                    # Punctuation between section name and numbering
                    rf"(?P<punc_after>\s*{TITLE_PUNCTUATION_PATTERN_S}\s*)",
                    # Text group starting with one word and not ending with punctuation
                    r"(?P<text>(?!.*[.;:,]$)[a-zA-Z]+(\b.+)*)$",
                ],
            ),
            # Variant 4 : This regex matches "Prescriptions annexées" as an annexe marker
            regex_tree.Sequence(
                [
                    regex_tree.Literal(
                        r"^(?P<prescriptions_annexees>Prescriptions\s+annexées)",
                        settings=SECTION_TYPE_SETTINGS,
                    ),
                    rf"(?P<punc_after>{TITLE_PUNCTUATION_PATTERN_S}*)",
                    r"(?P<text>.*?)$",
                ],
            ),
        ],
    ),
    group_name="title",
)


def parse_title_text(line: str) -> Tuple[str, str]:
    """This function splits a line containing a title into its section name and text parts."""
    # Detect pattern
    match_pattern = regex_tree_match([line], TITLE_NODE)
    assert match_pattern, "Only use parse function when match pattern exists!"

    # Extract dict
    match_dict = match_pattern.match_dict

    if "prescriptions_annexees" in match_dict:
        section_name = match_dict["prescriptions_annexees"]
        punc_after = match_dict.get("punc_after", "")
        section_name = section_name + punc_after
        text = match_dict.get("text", "")
        return section_name, text

    # Build the section name
    section_type = match_dict.get("section_type", "")
    punc_before = match_dict.get("punc_before", "")
    number = match_dict.get("number", "")
    eme = match_dict.get("eme", "")
    punc_after = match_dict.get("punc_after", "")
    section_name = "".join([section_type, punc_before, number, eme, punc_after])

    # Split text parts
    text = match_dict.get("text", "")

    return section_name, text


def parse_title_info(line: str) -> TitleInfo:
    # Detect pattern
    match_pattern = regex_tree_match([line], TITLE_NODE)
    assert match_pattern, "Only use parse function when match pattern exists!"

    # Extract values
    match_dict = match_pattern.match_dict

    if "prescriptions_annexees" in match_dict:
        return TitleInfo(
            section_type=SectionType.ANNEXE,
            number="1",
            levels=[1],
            text=match_dict.get("text") or None,
        )

    section_type = _extract_section_type(match_dict)
    number = match_dict.get("number", "")
    text = match_dict.get("text")

    # Compute levels
    number = LEADING_TRAILING_PUNCTUATION_PATTERN.sub("", number)
    if len(number) <= 0:
        _LOGGER.warning(f"Numbering parsing output none for title: {line}")
    if ORDINAL_PATTERN.match(number):
        number = str(ordinal_str_to_int(number))
    levels = str_to_levels(number)

    # Define title info
    title_info = TitleInfo(
        section_type=section_type,
        number=number,
        levels=levels,
        text=text,
    )

    return title_info


def _extract_section_type(match_dict: MatchDict) -> SectionType:
    if "section_type" not in match_dict:
        return SectionType.UNKNOWN

    actual_section_type_str = lookup_normalized_version(
        [section_type_str for _, section_type_str in SECTION_TYPES_LIST],
        match_dict["section_type"],
        settings=SECTION_TYPE_SETTINGS,
    )
    filtered = [
        section_type
        for section_type, section_type_str in SECTION_TYPES_LIST
        if section_type_str == actual_section_type_str
    ]
    assert len(filtered) == 1, (
        f"Expected exactly one section type for section type string {actual_section_type_str},"
        " but got {filtered}."
    )
    return SectionType(filtered[0])


def is_next_title(
    current_global_levels: Optional[Sequence[int]],
    current_title_levels: Optional[Sequence[int]],
    new_title_levels: Optional[Sequence[int]],
) -> bool:
    return are_levels_contiguous(current_global_levels, new_title_levels) or are_levels_contiguous(
        current_title_levels, new_title_levels
    )
