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
from typing import List, Optional, Tuple

import spacy

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
from arretify.utils.html_split_merge import regex_tree_match
from .types import TitleInfo


_LOGGER = logging.getLogger(__name__)

SPACY_MODEL = spacy.load("fr_dep_news_trf")


TITLE_PUNCTUATION_PATTERN_S = r"[.\s\-:]"
IS_NOT_ENDING_WITH_PUNCTUATION = r"(?!.*[.;:,]$)"
NUMBERING_THEN_OPT_NUMBERS_PATTERN_S = rf"{NUMBERING_PATTERN_S}([.\-]{NUMBERS_PATTERN_S})*\.?"
NUMBERING_THEN_OBL_NUMBERS_PATTERN_S = rf"{NUMBERING_PATTERN_S}([.\-]{NUMBERS_PATTERN_S})+\.?"

SECTION_NAMES_LIST = [
    r"annexe",
    r"titre",
    r"chapitre",
    r"article",
]

SECTION_NAMES_PATTERN_S = rf"{join_with_or(SECTION_NAMES_LIST)}"
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
                    rf"^(?P<section_name>{SECTION_NAMES_PATTERN_S})",
                    regex_tree.Branching(
                        [
                            # Title has no numbering
                            regex_tree.Sequence(
                                [
                                    # Punctuation before the end of the line
                                    rf"{TITLE_PUNCTUATION_PATTERN_S}*$",
                                ]
                            ),
                            # Title has numbering
                            regex_tree.Sequence(
                                [
                                    # Punctuation between section name and numbering
                                    rf"\s*{TITLE_PUNCTUATION_PATTERN_S}\s*",
                                    # Numbering pattern
                                    regex_tree.Branching(
                                        [
                                            rf"(?P<number>{ORDINAL_PATTERN_S})",
                                            rf"(?P<number>(\d|I|i)){EME_PATTERN_S}",
                                            rf"(?P<number>{NUMBERING_THEN_OPT_NUMBERS_PATTERN_S})",
                                        ],
                                    ),
                                    # Punctuation between numbering and text
                                    rf"{TITLE_PUNCTUATION_PATTERN_S}*",
                                    # Text group
                                    r"(?P<text>.*?)$",
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
                    rf"(?P<number>{NUMBERING_THEN_OBL_NUMBERS_PATTERN_S})",
                    # Punctuation between numbering and text
                    rf"{TITLE_PUNCTUATION_PATTERN_S}*",
                    # Text group
                    r"(?P<text>.*?)$",
                ],
            ),
            # This regex matches section names in arretes such as
            # 1 TITRE
            # 1 - Article
            regex_tree.Sequence(
                [
                    # Numbering pattern with only one integer
                    rf"^(?P<number>{NUMBERS_PATTERN_S}\.?)",
                    # Punctuation between section name and numbering
                    rf"\s*{TITLE_PUNCTUATION_PATTERN_S}\s*",
                    # Text group not ending with punctuation
                    rf"(?P<text>{IS_NOT_ENDING_WITH_PUNCTUATION}.*?)$",
                ],
            ),
        ],
    ),
    group_name="title",
)


def _split_at_first_verb(line: str) -> Tuple[str, Optional[str]]:
    """
    This function takes a complete string as input and outputs a tuple of string and eventually
    a second string.

    The input string might be a section title, an alinea, or both. If both, the section title
    and its following alinea are usually separated with a ":" character, which we use to split
    the line first.

    Then, the function converts each part of the line into a spacy doc and looks at its tokens.
    Whenever we fall upon a conjugated verb, the first string will contain all sentences until
    the one containing the verb. It forms the section title. And the second string might contain
    the following elements. It forms the alinea.

    Examples :

    line = "Date d'ouverture, durée et modalités: L'enquête se déroulera pendant 33 jours."
    _split_at_first_verb(line) ->
    title_text = "Date d'ouverture, durée et modalités:"
    alinea_text = "L'enquête se déroulera pendant 33 jours."
    """
    # Initialize alinea text
    alinea_text = None

    # Split sentences
    sentences = line.split(":")

    for i, sentence in enumerate(sentences):

        if sentence.strip():

            # POS tagging
            spacy_doc = SPACY_MODEL(sentence)

            for token in spacy_doc:

                # If a sentence contains a verb in finite form, not capitalized, then all
                # following text will be comprised in a new alinea distinct from the title
                # See : https://universaldependencies.org/u/feat/VerbForm.html
                is_verb = token.pos_ in {"AUX", "VERB"}
                is_finite_form = token.morph.get("VerbForm", default=None) == ["Fin"]
                is_lowercase = all(c == "x" for c in token.shape_)

                if is_verb and is_finite_form and is_lowercase:

                    _LOGGER.info(f"INFO - Split alinea contents in line: {line}")

                    # All parts until the verb form the section title
                    title_text = ":".join(sentences[:i])
                    # Following parts form the alinea
                    alinea_text = ":".join(sentences[i:])

                    break

    if not alinea_text:
        title_text = line

    return title_text, alinea_text


def parse_title_info(line: str) -> TitleInfo:
    # Detect pattern
    match_pattern = regex_tree_match([line], TITLE_NODE)
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

    # If the title contains an alinea, break it down in two lines
    if not text:
        title_text, alinea_text = text, None
    else:
        title_text, alinea_text = _split_at_first_verb(text)

    # Define title info
    title_info = TitleInfo(
        section_type=section_type,
        number=number,
        levels=levels,
        title_text=title_text,
        alinea_text=alinea_text,
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
