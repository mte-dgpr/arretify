"""Test section parser."""


from .parse_section import parse_section
from .config import BodySection


def test_section_valid_cases():

    # Cas titre avec chiffre romain
    assert parse_section("TITRE I - Premier titre") == {
        'type': BodySection.TITLE,
        "level": 0,
        "level_name": "titre_0",
        'number': 'I',
        'text': 'Premier titre'
    }

    # Cas titre avec chiffre arabe
    assert parse_section("TITRE 1 - Autre titre") == {
        'type': BodySection.TITLE,
        "level": 0,
        "level_name": "titre_0",
        'number': '1',
        'text': 'Autre titre'
    }

    # Cas chapitre avec lettre sans point
    assert parse_section("CHAPITRE A - Premier chapitre") == {
        'type': BodySection.CHAPTER,
        "level": 0,
        "level_name": "chapitre_0",
        'number': 'A',
        'text': 'Premier chapitre'
    }

    # Cas chapitre avec lettre avec point
    assert parse_section("CHAPITRE A. - Premier chapitre") == {
        'type': BodySection.CHAPTER,
        "level": 0,
        "level_name": "chapitre_0",
        'number': 'A',
        'text': 'Premier chapitre'
    }

    # Cas article avec chiffre arabe sans point
    assert parse_section("ARTICLE 1") == {
        'type': BodySection.ARTICLE,
        "level": 0,
        "level_name": "article_0",
        'number': '1',
        'text': ''
    }

    # Cas article avec chiffre arabe avec point
    assert parse_section("ARTICLE 1.") == {
        'type': BodySection.ARTICLE,
        "level": 0,
        "level_name": "article_0",
        'number': '1',
        'text': ''
    }

    # Cas chapitre hiérarchique avec lettre sans point
    assert parse_section("CHAPITRE I.A - Premier chapitre") == {
        'type': BodySection.CHAPTER,
        "level": 1,
        "level_name": "chapitre_1",
        'number': 'I.A',
        'text': 'Premier chapitre'
    }

    # Cas chapitre hiérarchique avec lettre avec point
    assert parse_section("CHAPITRE I.A. - Premier chapitre") == {
        'type': BodySection.CHAPTER,
        "level": 1,
        "level_name": "chapitre_1",
        'number': 'I.A',
        'text': 'Premier chapitre'
    }

    # Cas chapitre hiérarchique avec chiffre sans point sans séparateur
    assert parse_section("CHAPITRE 1.1 Premier chapitre") == {
        'type': BodySection.CHAPTER,
        "level": 1,
        "level_name": "chapitre_1",
        'number': '1.1',
        'text': 'Premier chapitre'
    }

    # Cas article hiérarchique avec chiffre sans point sans séparateur
    assert parse_section("ARTICLE 1.1.1 Premier article") == {
        'type': BodySection.ARTICLE,
        "level": 2,
        "level_name": "article_2",
        'number': '1.1.1',
        'text': 'Premier article'
    }

    # Cas sous article hiérarchique avec chiffre sans point sans séparateur
    assert parse_section("ARTICLE 1.1.1.1 Premier sous article") == {
        'type': BodySection.SUB_ARTICLE,
        "level": 3,
        "level_name": "sous_article_3",
        'number': '1.1.1.1',
        'text': 'Premier sous article'
    }

    # Cas article hiérarchique avec chiffre arabe sans point
    assert parse_section("ARTICLE 1.A.3 - Premier article") == {
        'type': BodySection.ARTICLE,
        "level": 2,
        "level_name": "article_2",
        'number': '1.A.3',
        'text': 'Premier article'
    }
    # Cas article hiérarchique avec chiffre arabe avec point
    assert parse_section("ARTICLE 1.A.3. - Premier article") == {
        'type': BodySection.ARTICLE,
        "level": 2,
        "level_name": "article_2",
        'number': '1.A.3',
        'text': 'Premier article'
    }

    # Cas sous article sans nom avec point
    assert parse_section("1.2. - Sous-article") == {
        'type': BodySection.SUB_ARTICLE,
        "level": 1,
        "level_name": "sous_article_1",
        'number': '1.2',
        'text': 'Sous-article'
    }

    # Cas sous article sans nom sans point
    assert parse_section("1.2 - Sous-article") == {
        'type': BodySection.SUB_ARTICLE,
        "level": 1,
        "level_name": "sous_article_1",
        'number': '1.2',
        'text': 'Sous-article'
    }

    # Cas titre sans nom
    assert parse_section("I - Titre") == {
        'type': BodySection.TITLE,
        "level": 0,
        "level_name": "titre_0",
        'number': 'I',
        'text': 'Titre'
    }

    # Cas article sans nom avec point
    assert parse_section("1. Article directement écrit comme une phrase.") == {
        'type': BodySection.ARTICLE,
        "level": 0,
        "level_name": "article_0",
        'number': '1',
        'text': 'Article directement écrit comme une phrase.'
    }

    # Phrase quelconque
    assert parse_section("Ceci est une phrase.") == {
        "type": BodySection.NONE,
        "level": -1,
        "level_name": "none_-1",
        "number": "",
        "text": "",
    }

    # Phrase commençant par une lettre
    assert parse_section("A la bonne journée") == {
        "type": BodySection.NONE,
        "level": -1,
        "level_name": "none_-1",
        "number": "",
        "text": "",
    }

    # Phrase commençant par un chiffre arabe
    assert parse_section("1 On écrit directement un exemple") == {
        "type": BodySection.NONE,
        "level": -1,
        "level_name": "none_-1",
        "number": "",
        "text": "",
    }

    # Liste (on peut aussi trouver 1°)
    assert parse_section("1) Ceci est une liste") == {
        "type": BodySection.NONE,
        "level": -1,
        "level_name": "none_-1",
        "number": "",
        "text": "",
    }

    # Liste
    assert parse_section("- Ceci est une liste") == {
        "type": BodySection.NONE,
        "level": -1,
        "level_name": "none_-1",
        "number": "",
        "text": "",
    }

    # Tableau
    assert parse_section("| Ceci est un tableau |") == {
        "type": BodySection.NONE,
        "level": -1,
        "level_name": "none_-1",
        "number": "",
        "text": "",
    }

    # Tableau
    assert parse_section("(*) Ceci est une description de tableau") == {
        "type": BodySection.NONE,
        "level": -1,
        "level_name": "none_-1",
        "number": "",
        "text": "",
    }


if __name__ == "__main__":

    test_section_valid_cases()
