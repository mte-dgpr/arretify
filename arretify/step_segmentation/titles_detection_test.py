"""Test section parser."""

import unittest

from bs4 import BeautifulSoup

from arretify.types import SectionType
from arretify.parsing_utils.source_mapping import initialize_lines
from .types import TitleInfo
from .titles_detection import (
    is_title,
    parse_title_info,
    is_next_title,
)


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
        assert not is_title(text)

    def test_list_with_colon(self):
        text = "3. Liste ;"
        assert not is_title(text)

    def test_sentence_start_point(self):
        text = ". Ni 5,0 mg / 1"
        assert not is_title(text)

    def test_mister(self):
        text = "M. le Maire de"
        assert not is_title(text)

    def test_more_than_two_numbers(self):
        text = "27406 LOUVIERS"
        assert not is_title(text)

    def test_toc_no_name(self):
        text = "1. Titre ..... 5"
        assert not is_title(text)

    def test_toc(self):
        text = "Titre 1 - Titre ..... 5"
        assert not is_title(text)


class TestParseTitleInfo(unittest.TestCase):

    def setUp(self):
        self.soup = BeautifulSoup("", "html.parser")

    def test_title_with_roman_number(self):
        # Arrange
        lines = initialize_lines(["TITRE I - Premier titre"])

        # Act
        title_info = parse_title_info(lines[0].contents)

        # Assert
        assert title_info == TitleInfo(
            section_type=SectionType.TITRE,
            number="I",
            levels=[1],
            text="Premier titre",
        )

    def test_title_with_arabic_number(self):
        # Arrange
        lines = initialize_lines(["TITRE 1 - Autre titre"])

        # Act
        title_info = parse_title_info(lines[0].contents)

        # Assert
        assert title_info == TitleInfo(
            section_type=SectionType.TITRE,
            number="1",
            levels=[1],
            text="Autre titre",
        )

    def test_chapter_with_letter_without_dot(self):
        # Arrange
        lines = initialize_lines(["CHAPITRE A - Premier chapitre"])

        # Act
        title_info = parse_title_info(lines[0].contents)

        # Assert
        assert title_info == TitleInfo(
            section_type=SectionType.CHAPITRE,
            number="A",
            levels=[1],
            text="Premier chapitre",
        )

    def test_chapter_with_letter_with_dot(self):
        # Arrange
        lines = initialize_lines(["CHAPITRE A. - Premier chapitre"])

        # Act
        title_info = parse_title_info(lines[0].contents)

        # Assert
        assert title_info == TitleInfo(
            section_type=SectionType.CHAPITRE,
            number="A",
            levels=[1],
            text="Premier chapitre",
        )

    def test_article_with_arabic_number_without_dot(self):
        # Arrange
        lines = initialize_lines(["ARTICLE 1"])

        # Act
        title_info = parse_title_info(lines[0].contents)

        # Assert
        assert title_info == TitleInfo(
            section_type=SectionType.ARTICLE,
            number="1",
            levels=[1],
        )

    def test_article_with_first_number(self):
        # Arrange
        lines = initialize_lines(["ARTICLE 1er"])

        # Act
        title_info = parse_title_info(lines[0].contents)

        # Assert
        assert title_info == TitleInfo(
            section_type=SectionType.ARTICLE,
            number="1",
            levels=[1],
        )

    def test_article_with_arabic_number_with_dot(self):
        # Arrange
        lines = initialize_lines(["ARTICLE 1."])

        # Act
        title_info = parse_title_info(lines[0].contents)

        # Assert
        assert title_info == TitleInfo(
            section_type=SectionType.ARTICLE,
            number="1",
            levels=[1],
        )

    def test_hierarchical_chapter_with_letter_without_dot(self):
        # Arrange
        lines = initialize_lines(["CHAPITRE I.A - Premier chapitre"])

        # Act
        title_info = parse_title_info(lines[0].contents)

        # Assert
        assert title_info == TitleInfo(
            section_type=SectionType.CHAPITRE,
            number="I.A",
            levels=[1, 1],
            text="Premier chapitre",
        )

    def test_hierarchical_chapter_with_letter_with_dot(self):
        # Arrange
        lines = initialize_lines(["CHAPITRE I.A. - Premier chapitre"])

        # Act
        title_info = parse_title_info(lines[0].contents)

        # Assert
        assert title_info == TitleInfo(
            section_type=SectionType.CHAPITRE,
            number="I.A",
            levels=[1, 1],
            text="Premier chapitre",
        )

    def test_hierarchical_chapter_with_arabic_number_without_dot(
        self,
    ):
        # Arrange
        lines = initialize_lines(["CHAPITRE 1.1 Premier chapitre"])

        # Act
        title_info = parse_title_info(lines[0].contents)

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
        lines = initialize_lines(["ARTICLE 1.1.1 Premier article"])

        # Act
        title_info = parse_title_info(lines[0].contents)

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
        lines = initialize_lines(["ARTICLE 1.1.1.1 Premier sous article"])

        # Act
        title_info = parse_title_info(lines[0].contents)

        # Assert
        assert title_info == TitleInfo(
            section_type=SectionType.ARTICLE,
            number="1.1.1.1",
            levels=[1, 1, 1, 1],
            text="Premier sous article",
        )

    def test_hierarchical_article_with_arabic_number_with_letter(
        self,
    ):
        # Arrange
        lines = initialize_lines(["ARTICLE 1.A.3 - Premier article"])

        # Act
        title_info = parse_title_info(lines[0].contents)

        # Assert
        assert title_info == TitleInfo(
            section_type=SectionType.ARTICLE,
            number="1.A.3",
            levels=[1, 1, 3],
            text="Premier article",
        )

    def test_hierarchical_article_with_arabic_number_with_letter_and_dot(
        self,
    ):
        # Arrange
        lines = initialize_lines(["ARTICLE 1.A.3. - Premier article"])

        # Act
        title_info = parse_title_info(lines[0].contents)

        # Assert
        assert title_info == TitleInfo(
            section_type=SectionType.ARTICLE,
            number="1.A.3",
            levels=[1, 1, 3],
            text="Premier article",
        )

    def test_simple_title_no_name(self):
        # Arrange
        lines = initialize_lines(["1. TITRE"])

        # Act
        title_info = parse_title_info(lines[0].contents)

        # Assert
        assert title_info == TitleInfo(
            section_type=SectionType.UNKNOWN,
            number="1",
            levels=[1],
            text="TITRE",
        )

    def test_hierarchical_title_no_name(self):
        # Arrange
        lines = initialize_lines(["1.1.1 Article"])

        # Act
        title_info = parse_title_info(lines[0].contents)

        # Assert
        assert title_info == TitleInfo(
            section_type=SectionType.UNKNOWN,
            number="1.1.1",
            levels=[1, 1, 1],
            text="Article",
        )

    def test_sub_article_no_name(self):
        # Arrange
        lines = initialize_lines(["3.1. Sous-article"])

        # Act
        title_info = parse_title_info(lines[0].contents)

        # Assert
        assert title_info == TitleInfo(
            section_type=SectionType.UNKNOWN,
            number="3.1",
            levels=[3, 1],
            text="Sous-article",
        )

    def test_one_line_list_with_colon(self):
        # Arrange
        lines = initialize_lines(["1. Liste : a. Point b. Point"])

        # Act
        title_info = parse_title_info(lines[0].contents)

        # Assert
        assert title_info == TitleInfo(
            section_type=SectionType.UNKNOWN,
            number="1",
            levels=[1],
            text="Liste : a. Point b. Point",
        )

    def test_simple_no_space(self):
        # Arrange
        lines = initialize_lines(["ARTICLE 6-ARTICLE"])

        # Act
        title_info = parse_title_info(lines[0].contents)

        # Assert
        assert title_info == TitleInfo(
            section_type=SectionType.ARTICLE,
            number="6",
            levels=[6],
            text="ARTICLE",
        )

    def test_ocr_error_eme(self):
        # Arrange
        lines = initialize_lines(["ARTICLE 1erCeci est un titre"])

        # Act
        title_info = parse_title_info(lines[0].contents)

        # Assert
        assert title_info == TitleInfo(
            section_type=SectionType.ARTICLE,
            number="1",
            levels=[1],
            text="Ceci est un titre",
        )

    def test_chapter_joined_text(self):
        # Arrange
        lines = initialize_lines(["CHAPITRE 5.1CECI EST UN CHAPITRE"])

        # Act
        title_info = parse_title_info(lines[0].contents)

        # Assert
        assert title_info == TitleInfo(
            section_type=SectionType.CHAPITRE,
            number="5.1",
            levels=[5, 1],
            text="CECI EST UN CHAPITRE",
        )

    def test_article_ordinal(self):
        # Arrange
        lines = initialize_lines(["Article premier :"])

        # Act
        title_info = parse_title_info(lines[0].contents)

        # Assert
        assert title_info == TitleInfo(
            section_type=SectionType.ARTICLE,
            number="1",
            levels=[1],
            text=None,
        )

    def test_article_roman_eme(self):
        # Arrange
        lines = initialize_lines(["Article Ier :"])

        # Act
        title_info = parse_title_info(lines[0].contents)

        # Assert
        assert title_info == TitleInfo(
            section_type=SectionType.ARTICLE,
            number="I",
            levels=[1],
            text=None,
        )

    def test_title_no_point(self):
        # Arrange
        lines = initialize_lines(["1 Titre"])

        # Act
        title_info = parse_title_info(lines[0].contents)

        # Assert
        assert title_info == TitleInfo(
            section_type=SectionType.UNKNOWN,
            number="1",
            levels=[1],
            text="Titre",
        )

    def test_title_punctuation_middle(self):
        # Arrange
        lines = initialize_lines(["1  - Titre"])

        # Act
        title_info = parse_title_info(lines[0].contents)

        # Assert
        assert title_info == TitleInfo(
            section_type=SectionType.UNKNOWN,
            number="1",
            levels=[1],
            text="Titre",
        )

    def test_joined_text(self):
        # Arrange
        lines = initialize_lines(["5.1CECI EST UN CHAPITRE"])

        # Act
        title_info = parse_title_info(lines[0].contents)

        # Assert
        assert title_info == TitleInfo(
            section_type=SectionType.UNKNOWN,
            number="5.1",
            levels=[5, 1],
            text="CECI EST UN CHAPITRE",
        )
