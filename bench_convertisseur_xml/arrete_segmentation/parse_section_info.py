"""Section parser."""


import re
from typing import TypedDict, Dict, Union, Tuple, List

from .config import section_from_name, BodySection
from bench_convertisseur_xml.parsing_utils.source_mapping import TextSegments, TextSegment


class _CountTextDict(TypedDict):
    count: int
    text: list[str]

AuthorizedSections = Dict[str, _CountTextDict]


class SectionInfo(TypedDict):
    type: BodySection
    level: int
    level_name: str
    number: str
    text: str


# Numbering patterns
ROMAN_NUMERALS = r"(?:(?:X{0,3})(?:IX|IV|V?I{0,3}))"
NUMBERS = r"\d+"
LETTERS = r"[a-zA-Z]"
NUMBER_ELEMENT = fr"(?:{ROMAN_NUMERALS}|{NUMBERS}|{LETTERS})"
HIERARCHICAL_NUMBER = fr"{NUMBER_ELEMENT}(?:\.{NUMBER_ELEMENT})*"

# Section names pattern
SECTION_NAMES = ["titre", "chapitre", "article"]
SECTION_ELEMENT = '|'.join(SECTION_NAMES)

# Groups
SECTION_GROUP = fr"^(?P<section_name>{SECTION_ELEMENT})"
NUMBER_GROUP = fr"((?P<number>{HIERARCHICAL_NUMBER})|(?P<number_first>1er))"
OPTIONAL_TEXT_GROUP = r"(?:\s+(?P<text>.+))?$"
TEXT_GROUP = r"(?P<text>(?:(?![\.,:;]$).)+)$"  # no punctuation

# Pattern for sections with title
SECTION_TITLE = (
    f"{SECTION_GROUP}"  # section name
    r"\s+"  # mandatory whitespace
    f"{NUMBER_GROUP}"  # hierarchical numerotation
    f"{OPTIONAL_TEXT_GROUP}"  # optional text
)

# Pattern for sections without title
SECTION_NO_TITLE = (
    f"^{NUMBER_GROUP}"  # hierarchical numerotation
    r"(?:\.\s|\s(-|–|:)\s)"  # mandatory point with whitespace or separator
    f"{TEXT_GROUP}"  # text
)


def section_name_from_number(number: str) -> str:
    number_split = number.split('.')
    last_char = number_split[-1]
    level = len(number_split) - 1

    section_name = "none"

    # If level is above 0 we assume it is a sub article
    if level > 0:
        section_name = "sous_article"
    # If first numerotation is roman numeral, we assume it is a title
    elif re.match(ROMAN_NUMERALS + "$", last_char, re.IGNORECASE):
        section_name = 'titre'
    # If first numerotation is letter, we assume it is a chapter
    elif re.match(LETTERS + "$", last_char, re.IGNORECASE):
        section_name = 'chapitre'
    # If first numerotation is number, we assume it is an article
    elif re.match(NUMBERS + "$", last_char):
        section_name = 'article'

    return section_name


def parse_number_group(match_dict: Dict) -> Tuple[str, int]:
    if match_dict.get('number_first'):
        number = '1'
    else:
        number = match_dict['number'].rstrip('.')

    # We might have a sub article with 4 digits
    number_split = number.split(".")
    level = len(number_split) - 1
    return number, level


def parse_section_info(
    line: TextSegment, 
    authorized_sections: Union[None, AuthorizedSections] = None
) -> SectionInfo:
    match_title = re.match(SECTION_TITLE, line.contents, re.IGNORECASE)
    match_no_title = re.match(SECTION_NO_TITLE, line.contents, re.IGNORECASE)

    section_name = "none"
    level = -1

    if match_title:
        section_name = match_title.group('section_name').lower()
        text = match_title.group('text') or ""
        number, level = parse_number_group(match_title.groupdict())
        if level >= 3:
            section_name = "sous_article"
        # Remove optional separators
        text = re.sub(r"^[-–:\s]*", "", text)

    if match_no_title:
        text = match_no_title.group('text') or ""
        number, level = parse_number_group(match_no_title.groupdict())
        if level >= 3:
            section_name = "sous_article"
        # Guess section_name from number
        section_name = section_name_from_number(number)

    level_name = f"{section_name}_{level}"

    section_info: SectionInfo
    if match_title or match_no_title and (not authorized_sections or level_name in authorized_sections):
        section_info = {
            "type": section_from_name(section_name),
            "level": level,
            "level_name": level_name,
            "number": number,
            "text": text,
        }
    else:
        section_info = {
            "type": section_from_name("none"),
            "level": -1,
            "level_name": "none_-1",
            "number": "",
            "text": "",
        }
    return section_info


def identify_unique_sections(lines: TextSegments) -> AuthorizedSections:
    unique_sections: AuthorizedSections = {}

    # Pass on whole content
    for line in lines:
        # Parse any possible section
        section_info = parse_section_info(line)

        level_name = section_info["level_name"]

        # We detected a section
        if level_name != "none_-1":

            # Already seen, we have one more
            if level_name in unique_sections:
                unique_sections[level_name]["count"] += 1
                unique_sections[level_name]["text"].append(section_info["text"])

            # Otherwise create counter
            else:
                unique_sections[level_name] = {"count": 1, "text": [section_info["text"]]}

    return _filter_max_level_sections(unique_sections)


def _filter_max_level_sections(unique_sections: AuthorizedSections) -> AuthorizedSections:
    # Group sections by their base type (without _number suffix)
    grouped_sections: Dict[str, List[str]] = {}

    for level_name in unique_sections:

        # Extract base name (e.g., 'article' from 'article_0')
        level_name_split = level_name.split("_")
        section_name = "_".join(level_name_split[:-1])
        level = level_name_split[-1]

        # Initialize group if not exists
        if section_name not in grouped_sections:
            grouped_sections[section_name] = []

        # Add section to its group
        grouped_sections[section_name].append(level)

    # Initialize output dictionaries
    authorized_sections: AuthorizedSections = {}

    # For each group, keep only the highest level section
    for section_name, levels in grouped_sections.items():

        # Find the maximum level in this group
        max_level = max(levels)

        # Keep only sections with the maximum level
        authorized_section = "_".join([section_name, max_level])

        # Add all max level sections to the result
        authorized_sections[authorized_section] = unique_sections[authorized_section]

    return authorized_sections