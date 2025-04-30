import logging
from typing import List, Optional, Union

import roman

from arretify.parsing_utils.patterns import (
    EME_PATTERN_S,
    ORDINAL_PATTERN_S,
    ORDINAL_PATTERN,
    ordinal_str_to_int,
)
from arretify.regex_utils import (
    PatternProxy,
    regex_tree,
    join_with_or,
    Settings,
)
from arretify.regex_utils.regex_tree.execute import (
    match,
)
from .types import BodySection, SectionInfo


_LOGGER = logging.getLogger(__name__)


LEADING_TRAILING_PUNCTUATION_PATTERN = PatternProxy(r"^[\s.]+|[\s.]+$")
"""Detect leading and trailing points or whitespaces."""


ROMAN_NUMERALS = r"(?:(?:X{0,3})(?:IX|IV|V?I{0,3}))"
NUMBERS = r"\d+"
LETTER = r"[a-zA-Z]"
NUMBERING = rf"(?:{NUMBERS}|{LETTER}|{ROMAN_NUMERALS})"
ROMAN_NUMERALS_PATTERN = PatternProxy(ROMAN_NUMERALS + "$")
NUMBERS_PATTERN = PatternProxy(NUMBERS + "$")
LETTER_PATTERN = PatternProxy(LETTER + "$")
"""Detect all types of numbering patterns."""

SECTION_NAMES = [
    r"titre",
    r"chapitre",
    r"article",
]
"""Detect all section names."""


SECTION_TITLE_NODE = regex_tree.Group(
    regex_tree.Branching(
        [
            # This regex matches section names in arretes such as
            # Titre 1
            # Titre I - TITRE
            # Titre 1. TITRE
            # Titre 2 TITRE
            # Chapitre 1.A
            # Chapitre 1.2 - CHAPITRE
            # Chapitre A. CHAPITRE
            # Article X.X.X - Article
            # Article X.X.X
            # Article X.X.X. - Article.
            # Section is split into a section name, a numbering pattern and an optional text group
            regex_tree.Sequence(
                [
                    # Section name
                    rf"^(?P<section_name>{join_with_or(SECTION_NAMES)})\s*",
                    # Numbering pattern
                    regex_tree.Branching(
                        [
                            rf"(?P<number>{ORDINAL_PATTERN_S})",
                            rf"(?P<number>(\d|I|i)){EME_PATTERN_S}",
                            rf"(?P<number>{NUMBERING}(?:[.]{NUMBERING})*)",
                        ],
                        settings=Settings(ignore_accents=False),
                    ),
                    # Do not catch the optional punctuation
                    r"(?:[.\s\-:]*)",
                    # Optional text group
                    r"(?P<text>\s*(.+))?$",
                ]
            ),
            # This regex matches section names in arretes such as
            # 1. TITRE
            # 1.2 - CHAPITRE
            # 1.A. CHAPITRE
            # 1.X.X - Article
            # Section is split into a numbering pattern and a text group
            regex_tree.Sequence(
                [
                    # Numbering pattern with space
                    # First number must be an integer followed by point
                    rf"^(?P<number>{NUMBERS}[.](?:{NUMBERING}[.])*{NUMBERING})\s+",
                    # Text group without ending punctuation
                    r"(?P<text>\s*(.+?)(?<![.;:,]))$",
                ],
                settings=Settings(ignore_accents=False),
            ),
        ]
    ),
    group_name="section",
)


def _number_to_levels(number: str) -> Optional[List[int]]:

    number_split = number.replace(".", " ").split()
    level = len(number_split) - 1

    if level < 0:
        return None

    section_levels = [0] * (level + 1)

    for i in range(level + 1):

        cur_char = number_split[level - i]

        if ROMAN_NUMERALS_PATTERN.match(cur_char):
            cur_number = roman.fromRoman(cur_char)
        elif LETTER_PATTERN.match(cur_char):
            cur_number = ord(cur_char.lower()) - 96
        elif NUMBERS_PATTERN.match(cur_char):
            cur_number = int(cur_char)
        else:
            err_msg = f"Unsupported level conversion for {cur_char}"
            raise ValueError(err_msg)

        section_levels[level - i] = cur_number

    return section_levels


def are_sections_contiguous(
    cur_section_levels: Union[None, List[int]],
    new_section_levels: Union[None, List[int]],
) -> bool:

    if not new_section_levels:
        return False

    if not cur_section_levels:
        return True

    cur_section_level = len(cur_section_levels)
    new_section_level = len(new_section_levels)

    is_continuing_section = False

    # First the new section should be increasing
    if new_section_level > cur_section_level:

        if new_section_levels[-1] == 1:
            is_continuing_section = True

        common_level = cur_section_level

    elif new_section_level == cur_section_level:

        if new_section_levels[-1] == cur_section_levels[-1] + 1:
            is_continuing_section = True

        common_level = new_section_level - 1

    else:

        if new_section_levels[-1] == cur_section_levels[new_section_level - 1] + 1:
            is_continuing_section = True

        common_level = new_section_level - 1

    # The lists might have a common part which should be the same
    for i in range(common_level):
        if new_section_levels[i] != cur_section_levels[i]:
            is_continuing_section = False

    return is_continuing_section


def _clean_numbering_match(numbering: str) -> str:
    # Remove leading and trailing points or whitespaces
    numbering = LEADING_TRAILING_PUNCTUATION_PATTERN.sub("", numbering)

    # Consider empty numbering to be set at 0
    if len(numbering) <= 0:
        numbering = "0"

    return numbering


def parse_section_info(line: str) -> SectionInfo:

    # Detect pattern
    match_pattern = match(SECTION_TITLE_NODE, line)
    if not match_pattern:
        return SectionInfo(type=BodySection.NONE)

    # Extract dict
    match_dict = match_pattern.match_dict

    section = BodySection.from_string(match_dict.get("section_name", "unknown"))
    number = match_dict.get("number", "")
    text = match_dict.get("text")

    # Compute levels
    number = _clean_numbering_match(number)
    if ORDINAL_PATTERN.match(number):
        number = str(ordinal_str_to_int(number))
    if number == "0":
        _LOGGER.warning(f"Numbering parsing output none for section title: {line}")
        return SectionInfo(type=BodySection.NONE)
    levels = _number_to_levels(number)

    section_info = SectionInfo(
        type=section,
        number=number,
        levels=levels,
        text=text,
    )

    return section_info


def is_body_section(line: str) -> bool:
    section_info = parse_section_info(line)

    if section_info.type == BodySection.NONE:
        return False

    return True
