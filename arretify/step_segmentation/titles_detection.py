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
)
from arretify.regex_utils.regex_tree.execute import match
from .document_elements import TABLE_OF_CONTENTS_PAGING_PATTERN_S
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
            # Chapitre 1.2 - CHAPITRE
            # Chapitre A. CHAPITRE
            # Article 1.2.3 - Article
            # Article 1.2.3
            # Article 1.2.3. - Article.
            regex_tree.Sequence(
                [
                    # Section name
                    rf"^(?P<section_name>{join_with_or(SECTION_NAMES)})",
                    regex_tree.Branching(
                        [
                            # Title has no numbering
                            regex_tree.Sequence(
                                [
                                    # Do not catch the punctuation
                                    r"(?:[.\s\-:]*)$",
                                ]
                            ),
                            # Title has numbering
                            regex_tree.Sequence(
                                [
                                    # Do not catch punctuation, assert at least one space
                                    # This prevents detecting a word beginning with a section name
                                    # pattern as a section name plus numbering
                                    r"(?:[.\-:]*\s[.\-:\s]*)",
                                    # Numbering pattern
                                    regex_tree.Branching(
                                        [
                                            rf"(?P<number>{ORDINAL_PATTERN_S})",
                                            rf"(?P<number>(\d|I|i)){EME_PATTERN_S}",
                                            # Only first can be roman or letter
                                            rf"(?P<number>{NUMBERING_PATTERN_S}"
                                            rf"(?:[.\-]{NUMBERS_PATTERN_S})*)",
                                        ],
                                    ),
                                    # Do not catch the punctuation
                                    r"(?:[.\s\-:]*)",
                                    # Optional text group not ending with 5 points and numbers (ToC)
                                    r"(?P<text>\s*[A-Za-z]"
                                    rf"(?:(?!{TABLE_OF_CONTENTS_PAGING_PATTERN_S}).)*)?$",
                                ]
                            ),
                        ],
                    ),
                ],
            ),
            # This regex matches section names in arretes such as
            # 1.2 - CHAPITRE
            # 1.2.3 - Article
            # 1.2.3. - Article.
            regex_tree.Sequence(
                [
                    # Numbering pattern with at least two numbers
                    rf"^(?P<number>{NUMBERING_PATTERN_S}(?:[.\-]{NUMBERS_PATTERN_S})+)",
                    # Do not catch punctuation
                    r"(?:[.\s\-:]*)",
                    # Text group not ending with 5 points and numbers (ToC)
                    (rf"(?P<text>\s*[A-Za-z](?:(?!{TABLE_OF_CONTENTS_PAGING_PATTERN_S})" r".)+?)$"),
                ],
            ),
            # This regex matches section names in arretes such as
            # 1 TITRE
            # 1 - Article
            regex_tree.Sequence(
                [
                    # Numbering pattern with only one integer
                    rf"^(?P<number>{NUMBERS_PATTERN_S})",
                    # Do not catch punctuation, assert at least one space
                    # This prevents detecting a word as a numbering plus text group
                    r"(?:[.\-:]*\s[.\-:\s]*)",
                    # Text group not ending with punctuation or 5 points and numbers (ToC)
                    (
                        rf"(?P<text>\s*[A-Za-z](?:(?!{TABLE_OF_CONTENTS_PAGING_PATTERN_S})"
                        r".)+?(?<![.;:,]))$"
                    ),
                ],
            ),
        ],
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
