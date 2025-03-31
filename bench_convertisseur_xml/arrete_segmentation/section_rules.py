import re
from typing import List, Optional, Union

import roman

from bench_convertisseur_xml.regex_utils import PatternProxy, regex_tree, join_with_or
from bench_convertisseur_xml.regex_utils.regex_tree.execute import match
from .types import BodySection, SectionInfo


ROMAN_NUMERALS = r"(?:(?:X{0,3})(?:IX|IV|V?I{0,3}))"
NUMBERS = r"\d+"
LETTER = r"[a-zA-Z]"
NUMBERING = fr'(?:{NUMBERS}|{LETTER}|{ROMAN_NUMERALS})'
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

PUNCTUATION = r'[.\s\-:–]'

SECTION_NODE = regex_tree.Group(
    regex_tree.Sequence([
        r'^',
        regex_tree.Branching([
            # With section name - optional punctuation
            regex_tree.Sequence([
                fr'(?P<section_name>{join_with_or(SECTION_NAMES)})\s+',
                # Numbering pattern
                regex_tree.Branching([
                    r'(?P<number_first>1er)',
                    fr'(?P<number>{NUMBERING}(?:[.]{NUMBERING})*)',
                ]),
                # Optional punctuation that should be excluded from text
                fr'(?:{PUNCTUATION}*)',
            ]),
            # Without section name - mandatory punctuation
            regex_tree.Sequence([
                # Numbering pattern
                regex_tree.Branching([
                    r'(?P<number_first>1er)',
                    fr'(?P<number>{NUMBERING}(?:[.]{NUMBERING})*)',
                ]),
                # Mandatory punctuation that should be excluded from text
                fr'{PUNCTUATION}+',
            ]),
        ]),
        # Optional text group
        r'(?P<text>\s*(.+))?$',
    ]),
    group_name='section',
)


def _number_to_levels(number: str) -> Optional[List[int]]:

    number_split = number.split('.')
    level = len(number_split) - 1

    if level < 0:
        return None

    section_levels = [0] * (level+1)

    for i in range(level+1):

        cur_char = number_split[level-i]

        if ROMAN_NUMERALS_PATTERN.match(cur_char):
            cur_number = roman.fromRoman(cur_char)
        elif LETTER_PATTERN.match(cur_char):
            cur_number = ord(cur_char.lower()) - 96
        elif NUMBERS_PATTERN.match(cur_char):
            cur_number = int(cur_char)
        else:
            err_msg = f"Unsupported level conversion for {cur_char}"
            raise ValueError(err_msg)

        section_levels[level-i] = cur_number

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

        if new_section_levels[-1] == cur_section_levels[new_section_level-1] + 1:
            is_continuing_section = True

        common_level = new_section_level - 1

    # The lists might have a common part which should be the same
    for i in range(common_level):
        if new_section_levels[i] != cur_section_levels[i]:
            is_continuing_section = False

    return is_continuing_section


def parse_section_info(line: str) -> SectionInfo:
    match_pattern = match(SECTION_NODE, line)

    if not match_pattern:
        return SectionInfo(type=BodySection.NONE)

    match_dict = match_pattern.match_dict

    section = BodySection.from_string(match_dict.get('section_name', 'none'))

    if match_dict.get('number_first'):
        number = '1'
    else:
        number = match_dict.get('number', '0').rstrip('.')
    levels = _number_to_levels(number)

    text = match_dict.get('text')
    if text:
        # Remove starting separator such as '-' which might be catched in the title text
        text = re.sub(r'^[-–:\s]*', '', text)

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
