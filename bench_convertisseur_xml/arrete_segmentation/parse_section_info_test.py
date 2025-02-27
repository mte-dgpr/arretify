"""Test section parser."""
import re
import unittest

from .parse_section_info import (
    are_sections_contiguous, parse_section_info, _section_to_levels, NUMBER_GROUP
)
from .config import BodySection
from bench_convertisseur_xml.parsing_utils.source_mapping import TextSegment


class TestNumberGroupRegex(unittest.TestCase):

    def setUp(self):
        self.pattern = re.compile(NUMBER_GROUP)

    def test_simple_number(self):
        # Arrange
        text = "123"

        # Act
        match = self.pattern.fullmatch(text)

        # Assert
        assert match is not None, "Should match simple number"
        assert match.group("number") == "123", "Group 'number' should equal '123'"

    def test_hierarchical_number(self):
        # Arrange
        text = "1.2.3"

        # Act
        match = self.pattern.fullmatch(text)

        # Assert
        assert match is not None, "Should match hierarchical number"
        assert match.group("number") == "1.2.3", "Group 'number' should equal '1.2.3'"

    def test_roman_numerals(self):
        # Arrange
        text = "X.II.IV"

        # Act
        match = self.pattern.fullmatch(text)

        # Assert
        assert match is not None, "Should match Roman numeral hierarchical number"
        assert match.group("number") == "X.II.IV", "Group 'number' should equal 'X.II.IV'"

    def test_letter(self):
        # Arrange
        text = "A.B.C"

        # Act
        match = self.pattern.fullmatch(text)

        # Assert
        assert match is not None, "Should match letter hierarchical number"
        assert match.group("number") == "A.B.C", "Group 'number' should equal 'A.B.C'"

    def test_first_number(self):
        # Arrange
        text = "1er"

        # Act
        match = self.pattern.fullmatch(text)

        # Assert
        assert match is not None, "Should match '1er'"
        assert match.group("number_first") == "1er", "Group 'number_first' should equal '1er'"


class TestSectionValidCases(unittest.TestCase):

    def test_title_with_roman_number(self):
        # Arrange
        text_segment = _make_text_segment("TITRE I - Premier titre")

        # Act
        result = parse_section_info(text_segment)

        # Assert
        assert result == {
            'type': BodySection.TITLE,
            "level": 0,
            "level_name": "titre_0",
            'number': 'I',
            'text': 'Premier titre',
            'levels': [1]
        }

    def test_title_with_arabic_number(self):
        # Arrange
        text_segment = _make_text_segment("TITRE 1 - Autre titre")

        # Act
        result = parse_section_info(text_segment)

        # Assert
        assert result == {
            'type': BodySection.TITLE,
            "level": 0,
            "level_name": "titre_0",
            'number': '1',
            'text': 'Autre titre',
            'levels': [1]
        }

    def test_chapter_with_letter_without_dot(self):
        # Arrange
        text_segment = _make_text_segment("CHAPITRE A - Premier chapitre")

        # Act
        result = parse_section_info(text_segment)

        # Assert
        assert result == {
            'type': BodySection.CHAPTER,
            "level": 0,
            "level_name": "chapitre_0",
            'number': 'A',
            'text': 'Premier chapitre',
            'levels': [1]
        }

    def test_chapter_with_letter_with_dot(self):
        # Arrange
        text_segment = _make_text_segment("CHAPITRE A. - Premier chapitre")

        # Act
        result = parse_section_info(text_segment)

        # Assert
        assert result == {
            'type': BodySection.CHAPTER,
            "level": 0,
            "level_name": "chapitre_0",
            'number': 'A',
            'text': 'Premier chapitre',
            'levels': [1]
        }

    def test_article_with_arabic_number_without_dot(self):
        # Arrange
        text_segment = _make_text_segment("ARTICLE 1")

        # Act
        result = parse_section_info(text_segment)

        # Assert
        assert result == {
            'type': BodySection.ARTICLE,
            "level": 0,
            "level_name": "article_0",
            'number': '1',
            'text': '',
            'levels': [1]
        }

    def test_article_with_first_number(self):
        # Arrange
        text_segment = _make_text_segment("ARTICLE 1er")

        # Act
        result = parse_section_info(text_segment)

        # Assert
        assert result == {
            'type': BodySection.ARTICLE,
            "level": 0,
            "level_name": "article_0",
            'number': '1',
            'text': '',
            'levels': [1]
        }

    def test_article_with_arabic_number_with_dot(self):
        # Arrange
        text_segment = _make_text_segment("ARTICLE 1.")

        # Act
        result = parse_section_info(text_segment)

        # Assert
        assert result == {
            'type': BodySection.ARTICLE,
            "level": 0,
            "level_name": "article_0",
            'number': '1',
            'text': '',
            'levels': [1]
        }

    def test_hierarchical_chapter_with_letter_without_dot(self):
        # Arrange
        text_segment = _make_text_segment("CHAPITRE I.A - Premier chapitre")

        # Act
        result = parse_section_info(text_segment)

        # Assert
        assert result == {
            'type': BodySection.CHAPTER,
            "level": 1,
            "level_name": "chapitre_1",
            'number': 'I.A',
            'text': 'Premier chapitre',
            'levels': [1, 1]
        }

    def test_hierarchical_chapter_with_letter_with_dot(self):
        # Arrange
        text_segment = _make_text_segment("CHAPITRE I.A. - Premier chapitre")

        # Act
        result = parse_section_info(text_segment)

        # Assert
        assert result == {
            'type': BodySection.CHAPTER,
            "level": 1,
            "level_name": "chapitre_1",
            'number': 'I.A',
            'text': 'Premier chapitre',
            'levels': [1, 1]
        }

    def test_hierarchical_chapter_with_arabic_number_without_dot(self):
        # Arrange
        text_segment = _make_text_segment("CHAPITRE 1.1 Premier chapitre")

        # Act
        result = parse_section_info(text_segment)

        # Assert
        assert result == {
            'type': BodySection.CHAPTER,
            "level": 1,
            "level_name": "chapitre_1",
            'number': '1.1',
            'text': 'Premier chapitre',
            'levels': [1, 1]
        }

    def test_hierarchical_article_with_arabic_number_without_dot(self):
        # Arrange
        text_segment = _make_text_segment("ARTICLE 1.1.1 Premier article")

        # Act
        result = parse_section_info(text_segment)

        # Assert
        assert result == {
            'type': BodySection.ARTICLE,
            "level": 2,
            "level_name": "article_2",
            'number': '1.1.1',
            'text': 'Premier article',
            'levels': [1, 1, 1]
        }

    def test_hierarchical_sub_article_with_arabic_number_without_dot(self):
        # Arrange
        text_segment = _make_text_segment("ARTICLE 1.1.1.1 Premier sous article")

        # Act
        result = parse_section_info(text_segment)

        # Assert
        assert result == {
            'type': BodySection.SUB_ARTICLE,
            "level": 3,
            "level_name": "sous_article_3",
            'number': '1.1.1.1',
            'text': 'Premier sous article',
            'levels': [1, 1, 1, 1]
        }

    def test_hierarchical_article_with_arabic_number_with_letter(self):
        # Arrange
        text_segment = _make_text_segment("ARTICLE 1.A.3 - Premier article")

        # Act
        result = parse_section_info(text_segment)

        # Assert
        assert result == {
            'type': BodySection.ARTICLE,
            "level": 2,
            "level_name": "article_2",
            'number': '1.A.3',
            'text': 'Premier article',
            'levels': [1, 1, 3]
        }

    def test_hierarchical_article_with_arabic_number_with_letter_and_dot(self):
        # Arrange
        text_segment = _make_text_segment("ARTICLE 1.A.3. - Premier article")

        # Act
        result = parse_section_info(text_segment)

        # Assert
        assert result == {
            'type': BodySection.ARTICLE,
            "level": 2,
            "level_name": "article_2",
            'number': '1.A.3',
            'text': 'Premier article',
            'levels': [1, 1, 3]
        }

    def test_sub_article_without_name_with_dot(self):
        # Arrange
        text_segment = _make_text_segment("1.2. - Sous-article")

        # Act
        result = parse_section_info(text_segment)

        # Assert
        assert result == {
            'type': BodySection.SUB_ARTICLE,
            "level": 1,
            "level_name": "sous_article_1",
            'number': '1.2',
            'text': 'Sous-article',
            'levels': [1, 2]
        }

    def test_sub_article_without_name_without_dot(self):
        # Arrange
        text_segment = _make_text_segment("1.2 - Sous-article")

        # Act
        result = parse_section_info(text_segment)

        # Assert
        assert result == {
            'type': BodySection.SUB_ARTICLE,
            "level": 1,
            "level_name": "sous_article_1",
            'number': '1.2',
            'text': 'Sous-article',
            'levels': [1, 2]
        }

    def test_title_without_name(self):
        # Arrange
        text_segment = _make_text_segment("I - Titre")

        # Act
        result = parse_section_info(text_segment)

        # Assert
        assert result == {
            'type': BodySection.TITLE,
            "level": 0,
            "level_name": "titre_0",
            'number': 'I',
            'text': 'Titre',
            'levels': [1]
        }

    # We decided to stop detecting these as section titles for now
    def test_article_without_name_with_dot(self):
        # Arrange
        text_segment = _make_text_segment("1. Article directement écrit comme une phrase.")

        # Act
        result = parse_section_info(text_segment)

        # Assert
        assert result == {
            'type': BodySection.NONE,
            "level": -1,
            "level_name": "none_-1",
            'number': "",
            'text': "",
            'levels': None
        }

    def test_random_sentence(self):
        # Arrange
        text_segment = _make_text_segment("Ceci est une phrase.")

        # Act
        result = parse_section_info(text_segment)

        # Assert
        assert result == {
            "type": BodySection.NONE,
            "level": -1,
            "level_name": "none_-1",
            "number": "",
            "text": "",
            "levels": None
        }

    def test_sentence_starting_with_letter(self):
        # Arrange
        text_segment = _make_text_segment("A la bonne journée")

        # Act
        result = parse_section_info(text_segment)

        # Assert
        assert result == {
            "type": BodySection.NONE,
            "level": -1,
            "level_name": "none_-1",
            "number": "",
            "text": "",
            "levels": None
        }

    def test_sentence_starting_with_arabic_number(self):
        # Arrange
        text_segment = _make_text_segment("1 On écrit directement un exemple")

        # Act
        result = parse_section_info(text_segment)

        # Assert
        assert result == {
            "type": BodySection.NONE,
            "level": -1,
            "level_name": "none_-1",
            "number": "",
            "text": "",
            "levels": None
        }

    def test_list_with_parenthesis(self):
        # Arrange
        text_segment = _make_text_segment("1) Ceci est une liste")

        # Act
        result = parse_section_info(text_segment)

        # Assert
        assert result == {
            "type": BodySection.NONE,
            "level": -1,
            "level_name": "none_-1",
            "number": "",
            "text": "",
            "levels": None
        }

    def test_list_with_dash(self):
        # Arrange
        text_segment = _make_text_segment("- Ceci est une liste")

        # Act
        result = parse_section_info(text_segment)

        # Assert
        assert result == {
            "type": BodySection.NONE,
            "level": -1,
            "level_name": "none_-1",
            "number": "",
            "text": "",
            "levels": None
        }

    def test_table(self):
        # Arrange
        text_segment = _make_text_segment("| Ceci est un tableau |")

        # Act
        result = parse_section_info(text_segment)

        # Assert
        assert result == {
            "type": BodySection.NONE,
            "level": -1,
            "level_name": "none_-1",
            "number": "",
            "text": "",
            "levels": None
        }

    def test_table_description(self):
        # Arrange
        text_segment = _make_text_segment("(*) Ceci est une description de tableau")

        # Act
        result = parse_section_info(text_segment)

        # Assert
        assert result == {
            "type": BodySection.NONE,
            "level": -1,
            "level_name": "none_-1",
            "number": "",
            "text": "",
            "levels": None
        }


class TestLevelList(unittest.TestCase):

    def test_title(self):
        # Arrange
        text = "I"
        level = 0

        # Act
        result = _section_to_levels(text, level)

        # Assert
        assert result == [1]

    def test_simple_number(self):
        # Arrange
        text = "123"
        level = 0

        # Act
        result = _section_to_levels(text, level)

        # Assert
        assert result == [123]

    def test_hierarchical_number(self):
        # Arrange
        text = "1.2.3"
        level = 2

        # Act
        result = _section_to_levels(text, level)

        # Assert
        result == [1, 2, 3]

    def test_roman_numerals(self):
        # Arrange
        text = "X.II.IV"
        level = 2

        # Act
        result = _section_to_levels(text, level)

        # Assert
        assert result == [10, 2, 4]

    def test_letter(self):
        # Arrange
        text = "A.B.C"
        level = 2

        # Act
        result = _section_to_levels(text, level)

        # Assert
        assert result == [1, 2, 3]

    def test_first_number(self):
        # Arrange
        text = "1er"
        level = 0

        # Act
        result = _section_to_levels(text, level)

        # Assert
        assert result == [1]

    def test_sub_article(self):
        # Arrange
        text = "1.4"
        level = 1

        # Act
        result = _section_to_levels(text, level)

        # Assert
        assert result == [1, 4]


class TestCompareLevelList(unittest.TestCase):

    def test_hierarchical_title_chapter(self):
        # Arrange
        cur_levels = [1]
        new_levels = [1, 1]

        # Act
        result = are_sections_contiguous(cur_levels, new_levels)
        
        # Assert
        assert result == True

    def test_hierarchical_chapter_article(self):
        # Arrange
        cur_levels = [1, 1]
        new_levels = [1, 1, 1]

        # Act
        result = are_sections_contiguous(cur_levels, new_levels)

        # Assert
        assert result == True

    def test_new_article(self):
        # Arrange
        cur_levels = [1, 1, 1]
        new_levels = [1, 1, 2]

        # Act
        result = are_sections_contiguous(cur_levels, new_levels)

        # Assert
        assert result == True

    def test_new_title_from_article(self):
        # Arrange
        cur_levels = [1, 8, 1]
        new_levels = [2]

        # Act
        result = are_sections_contiguous(cur_levels, new_levels)

        # Assert
        assert result == True

    def test_quoted_article(self):
        # Arrange
        cur_levels = [6]
        new_levels = [4, 3, 14]

        # Act
        result = are_sections_contiguous(cur_levels, new_levels)

        # Assert
        assert result == False

    def test_ocr_dot_not_detected(self):
        # Arrange
        cur_levels = [3, 1, 1]
        new_levels = [31, 2]

        # Act
        result = are_sections_contiguous(cur_levels, new_levels)

        # Assert
        assert result == False


def _make_text_segment(string: str) -> TextSegment:
    return TextSegment(contents=string, start=(0, 0), end=(0, 0))