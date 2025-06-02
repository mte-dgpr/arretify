import re
from typing import List, Optional

import roman

from arretify.regex_utils import PatternProxy
from .patterns import LETTER_PATTERN_S


# "°" is a common OCR error for superscript "è"
# as in "4ᵉ" for "4ème".
EME_PATTERN_S = r"(er|ème|è|°|ᵉ)"

ORDINAL_PATTERN_S = (
    r"(premier)|(deuxième|second)|(troisième)|(quatrième)|(cinquième)|(sixième)"
    r"|(septi[eè]me)|(huitième)|(neuvième)|(dixième)|(onzième)|(douzième)|(treizième)"
)

ORDINAL_PATTERN = PatternProxy(ORDINAL_PATTERN_S)

# Roman numerals limited to 49
ROMAN_NUMERALS_PATTERN_S = r"(?:(?:X{0,3})(?:IX|IV|V?I{0,3}))"

ENDING_ROMAN_NUMERALS_PATTERN = PatternProxy(ROMAN_NUMERALS_PATTERN_S + "$")

# One or two numbers
NUMBERS_PATTERN_S = r"\d{1,2}"

ENDING_NUMBERS_PATTERN = PatternProxy(NUMBERS_PATTERN_S + "$")

# Letter used in numbering
ENDING_LETTER_PATTERN = PatternProxy(LETTER_PATTERN_S + "$")

# All types of numbering patterns
NUMBERING_PATTERN_S = rf"(?:{NUMBERS_PATTERN_S}|{LETTER_PATTERN_S}|{ROMAN_NUMERALS_PATTERN_S})"


def ordinal_str_to_int(ordinal: str) -> int:
    ordinal_match = re.match(ORDINAL_PATTERN_S, ordinal, re.IGNORECASE)
    if not ordinal_match:
        raise RuntimeError("Ordinal match unexpectedly failed")

    for i in range(1, len(ordinal_match.groups()) + 1):
        if ordinal_match.group(i):
            return i

    raise RuntimeError(f"Ordinal not found {ordinal}")


def str_to_levels(number: str) -> Optional[List[int]]:

    number_split = number.replace(".", " ").replace("-", " ").split()
    level = len(number_split) - 1

    if level < 0:
        return None

    levels = [0] * (level + 1)

    for i in range(level + 1):

        cur_char = number_split[level - i]

        if ENDING_ROMAN_NUMERALS_PATTERN.match(cur_char):
            cur_number = roman.fromRoman(cur_char)
        elif ENDING_LETTER_PATTERN.match(cur_char):
            cur_number = ord(cur_char.lower()) - 96
        elif ENDING_NUMBERS_PATTERN.match(cur_char):
            cur_number = int(cur_char)
        else:
            err_msg = f"Unsupported level conversion for {cur_char}"
            raise ValueError(err_msg)

        levels[level - i] = cur_number

    return levels


def are_levels_contiguous(
    cur_levels: Optional[List[int]],
    new_levels: Optional[List[int]],
) -> bool:

    if not new_levels:
        return False

    if not cur_levels:
        return True

    cur_level = len(cur_levels)
    new_level = len(new_levels)

    is_continuing_levels = False

    # First the new levels should be increasing
    if new_level > cur_level:

        if new_levels[-1] == 1:
            is_continuing_levels = True

        common_level = cur_level

    elif new_level == cur_level:

        if new_levels[-1] == cur_levels[-1] + 1:
            is_continuing_levels = True

        common_level = new_level - 1

    else:

        if new_levels[-1] == cur_levels[new_level - 1] + 1:
            is_continuing_levels = True

        common_level = new_level - 1

    # The lists might have a common part which should be the same
    for i in range(common_level):
        if new_levels[i] != cur_levels[i]:
            is_continuing_levels = False

    return is_continuing_levels
