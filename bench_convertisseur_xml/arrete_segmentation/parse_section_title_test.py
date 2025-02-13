"""Test section parser."""
import re
import unittest

from .parse_section_title import parse_section_title, NUMBER_GROUP
from .config import BodySection


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


def test_section_valid_cases():

    # Cas titre avec chiffre romain
    assert parse_section_title("TITRE I - Premier titre") == {
        'type': BodySection.TITLE,
        "level": 0,
        "level_name": "titre_0",
        'number': 'I',
        'text': 'Premier titre'
    }

    # Cas titre avec chiffre arabe
    assert parse_section_title("TITRE 1 - Autre titre") == {
        'type': BodySection.TITLE,
        "level": 0,
        "level_name": "titre_0",
        'number': '1',
        'text': 'Autre titre'
    }

    # Cas chapitre avec lettre sans point
    assert parse_section_title("CHAPITRE A - Premier chapitre") == {
        'type': BodySection.CHAPTER,
        "level": 0,
        "level_name": "chapitre_0",
        'number': 'A',
        'text': 'Premier chapitre'
    }

    # Cas chapitre avec lettre avec point
    assert parse_section_title("CHAPITRE A. - Premier chapitre") == {
        'type': BodySection.CHAPTER,
        "level": 0,
        "level_name": "chapitre_0",
        'number': 'A',
        'text': 'Premier chapitre'
    }

    # Cas article avec chiffre arabe sans point
    assert parse_section_title("ARTICLE 1") == {
        'type': BodySection.ARTICLE,
        "level": 0,
        "level_name": "article_0",
        'number': '1',
        'text': ''
    }

    # Cas article avec 1er
    assert parse_section_title("ARTICLE 1er") == {
        'type': BodySection.ARTICLE,
        "level": 0,
        "level_name": "article_0",
        'number': '1',
        'text': ''
    }

    # Cas article avec chiffre arabe avec point
    assert parse_section_title("ARTICLE 1.") == {
        'type': BodySection.ARTICLE,
        "level": 0,
        "level_name": "article_0",
        'number': '1',
        'text': ''
    }

    # Cas chapitre hiérarchique avec lettre sans point
    assert parse_section_title("CHAPITRE I.A - Premier chapitre") == {
        'type': BodySection.CHAPTER,
        "level": 1,
        "level_name": "chapitre_1",
        'number': 'I.A',
        'text': 'Premier chapitre'
    }

    # Cas chapitre hiérarchique avec lettre avec point
    assert parse_section_title("CHAPITRE I.A. - Premier chapitre") == {
        'type': BodySection.CHAPTER,
        "level": 1,
        "level_name": "chapitre_1",
        'number': 'I.A',
        'text': 'Premier chapitre'
    }

    # Cas chapitre hiérarchique avec chiffre sans point sans séparateur
    assert parse_section_title("CHAPITRE 1.1 Premier chapitre") == {
        'type': BodySection.CHAPTER,
        "level": 1,
        "level_name": "chapitre_1",
        'number': '1.1',
        'text': 'Premier chapitre'
    }

    # Cas article hiérarchique avec chiffre sans point sans séparateur
    assert parse_section_title("ARTICLE 1.1.1 Premier article") == {
        'type': BodySection.ARTICLE,
        "level": 2,
        "level_name": "article_2",
        'number': '1.1.1',
        'text': 'Premier article'
    }

    # Cas sous article hiérarchique avec chiffre sans point sans séparateur
    assert parse_section_title("ARTICLE 1.1.1.1 Premier sous article") == {
        'type': BodySection.SUB_ARTICLE,
        "level": 3,
        "level_name": "sous_article_3",
        'number': '1.1.1.1',
        'text': 'Premier sous article'
    }

    # Cas article hiérarchique avec chiffre arabe sans point
    assert parse_section_title("ARTICLE 1.A.3 - Premier article") == {
        'type': BodySection.ARTICLE,
        "level": 2,
        "level_name": "article_2",
        'number': '1.A.3',
        'text': 'Premier article'
    }
    # Cas article hiérarchique avec chiffre arabe avec point
    assert parse_section_title("ARTICLE 1.A.3. - Premier article") == {
        'type': BodySection.ARTICLE,
        "level": 2,
        "level_name": "article_2",
        'number': '1.A.3',
        'text': 'Premier article'
    }

    # Cas sous article sans nom avec point
    assert parse_section_title("1.2. - Sous-article") == {
        'type': BodySection.SUB_ARTICLE,
        "level": 1,
        "level_name": "sous_article_1",
        'number': '1.2',
        'text': 'Sous-article'
    }

    # Cas sous article sans nom sans point
    assert parse_section_title("1.2 - Sous-article") == {
        'type': BodySection.SUB_ARTICLE,
        "level": 1,
        "level_name": "sous_article_1",
        'number': '1.2',
        'text': 'Sous-article'
    }

    # Cas titre sans nom
    assert parse_section_title("I - Titre") == {
        'type': BodySection.TITLE,
        "level": 0,
        "level_name": "titre_0",
        'number': 'I',
        'text': 'Titre'
    }

    # Cas article sans nom avec point
    assert parse_section_title("1. Article directement écrit comme une phrase.") == {
        'type': BodySection.ARTICLE,
        "level": 0,
        "level_name": "article_0",
        'number': '1',
        'text': 'Article directement écrit comme une phrase.'
    }

    # Phrase quelconque
    assert parse_section_title("Ceci est une phrase.") == {
        "type": BodySection.NONE,
        "level": -1,
        "level_name": "none_-1",
        "number": "",
        "text": "",
    }

    # Phrase commençant par une lettre
    assert parse_section_title("A la bonne journée") == {
        "type": BodySection.NONE,
        "level": -1,
        "level_name": "none_-1",
        "number": "",
        "text": "",
    }

    # Phrase commençant par un chiffre arabe
    assert parse_section_title("1 On écrit directement un exemple") == {
        "type": BodySection.NONE,
        "level": -1,
        "level_name": "none_-1",
        "number": "",
        "text": "",
    }

    # Liste (on peut aussi trouver 1°)
    assert parse_section_title("1) Ceci est une liste") == {
        "type": BodySection.NONE,
        "level": -1,
        "level_name": "none_-1",
        "number": "",
        "text": "",
    }

    # Liste
    assert parse_section_title("- Ceci est une liste") == {
        "type": BodySection.NONE,
        "level": -1,
        "level_name": "none_-1",
        "number": "",
        "text": "",
    }

    # Tableau
    assert parse_section_title("| Ceci est un tableau |") == {
        "type": BodySection.NONE,
        "level": -1,
        "level_name": "none_-1",
        "number": "",
        "text": "",
    }

    # Tableau
    assert parse_section_title("(*) Ceci est une description de tableau") == {
        "type": BodySection.NONE,
        "level": -1,
        "level_name": "none_-1",
        "number": "",
        "text": "",
    }
