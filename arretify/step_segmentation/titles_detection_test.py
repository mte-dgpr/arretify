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
"""Test section parser."""

import unittest

from bs4 import BeautifulSoup

from arretify.types import SectionType

from .titles_detection import TITLE_NODE, is_next_title, parse_title_info
from .types import TitleInfo


class TestCompareLevelTitles(unittest.TestCase):

    def test_hierarchical_title_chapter(self):
        # Arrange
        current_global_levels = [1]
        current_title_levels = [1]
        new_title_levels = [1, 1]

        # Act
        result = is_next_title(current_global_levels, current_title_levels, new_title_levels)

        # Assert
        assert result is True

    def test_hierarchical_chapter_article(self):
        # Arrange
        current_global_levels = [1, 1]
        current_title_levels = [1, 1]
        new_title_levels = [1, 1, 1]

        # Act
        result = is_next_title(current_global_levels, current_title_levels, new_title_levels)

        # Assert
        assert result is True

    def test_new_article(self):
        # Arrange
        current_global_levels = [1, 1, 1]
        current_title_levels = [1, 1, 1]
        new_title_levels = [1, 1, 2]

        # Act
        result = is_next_title(current_global_levels, current_title_levels, new_title_levels)

        # Assert
        assert result is True

    def test_new_title_from_article(self):
        # Arrange
        current_global_levels = [1, 8, 1]
        current_title_levels = [1, 8, 1]
        new_title_levels = [2]

        # Act
        result = is_next_title(current_global_levels, current_title_levels, new_title_levels)

        # Assert
        assert result is True

    def test_quoted_article(self):
        # Arrange
        current_global_levels = [6]
        current_title_levels = [6]
        new_title_levels = [4, 3, 14]

        # Act
        result = is_next_title(current_global_levels, current_title_levels, new_title_levels)

        # Assert
        assert result is False

    def test_ocr_dot_not_detected(self):
        # Arrange
        current_global_levels = [3, 1, 1]
        current_title_levels = [3, 1, 1]
        new_title_levels = [31, 2]

        # Act
        result = is_next_title(current_global_levels, current_title_levels, new_title_levels)

        # Assert
        assert result is False

    def test_only_one_numbering_article(self):
        # Arrange
        current_global_levels = [12]
        current_title_levels = [12]
        new_title_levels = [13]

        # Act
        result = is_next_title(current_global_levels, current_title_levels, new_title_levels)

        # Assert
        assert result is True

    def test_only_one_numbering_chapitre(self):
        # Arrange
        current_global_levels = [12]
        current_title_levels = [1]
        new_title_levels = [2]

        # Act
        result = is_next_title(current_global_levels, current_title_levels, new_title_levels)

        # Assert
        assert result is True

    def test_only_one_numbering_unknown_1(self):
        # Arrange
        current_global_levels = [1, 1]
        current_title_levels = [1, 1]
        new_title_levels = [1, 2]

        # Act
        result = is_next_title(current_global_levels, current_title_levels, new_title_levels)

        # Assert
        assert result is True

    def test_only_one_numbering_unknown_2(self):
        # Arrange
        current_global_levels = [1, 2]
        current_title_levels = [1, 2]
        new_title_levels = [1, 2, 1]

        # Act
        result = is_next_title(current_global_levels, current_title_levels, new_title_levels)

        # Assert
        assert result is True

    def test_title_after_article(self):
        # Arrange
        current_global_levels = [1]
        current_title_levels = None
        new_title_levels = [1]

        # Act
        result = is_next_title(current_global_levels, current_title_levels, new_title_levels)

        # Assert
        assert result is True


class TestTitlePattern(unittest.TestCase):

    def test_table_description(self):
        text = "(1) à l'exception du monoxyde de carbone."
        assert TITLE_NODE.pattern.match(text) is None

    def test_list_with_colon(self):
        text = "3. Liste ;"
        assert TITLE_NODE.pattern.match(text) is None

    def test_sentence_start_point(self):
        text = ". Ni 5,0 mg / 1"
        assert TITLE_NODE.pattern.match(text) is None

    def test_mister(self):
        text = "M. le Maire de"
        assert TITLE_NODE.pattern.match(text) is None

    def test_chapter_no_numbering(self):
        # TODO: Case to solve
        text = "A. Chapitre"
        assert TITLE_NODE.pattern.match(text) is None

    def test_more_than_two_numbers(self):
        text = "27406 Code postal"
        assert TITLE_NODE.pattern.match(text) is None

    def test_toc_appendix(self):
        text = "Annexes :"
        assert TITLE_NODE.pattern.match(text) is None


class TestParseTitleInfo(unittest.TestCase):

    def setUp(self):
        self.soup = BeautifulSoup("", "html.parser")

    def test_title_with_roman_number(self):
        # Arrange
        line = "TITRE I - Premier titre"

        # Act
        title_info = parse_title_info(line)

        # Assert
        assert title_info == TitleInfo(
            section_type=SectionType.TITRE,
            number="I",
            levels=[1],
            text="Premier titre",
        )

    def test_title_with_arabic_number(self):
        # Arrange
        line = "TITRE 1 - Autre titre"

        # Act
        title_info = parse_title_info(line)

        # Assert
        assert title_info == TitleInfo(
            section_type=SectionType.TITRE,
            number="1",
            levels=[1],
            text="Autre titre",
        )

    def test_chapter_with_letter_without_dot(self):
        # Arrange
        line = "CHAPITRE A - Premier chapitre"

        # Act
        title_info = parse_title_info(line)

        # Assert
        assert title_info == TitleInfo(
            section_type=SectionType.CHAPITRE,
            number="A",
            levels=[1],
            text="Premier chapitre",
        )

    def test_chapter_with_letter_with_dot(self):
        # Arrange
        line = "CHAPITRE A. - Premier chapitre"

        # Act
        title_info = parse_title_info(line)

        # Assert
        assert title_info == TitleInfo(
            section_type=SectionType.CHAPITRE,
            number="A",
            levels=[1],
            text="Premier chapitre",
        )

    def test_article_with_arabic_number_without_dot(self):
        # Arrange
        line = "ARTICLE 1"

        # Act
        title_info = parse_title_info(line)

        # Assert
        assert title_info == TitleInfo(
            section_type=SectionType.ARTICLE,
            number="1",
            levels=[1],
        )

    def test_article_with_first_number(self):
        # Arrange
        line = "ARTICLE 1er"

        # Act
        title_info = parse_title_info(line)

        # Assert
        assert title_info == TitleInfo(
            section_type=SectionType.ARTICLE,
            number="1",
            levels=[1],
        )

    def test_article_with_arabic_number_with_dot(self):
        # Arrange
        line = "ARTICLE 1."

        # Act
        title_info = parse_title_info(line)

        # Assert
        assert title_info == TitleInfo(
            section_type=SectionType.ARTICLE,
            number="1",
            levels=[1],
        )

    def test_hierarchical_chapter_with_arabic_number_without_dot(
        self,
    ):
        # Arrange
        line = "CHAPITRE 1.1 Premier chapitre"

        # Act
        title_info = parse_title_info(line)

        # Assert
        assert title_info == TitleInfo(
            section_type=SectionType.CHAPITRE,
            number="1.1",
            levels=[1, 1],
            text="Premier chapitre",
        )

    def test_hierarchical_article_with_arabic_number_without_dot(
        self,
    ):
        # Arrange
        line = "ARTICLE 1.1.1 Premier article"

        # Act
        title_info = parse_title_info(line)

        # Assert
        assert title_info == TitleInfo(
            section_type=SectionType.ARTICLE,
            number="1.1.1",
            levels=[1, 1, 1],
            text="Premier article",
        )

    def test_hierarchical_sub_article_with_arabic_number_without_dot(
        self,
    ):
        # Arrange
        line = "ARTICLE 1.1.1.1 Premier sous article"

        # Act
        title_info = parse_title_info(line)

        # Assert
        assert title_info == TitleInfo(
            section_type=SectionType.ARTICLE,
            number="1.1.1.1",
            levels=[1, 1, 1, 1],
            text="Premier sous article",
        )

    def test_simple_title_no_name(self):
        # Arrange
        line = "1. TITRE"

        # Act
        title_info = parse_title_info(line)

        # Assert
        assert title_info == TitleInfo(
            section_type=SectionType.UNKNOWN,
            number="1",
            levels=[1],
            text="TITRE",
        )

    def test_hierarchical_title_no_name(self):
        # Arrange
        line = "1.1.1 Article"

        # Act
        title_info = parse_title_info(line)

        # Assert
        assert title_info == TitleInfo(
            section_type=SectionType.UNKNOWN,
            number="1.1.1",
            levels=[1, 1, 1],
            text="Article",
        )

    def test_sub_article_no_name(self):
        # Arrange
        line = "3.1. Sous-article"

        # Act
        title_info = parse_title_info(line)

        # Assert
        assert title_info == TitleInfo(
            section_type=SectionType.UNKNOWN,
            number="3.1",
            levels=[3, 1],
            text="Sous-article",
        )

    def test_simple_no_space(self):
        # Arrange
        line = "ARTICLE 6-ARTICLE"

        # Act
        title_info = parse_title_info(line)

        # Assert
        assert title_info == TitleInfo(
            section_type=SectionType.ARTICLE,
            number="6",
            levels=[6],
            text="ARTICLE",
        )

    def test_ocr_error_eme(self):
        # Arrange
        line = "ARTICLE 1erTitre"

        # Act
        title_info = parse_title_info(line)

        # Assert
        assert title_info == TitleInfo(
            section_type=SectionType.ARTICLE,
            number="1",
            levels=[1],
            text="Titre",
        )

    def test_chapter_joined_text(self):
        # Arrange
        line = "CHAPITRE 5.1CHAPITRE"

        # Act
        title_info = parse_title_info(line)

        # Assert
        assert title_info == TitleInfo(
            section_type=SectionType.CHAPITRE,
            number="5.1",
            levels=[5, 1],
            text="CHAPITRE",
        )

    def test_article_ordinal(self):
        # Arrange
        line = "Article premier :"

        # Act
        title_info = parse_title_info(line)

        # Assert
        assert title_info == TitleInfo(
            section_type=SectionType.ARTICLE,
            number="1",
            levels=[1],
            text=None,
        )

    def test_article_roman_eme(self):
        # Arrange
        line = "Article Ier :"

        # Act
        title_info = parse_title_info(line)

        # Assert
        assert title_info == TitleInfo(
            section_type=SectionType.ARTICLE,
            number="I",
            levels=[1],
            text=None,
        )

    def test_title_no_point(self):
        # Arrange
        line = "1 Titre"

        # Act
        title_info = parse_title_info(line)

        # Assert
        assert title_info == TitleInfo(
            section_type=SectionType.UNKNOWN,
            number="1",
            levels=[1],
            text="Titre",
        )

    def test_title_punctuation_middle(self):
        # Arrange
        line = "1  - Titre"

        # Act
        title_info = parse_title_info(line)

        # Assert
        assert title_info == TitleInfo(
            section_type=SectionType.UNKNOWN,
            number="1",
            levels=[1],
            text="Titre",
        )

    def test_hyphen_before_numbering(self):
        # Arrange
        line = "Article - 1.2.3. Article"

        # Act
        title_info = parse_title_info(line)

        # Assert
        assert title_info == TitleInfo(
            section_type=SectionType.ARTICLE,
            number="1.2.3",
            levels=[1, 2, 3],
            text="Article",
        )

    def test_hyphen_in_numbering(self):
        # Arrange
        line = "Article 2-1 Article"

        # Act
        title_info = parse_title_info(line)

        # Assert
        assert title_info == TitleInfo(
            section_type=SectionType.ARTICLE,
            number="2-1",
            levels=[2, 1],
            text="Article",
        )

    def test_chapter(self):
        # Arrange
        line = "Chapitre A - Chapitre"

        # Act
        title_info = parse_title_info(line)

        # Assert
        assert title_info == TitleInfo(
            section_type=SectionType.CHAPITRE,
            number="A",
            levels=[1],
            text="Chapitre",
        )

    def test_article_no_numbering_ending_punctuation(self):
        # Arrange
        line = "2.1 - Article."

        # Act
        title_info = parse_title_info(line)

        # Assert
        assert title_info == TitleInfo(
            section_type=SectionType.UNKNOWN,
            number="2.1",
            levels=[2, 1],
            text="Article.",
        )

    def test_chapter_no_space(self):
        # Arrange
        line = "5.3CHAPITRE"

        # Act
        title_info = parse_title_info(line)

        # Assert
        assert title_info == TitleInfo(
            section_type=SectionType.UNKNOWN,
            number="5.3",
            levels=[5, 3],
            text="CHAPITRE",
        )

    def test_roman_no_section_name(self):
        # Arrange
        line = "II.1.1 - Sous-titre"

        # Act
        title_info = parse_title_info(line)

        # Assert
        assert title_info == TitleInfo(
            section_type=SectionType.UNKNOWN,
            number="II.1.1",
            levels=[2, 1, 1],
            text="Sous-titre",
        )

    def test_appendix(self):
        # Arrange
        line = "ANNEXE "

        # Act
        title_info = parse_title_info(line)

        # Assert
        assert title_info == TitleInfo(
            section_type=SectionType.ANNEXE,
            number="",
            levels=None,
            text=None,
        )

    def test_article_no_name_no_space(self):
        # Arrange
        line = "2-Article"

        # Act
        title_info = parse_title_info(line)

        # Assert
        assert title_info == TitleInfo(
            section_type=SectionType.UNKNOWN,
            number="2",
            levels=[2],
            text="Article",
        )

    def test_chapter_letter_v_roman(self):
        # Arrange
        line = "Chapitre C - Chapitre"

        # Act
        title_info = parse_title_info(line)

        # Assert
        assert title_info == TitleInfo(
            section_type=SectionType.CHAPITRE,
            number="C",
            levels=[3],
            text="Chapitre",
        )

    def test_title_long_roman(self):
        # Arrange
        line = "Titre XIV - Titre"

        # Act
        title_info = parse_title_info(line)

        # Assert
        assert title_info == TitleInfo(
            section_type=SectionType.TITRE,
            number="XIV",
            levels=[14],
            text="Titre",
        )

    def test_title_max_roman(self):
        # Arrange
        line = "Titre XXXIX - Titre"

        # Act
        title_info = parse_title_info(line)

        # Assert
        assert title_info == TitleInfo(
            section_type=SectionType.TITRE,
            number="XXXIX",
            levels=[39],
            text="Titre",
        )

    def test_title_with_wrongly_accented_char(self):
        # Arrange
        line = "ANNEXÉ 3 - Attestation du Prestataire"

        # Act
        title_info = parse_title_info(line)

        # Assert
        assert title_info == TitleInfo(
            section_type=SectionType.ANNEXE,
            number="3",
            levels=[3],
            text="Attestation du Prestataire",
        )
