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
from typing import Optional, Tuple
import logging

import spacy

from arretify.parsing_utils.patterns import LEADING_TRAILING_WHITESPACE_PATTERN


_LOGGER = logging.getLogger(__name__)


SPACY_MODEL = spacy.load("fr_dep_news_trf")


def split_at_first_verb(line: str) -> Tuple[Optional[str], Optional[str]]:
    """
    This function takes a complete string as input and outputs one to two strings.

    The input string might be a section title, an alinea, or both. If both, the section title
    and its following alinea are usually separated with a ":" character, which we use to split
    the line first.

    Then, the function converts each part of the line into a spacy doc and looks at its tokens.
    Whenever we fall upon a conjugated verb, the first string will contain all parts until
    the one containing the verb. It forms the section title. And the second string might contain
    the following parts. It forms the alinea.

    Examples :

    line = "Date d'ouverture, durée et modalités: L'enquête se déroulera pendant 33 jours."
    _split_at_first_verb(line) ->
    until_verb_or_all = "Date d'ouverture, durée et modalités:"
    after_verb = "L'enquête se déroulera pendant 33 jours."
    """
    # Initialize texts
    until_verb_or_all: Optional[str] = None
    after_verb: Optional[str] = None

    # Split parts
    parts = line.split(":")

    for i, part in enumerate(parts):

        if part.strip():

            # POS tagging
            spacy_doc = SPACY_MODEL(part)

            for token in spacy_doc:

                # If a part contains a verb in finite form, not capitalized, then all
                # following text will be comprised in a new alinea distinct from the title
                # Only verbs or auxiliary verbs
                is_verb = token.pos_ in {"AUX", "VERB"}
                # Only finite forms
                # See : https://universaldependencies.org/u/feat/VerbForm.html
                is_finite_form = token.morph.get("VerbForm", default=None) == ["Fin"]
                # Either the word contains a single letter then it should be lowercase e.g. "a"
                # or it contains multiple letters then all letters except the first one should be
                # lowercase e.g. "Est" or "est" but not "EST"
                is_lowercase = (len(token.shape_) <= 1 and token.shape_.islower()) or (
                    len(token.shape_) > 1 and token.shape_[1:].islower()
                )

                if is_verb and is_finite_form and is_lowercase:

                    _LOGGER.info(f"INFO - Split alinea contents in line: {line}")

                    # All parts until the verb form the section title
                    # TODO: improve the split and merging of strings
                    until_verb_or_all = ":".join(parts[:i])
                    if len(until_verb_or_all) <= 0:
                        until_verb_or_all = None
                    elif len(parts) >= 2 and until_verb_or_all:
                        until_verb_or_all += ":"
                    if until_verb_or_all:
                        until_verb_or_all = LEADING_TRAILING_WHITESPACE_PATTERN.sub(
                            "", until_verb_or_all
                        )
                    # Following parts form the alinea
                    after_verb = ":".join(parts[i:])
                    after_verb = LEADING_TRAILING_WHITESPACE_PATTERN.sub("", after_verb)

                    break

    if not after_verb:
        until_verb_or_all = line

    return until_verb_or_all, after_verb
