import unittest
import re

from bs4 import BeautifulSoup

from .header import _process_entity_pile, parse_header, _parse_visas_or_motifs
from .sentence_rules import VISA_PATTERN, MOTIF_PATTERN
from bench_convertisseur_xml.html_schemas import VISA_SCHEMA, MOTIF_SCHEMA


class TestProcessEntityPile(unittest.TestCase):

    def test_simple(self):
        pile = ['Préfecture du Doubs DIRECTION DES COLLECTIVITÉS LOCALES ET DE L\'ENVIRONNEMENT BUREAU DE L\'ENVIRONNEMENT']
        assert _process_entity_pile(pile) == [
            'Préfecture du Doubs ',
            'DIRECTION DES COLLECTIVITÉS LOCALES ET DE L\'ENVIRONNEMENT ',
            'BUREAU DE L\'ENVIRONNEMENT',
        ]


class TestParseMotifsOrVisas(unittest.TestCase):

    def test_simple(self):
        # Arrange
        lines = [
            "Vu le code de l'environnement, et notamment ses titres 1er et 4 des parties réglementaires et législatives du livre V ;",
            "Vu la nomenclature des installations classées codifiée à l'annexe de l'article R511-9 du code de l'environnement ;",
            "END",
        ]

        def _is_next_section(line: str) -> bool:
            return line == "END"

        # Act
        soup = BeautifulSoup()
        header = soup.new_tag('header')
        lines = _parse_visas_or_motifs(soup, header, lines, VISA_PATTERN, VISA_SCHEMA, _is_next_section)

        # Assert
        assert str(header) == (
            "<header>"
            "<div class=\"dsr-visa\">Vu le code de l'environnement, et notamment ses titres 1er et 4 des parties réglementaires et législatives du livre V ;</div>"
            "<div class=\"dsr-visa\">Vu la nomenclature des installations classées codifiée à l'annexe de l'article R511-9 du code de l'environnement ;</div>"
            "</header>"
        )
        assert lines == ["END"]

    def test_lists_with_keyword_first(self):
        # Arrange
        lines = [
            "VU",
            "- le titre premier du livre V du code de l'environnement ;",
            "- le décret n° 77-1133 du 21 septembre 1977 et notamment ses articles 17 et 20 ;",
            "END",
        ]

        def _is_next_section(line: str) -> bool:
            return line == "END"

        # Act
        soup = BeautifulSoup()
        header = soup.new_tag('header')
        lines = _parse_visas_or_motifs(soup, header, lines, VISA_PATTERN, VISA_SCHEMA, _is_next_section)

        # Assert
        assert str(header) == (
            "<header>"
            "<div>VU</div>"
            "<div class=\"dsr-visa\">- le titre premier du livre V du code de l'environnement ;</div>"
            "<div class=\"dsr-visa\">- le décret n° 77-1133 du 21 septembre 1977 et notamment ses articles 17 et 20 ;</div>"
            "</header>"
        )
        assert lines == ["END"]

    def test_lists_with_keyword_in_bullet(self):
        # Arrange
        lines = [
            "- Considérant qu’aux termes de l’article L. 512-1 du code de l’environnement relatif aux installations classées pour la protection de l’environnement, l’autorisation ne peut être accordée que si les dangers ou inconvénients de l’installation peuvent être prévenus par des mesures que spécifie l’arrêté préfectoral ;",
            "- Considérant que les conditions d’aménagement et d’exploitation, telles qu’elles sont définies par le présent arrêté, permettent de prévenir les dangers et inconvénients de l’installation pour les intérêts mentionnés à l’article L. 512-1 du code de l’environnement, notamment pour la commodité du voisinage, pour la santé, la sécurité, la salubrité publiques et pour la protection de la nature et de l’environnement ;",
            "END",
        ]

        def _is_next_section(line: str) -> bool:
            return line == "END"

        # Act
        soup = BeautifulSoup()
        header = soup.new_tag('header')
        lines = _parse_visas_or_motifs(soup, header, lines, MOTIF_PATTERN, MOTIF_SCHEMA, _is_next_section)

        # Assert
        assert str(header) == (
            "<header>"
            "<div class=\"dsr-motifs\">- Considérant qu’aux termes de l’article L. 512-1 du code de l’environnement relatif aux installations classées pour la protection de l’environnement, l’autorisation ne peut être accordée que si les dangers ou inconvénients de l’installation peuvent être prévenus par des mesures que spécifie l’arrêté préfectoral ;</div>"
            "<div class=\"dsr-motifs\">- Considérant que les conditions d’aménagement et d’exploitation, telles qu’elles sont définies par le présent arrêté, permettent de prévenir les dangers et inconvénients de l’installation pour les intérêts mentionnés à l’article L. 512-1 du code de l’environnement, notamment pour la commodité du voisinage, pour la santé, la sécurité, la salubrité publiques et pour la protection de la nature et de l’environnement ;</div>"
            "</header>"
        )
        assert lines == ["END"]

    def test_lists_with_keyword_in_bullet_next_is_list_too(self):
        # Arrange
        lines = [
            "CONSIDÉRANT :",
            "- qu’aux termes de l’article L. 512-1 du code de l’environnement relatif aux installations classées pour la protection de l’environnement, l’autorisation ne peut être accordée que si les dangers ou inconvénients de l’installation peuvent être prévenus par des mesures que spécifie l’arrêté préfectoral ;",
            "- que les conditions d’aménagement et d’exploitation, telles qu’elles sont définies par le présent arrêté, permettent de prévenir les dangers et inconvénients de l’installation pour les intérêts mentionnés à l’article L. 512-1 du code de l’environnement, notamment pour la commodité du voisinage, pour la santé, la sécurité, la salubrité publiques et pour la protection de la nature et de l’environnement ;",
            "- END",
        ]

        def _is_next_section(line: str) -> bool:
            return line == "- END"

        # Act
        soup = BeautifulSoup()
        header = soup.new_tag('header')
        lines = _parse_visas_or_motifs(soup, header, lines, MOTIF_PATTERN, MOTIF_SCHEMA, _is_next_section)

        # Assert
        assert str(header) == (
            "<header>"
            "<div>CONSIDÉRANT :</div>"
            "<div class=\"dsr-motifs\">- qu’aux termes de l’article L. 512-1 du code de l’environnement relatif aux installations classées pour la protection de l’environnement, l’autorisation ne peut être accordée que si les dangers ou inconvénients de l’installation peuvent être prévenus par des mesures que spécifie l’arrêté préfectoral ;</div>"
            "<div class=\"dsr-motifs\">- que les conditions d’aménagement et d’exploitation, telles qu’elles sont définies par le présent arrêté, permettent de prévenir les dangers et inconvénients de l’installation pour les intérêts mentionnés à l’article L. 512-1 du code de l’environnement, notamment pour la commodité du voisinage, pour la santé, la sécurité, la salubrité publiques et pour la protection de la nature et de l’environnement ;</div>"
            "</header>"
        )
        assert lines == ["- END"]

    def test_without_keyword_nor_bullet(self):
        # Arrange
        lines = [
            "VU",
            "le Code de l'Environnement,",
            "la nomenclature des installations classées,",
            "le dossier déposé à l'appui de sa demande,",
            "END",
        ]

        def _is_next_section(line: str) -> bool:
            return line == "END"

        # Act
        soup = BeautifulSoup()
        header = soup.new_tag('header')
        lines = _parse_visas_or_motifs(soup, header, lines, VISA_PATTERN, VISA_SCHEMA, _is_next_section)

        # Assert
        assert str(header) == (
            "<header>"
            "<div>VU</div>"
            "<div class=\"dsr-visa\">le Code de l'Environnement,</div>"
            "<div class=\"dsr-visa\">la nomenclature des installations classées,</div>"
            "<div class=\"dsr-visa\">le dossier déposé à l'appui de sa demande,</div>"
            "</header>"
        )
        assert lines == ["END"]

    def test_with_nested_list(self):
        # Arrange
        lines = [
            "VU",
            "l'avis des directeurs départementaux des services consultés :",
            "- territoires et de la mer,",
            "- architecture et patrimoine,",
            "- incendie et secours,",
            "la nomenclature des installations classées,",
            "END",
        ]

        def _is_next_section(line: str) -> bool:
            return line == "END"

        # Act
        soup = BeautifulSoup()
        header = soup.new_tag('header')
        lines = _parse_visas_or_motifs(soup, header, lines, VISA_PATTERN, VISA_SCHEMA, _is_next_section)

        # Assert
        assert str(header) == (
            "<header>"
            "<div>VU</div>"
            "<div class=\"dsr-visa\">l'avis des directeurs départementaux des services consultés :"
            "<ul>"
            "<li>territoires et de la mer,</li>"
            "<li>architecture et patrimoine,</li>"
            "<li>incendie et secours,</li>"
            "</ul>"
            "</div>"
            "<div class=\"dsr-visa\">la nomenclature des installations classées,</div>"
            "</header>"
        )
        assert lines == ["END"]

    def test_with_nested_list_bullet(self):
        # Arrange
        lines = [
            "VU",
            "- les avis :",
            "  - de la Direction Départementale de l’Equipement en date du 3 octobre 2000,",
            "  - de la Direction Départementale de l’Agriculture et de la Forêt en date du 6 octobre 2000,",
            "- la nomenclature des installations classées,",
            "END",
        ]

        def _is_next_section(line: str) -> bool:
            return line == "END"

        # Act
        soup = BeautifulSoup()
        header = soup.new_tag('header')
        lines = _parse_visas_or_motifs(soup, header, lines, VISA_PATTERN, VISA_SCHEMA, _is_next_section)

        # Assert
        assert str(header) == (
            "<header>"
            "<div>VU</div>"
            "<div class=\"dsr-visa\">- les avis :"
            "<ul>"
            "<li>de la Direction Départementale de l’Equipement en date du 3 octobre 2000,</li>"
            "<li>de la Direction Départementale de l’Agriculture et de la Forêt en date du 6 octobre 2000,</li>"
            "</ul>"
            "</div>"
            "<div class=\"dsr-visa\">- la nomenclature des installations classées,</div>"
            "</header>"
        )
        assert lines == ["END"]