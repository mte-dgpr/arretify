"""Test section parser."""
import unittest

from bs4 import BeautifulSoup

from bench_convertisseur_xml.parsing_utils.source_mapping import initialize_lines
from .types import BodySection, SectionInfo
from .section_rules import are_sections_contiguous, parse_section_info, _number_to_levels


class TestLevelList(unittest.TestCase):

    def test_title(self):
        # Arrange
        number = "I"

        # Act
        result = _number_to_levels(number)

        # Assert
        assert result == [1]

    def test_simple_number(self):
        # Arrange
        number = "123"

        # Act
        result = _number_to_levels(number)

        # Assert
        assert result == [123]

    def test_hierarchical_number(self):
        # Arrange
        number = "1.2.3"

        # Act
        result = _number_to_levels(number)

        # Assert
        assert result == [1, 2, 3]

    def test_roman_numerals(self):
        # Arrange
        number = "X.II.IV"

        # Act
        result = _number_to_levels(number)

        # Assert
        assert result == [10, 2, 4]

    def test_letter(self):
        # Arrange
        number = "A.B.C"

        # Act
        result = _number_to_levels(number)

        # Assert
        assert result == [1, 2, 3]

    def test_first_number(self):
        # Arrange
        number = "1"

        # Act
        result = _number_to_levels(number)

        # Assert
        assert result == [1]

    def test_sub_article(self):
        # Arrange
        number = "1.4"

        # Act
        result = _number_to_levels(number)

        # Assert
        assert result == [1, 4]


class TestCompareLevelList(unittest.TestCase):

    def test_hierarchical_title_chapter(self):
        # Arrange
        current_levels = [1]
        new_levels = [1, 1]

        # Act
        result = are_sections_contiguous(current_levels, new_levels)

        # Assert
        assert result == True

    def test_hierarchical_chapter_article(self):
        # Arrange
        current_levels = [1, 1]
        new_levels = [1, 1, 1]

        # Act
        result = are_sections_contiguous(current_levels, new_levels)

        # Assert
        assert result == True

    def test_new_article(self):
        # Arrange
        current_levels = [1, 1, 1]
        new_levels = [1, 1, 2]

        # Act
        result = are_sections_contiguous(current_levels, new_levels)

        # Assert
        assert result == True

    def test_new_title_from_article(self):
        # Arrange
        current_levels = [1, 8, 1]
        new_levels = [2]

        # Act
        result = are_sections_contiguous(current_levels, new_levels)

        # Assert
        assert result == True

    def test_quoted_article(self):
        # Arrange
        current_levels = [6]
        new_levels = [4, 3, 14]

        # Act
        result = are_sections_contiguous(current_levels, new_levels)

        # Assert
        assert result == False

    def test_ocr_dot_not_detected(self):
        # Arrange
        current_levels = [3, 1, 1]
        new_levels = [31, 2]

        # Act
        result = are_sections_contiguous(current_levels, new_levels)

        # Assert
        assert result == False


class TestSectionValidCases(unittest.TestCase):

    def setUp(self):
        self.soup = BeautifulSoup("", "html.parser")

    def test_title_with_roman_number(self):
        # Arrange
        lines = initialize_lines(["TITRE I - Premier titre"])

        # Act
        section_info = parse_section_info(lines[0].contents)

        # Assert
        assert section_info == SectionInfo(
            type=BodySection.TITRE,
            number='I',
            levels=[1],
            text='Premier titre',
        )

    def test_title_with_arabic_number(self):
        # Arrange
        lines = initialize_lines(["TITRE 1 - Autre titre"])

        # Act
        section_info = parse_section_info(lines[0].contents)

        # Assert
        assert section_info == SectionInfo(
            type=BodySection.TITRE,
            number='1',
            levels=[1],
            text='Autre titre',
        )

    def test_chapter_with_letter_without_dot(self):
        # Arrange
        lines = initialize_lines(["CHAPITRE A - Premier chapitre"])

        # Act
        section_info = parse_section_info(lines[0].contents)

        # Assert
        assert section_info == SectionInfo(
            type=BodySection.CHAPITRE,
            number='A',
            levels=[1],
            text='Premier chapitre',
        )

    def test_chapter_with_letter_with_dot(self):
        # Arrange
        lines = initialize_lines(["CHAPITRE A. - Premier chapitre"])

        # Act
        section_info = parse_section_info(lines[0].contents)

        # Assert
        assert section_info == SectionInfo(
            type=BodySection.CHAPITRE,
            number='A',
            levels=[1],
            text='Premier chapitre',
        )

    def test_article_with_arabic_number_without_dot(self):
        # Arrange
        lines = initialize_lines(["ARTICLE 1"])

        # Act
        section_info = parse_section_info(lines[0].contents)

        # Assert
        assert section_info == SectionInfo(
            type=BodySection.ARTICLE,
            number='1',
            levels=[1],
        )

    def test_article_with_first_number(self):
        # Arrange
        lines = initialize_lines(["ARTICLE 1er"])

        # Act
        section_info = parse_section_info(lines[0].contents)

        # Assert
        assert section_info == SectionInfo(
            type=BodySection.ARTICLE,
            number='1',
            levels=[1],
        )

    def test_article_with_arabic_number_with_dot(self):
        # Arrange
        lines = initialize_lines(["ARTICLE 1."])

        # Act
        section_info = parse_section_info(lines[0].contents)

        # Assert
        assert section_info == SectionInfo(
            type=BodySection.ARTICLE,
            number='1',
            levels=[1],
        )

    def test_hierarchical_chapter_with_letter_without_dot(self):
        # Arrange
        lines = initialize_lines(["CHAPITRE I.A - Premier chapitre"])

        # Act
        section_info = parse_section_info(lines[0].contents)

        # Assert
        assert section_info == SectionInfo(
            type=BodySection.CHAPITRE,
            number='I.A',
            levels=[1, 1],
            text='Premier chapitre',
        )

    def test_hierarchical_chapter_with_letter_with_dot(self):
        # Arrange
        lines = initialize_lines(["CHAPITRE I.A. - Premier chapitre"])

        # Act
        section_info = parse_section_info(lines[0].contents)

        # Assert
        assert section_info == SectionInfo(
            type=BodySection.CHAPITRE,
            number='I.A',
            levels=[1, 1],
            text='Premier chapitre',
        )

    def test_hierarchical_chapter_with_arabic_number_without_dot(self):
        # Arrange
        lines = initialize_lines(["CHAPITRE 1.1 Premier chapitre"])

        # Act
        section_info = parse_section_info(lines[0].contents)

        # Assert
        assert section_info == SectionInfo(
            type=BodySection.CHAPITRE,
            number='1.1',
            levels=[1, 1],
            text='Premier chapitre',
        )

    def test_hierarchical_article_with_arabic_number_without_dot(self):
        # Arrange
        lines = initialize_lines(["ARTICLE 1.1.1 Premier article"])

        # Act
        section_info = parse_section_info(lines[0].contents)

        # Assert
        assert section_info == SectionInfo(
            type=BodySection.ARTICLE,
            number='1.1.1',
            levels=[1, 1, 1],
            text='Premier article',
        )

    def test_hierarchical_sub_article_with_arabic_number_without_dot(self):
        # Arrange
        lines = initialize_lines(["ARTICLE 1.1.1.1 Premier sous article"])

        # Act
        section_info = parse_section_info(lines[0].contents)

        # Assert
        assert section_info == SectionInfo(
            type=BodySection.ARTICLE,
            number='1.1.1.1',
            levels=[1, 1, 1, 1],
            text='Premier sous article',
        )

    def test_hierarchical_article_with_arabic_number_with_letter(self):
        # Arrange
        lines = initialize_lines(["ARTICLE 1.A.3 - Premier article"])

        # Act
        section_info = parse_section_info(lines[0].contents)

        # Assert
        assert section_info == SectionInfo(
            type=BodySection.ARTICLE,
            number='1.A.3',
            levels=[1, 1, 3],
            text='Premier article',
        )

    def test_hierarchical_article_with_arabic_number_with_letter_and_dot(self):
        # Arrange
        lines = initialize_lines(["ARTICLE 1.A.3. - Premier article"])

        # Act
        section_info = parse_section_info(lines[0].contents)

        # Assert
        assert section_info == SectionInfo(
            type=BodySection.ARTICLE,
            number='1.A.3',
            levels=[1, 1, 3],
            text='Premier article',
        )
