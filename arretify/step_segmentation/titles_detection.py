import logging
from typing import List, Optional


from arretify.types import SectionType
from arretify.parsing_utils.patterns import LEADING_TRAILING_PUNCTUATION_PATTERN
from arretify.parsing_utils.numbering import (
    EME_PATTERN_S,
    ORDINAL_PATTERN_S,
    ORDINAL_PATTERN,
    NUMBERS_PATTERN_S,
    NUMBERING_PATTERN_S,
    ordinal_str_to_int,
    str_to_levels,
    are_levels_contiguous,
)
from arretify.regex_utils import (
    regex_tree,
    join_with_or,
    Settings,
)
from arretify.regex_utils.regex_tree.execute import match
from .types import TitleInfo


_LOGGER = logging.getLogger(__name__)


SECTION_NAMES = [
    r"annexe",
    r"titre",
    r"chapitre",
    r"article",
]
"""Detect all section names."""

TITLE_NODE = regex_tree.Group(
    regex_tree.Branching(
        [
            # This regex matches section names in arretes such as
            # Annexe 1
            # Titre 1
            # Titre I - TITRE
            # Titre 1. TITRE
            # Titre 2 TITRE
            # Chapitre 1.A
            # Chapitre 1.2 - CHAPITRE
            # Chapitre A. CHAPITRE
            # Article 1.2.3 - Article
            # Article 1.2.3
            # Article 1.2.3. - Article.
            # Title is split into a section name, a numbering pattern and an optional text group
            regex_tree.Sequence(
                [
                    # Section name
                    rf"^(?P<section_name>{join_with_or(SECTION_NAMES)})",
                    # Mandatory space or punctuation
                    # This prevents detecting a word beginning with a section name pattern
                    # as a section name plus numbering
                    r"[\s\-:]",
                    # Numbering pattern
                    regex_tree.Branching(
                        [
                            rf"(?P<number>{ORDINAL_PATTERN_S})",
                            rf"(?P<number>(\d|I|i)){EME_PATTERN_S}",
                            rf"(?P<number>{NUMBERING_PATTERN_S}(?:[.]{NUMBERING_PATTERN_S})*)",
                        ],
                        settings=Settings(ignore_accents=False),
                    ),
                    # Do not catch the optional punctuation
                    r"(?:[.\s\-:]*)",
                    # Optional text group not ending with 5 points and numbers (ToC)
                    r"(?P<text>\s*(?:(?!\.{5}\s+\d+).)*)?$",
                ]
            ),
            # This regex matches section names in arretes such as
            # 1 TITRE
            # 1.2 - CHAPITRE
            # 1.A. CHAPITRE
            # 1.2.3 - Article
            # Title is split into a numbering pattern and a text group
            regex_tree.Sequence(
                [
                    # Numbering pattern with integer as first number
                    rf"(?P<number>{NUMBERS_PATTERN_S}(?:[.]{NUMBERING_PATTERN_S})*)",
                    # Do not catch the optional punctuation
                    r"(?:[.\s\-:]*)",
                    # Text group without ending punctuation or 5 points and numbers (ToC)
                    r"(?P<text>\s*[A-Za-z](?:(?!\.{5}\s+\d+).)+?(?<![.;:,]))$",
                ],
                settings=Settings(ignore_accents=False),
            ),
        ]
    ),
    group_name="title",
)


def is_title(line: str) -> bool:
    return bool(match(TITLE_NODE, line))


def parse_title_info(line: str) -> TitleInfo:

    # Detect pattern
    match_pattern = match(TITLE_NODE, line)
    assert match_pattern, "Only use parse function when match pattern exists!"

    # Extract dict
    match_dict = match_pattern.match_dict

    section_type = SectionType.from_string(match_dict.get("section_name", "unknown"))
    number = match_dict.get("number", "")
    text = match_dict.get("text")

    # Compute levels
    number = LEADING_TRAILING_PUNCTUATION_PATTERN.sub("", number)
    if len(number) <= 0:
        _LOGGER.warning(f"Numbering parsing output none for title: {line}")
    if ORDINAL_PATTERN.match(number):
        number = str(ordinal_str_to_int(number))
    levels = str_to_levels(number)

    title_info = TitleInfo(
        section_type=section_type,
        number=number,
        levels=levels,
        text=text,
    )

    return title_info


def is_next_title(
    current_global_levels: Optional[List[int]],
    current_title_levels: Optional[List[int]],
    new_title_levels: Optional[List[int]],
) -> bool:
    return are_levels_contiguous(current_global_levels, new_title_levels) or are_levels_contiguous(
        current_title_levels, new_title_levels
    )
