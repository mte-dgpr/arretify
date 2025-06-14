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
import unittest

from bs4 import BeautifulSoup

from arretify.parsing_utils.source_mapping import (
    initialize_lines,
    text_segments_to_str,
)
from arretify.parsing_utils.patterns import join_split_pile_with_pattern
from .header_elements import (
    ENTITY_PATTERN,
    HONORARY_PATTERN,
    SUPPLEMENTARY_MOTIF_INFORMATION_PATTERN,
    HEADER_ELEMENTS_PATTERNS,
    _parse_visas_or_motifs,
    _parse_arrete_title_info,
)
from arretify.utils.testing import (
    normalized_html_str,
    assert_html_list_equal,
    normalized_soup,
)


class TestArretePattern(unittest.TestCase):

    arrete_pattern = HEADER_ELEMENTS_PATTERNS["arrete_title"]

    def test_arrete_toc(self):
        text = "Arrêté suite ..... 1"
        assert not bool(self.arrete_pattern.search(text))


class TestJoinSplitPile(unittest.TestCase):

    def test_entity(self):
        pile = [
            (
                "Préfecture du Doubs DIRECTION DES COLLECTIVITÉS LOCALES "
                "ET DE L'ENVIRONNEMENT BUREAU DE L'ENVIRONNEMENT"
            )
        ]
        assert join_split_pile_with_pattern(pile, pattern=ENTITY_PATTERN) == [
            "Préfecture du Doubs ",
            "DIRECTION DES COLLECTIVITÉS LOCALES ET DE L'ENVIRONNEMENT ",
            "BUREAU DE L'ENVIRONNEMENT",
        ]

    def test_honorary(self):
        pile = [
            (
                "Le Préfet du Haut-Rhin"
                "Chevalier de la Légion d'Honneur"
                "Officier de l'Ordre National du Mérite"
            )
        ]
        assert join_split_pile_with_pattern(pile, pattern=HONORARY_PATTERN) == [
            "Le Préfet du Haut-Rhin",
            "Chevalier de la Légion d'Honneur",
            "Officier de l'Ordre National du Mérite",
        ]

    def test_supplementary_header_info(self):
        pile = [
            (
                "APRĖS communication du projet d'arrêté à l'exploitant ;"
                "SUR proposition du secrétaire général de la préfecture du Haut-Rhin ;"
            )
        ]
        assert join_split_pile_with_pattern(
            pile, pattern=SUPPLEMENTARY_MOTIF_INFORMATION_PATTERN
        ) == [
            "APRĖS communication du projet d'arrêté à l'exploitant ;",
            "SUR proposition du secrétaire général de la préfecture du Haut-Rhin ;",
        ]


class TestParseArreteTitleInfo(unittest.TestCase):

    def test_parse_date(self):
        soup = normalized_soup(
            """
            Arrêté du 22 fevrier 2023 portant modification de l'autorisation d'exploiter
            une unité de valorisation énergétique de combustibles solides de
            récupération (CSR), de déchets d'activité économique (DAE) et d'ordures
            ménagères (OM) sur le territoire de la commune de Bantzenheim à la
            société B+T ENERGIE France Sas
            """
        )
        assert_html_list_equal(
            _parse_arrete_title_info(soup, soup.children),
            [
                "Arrêté du ",
                normalized_html_str(
                    """
                    <time class="dsr-date" datetime="2023-02-22">
                        22 fevrier 2023
                    </time>
                """
                ),
                (
                    " portant modification de l'autorisation d'exploiter "
                    "une unité de valorisation énergétique de combustibles solides de "
                    "récupération (CSR), de déchets d'activité économique (DAE) et d'ordures "
                    "ménagères (OM) sur le territoire de la commune de Bantzenheim à la "
                    "société B+T ENERGIE France Sas"
                ),
            ],
        )


class TestParseMotifsOrVisas(unittest.TestCase):

    def test_simple(self):
        # Arrange
        lines = initialize_lines(
            [
                (
                    "Vu le code de l'environnement, et notamment ses titres "
                    "1er et 4 des parties réglementaires et législatives du livre V ;"
                ),
                (
                    "Vu la nomenclature des installations classées codifiée à l'annexe "
                    "de l'article R511-9 du code de l'environnement ;"
                ),
                "ARRETE",
            ]
        )

        # Act
        soup = BeautifulSoup()
        header = soup.new_tag("header")
        lines = _parse_visas_or_motifs(soup, header, lines, "visa")

        # Assert
        assert str(header) == normalized_html_str(
            """
            <header>
                <div class="dsr-visa">
                    Vu le code de l'environnement, et notamment ses titres 1er
                    et 4 des parties réglementaires et législatives du livre V ;
                </div>
                <div class="dsr-visa">
                    Vu la nomenclature des installations classées codifiée
                    à l'annexe de l'article R511-9 du code de l'environnement ;
                </div>
            </header>
            """
        )
        assert text_segments_to_str(lines) == ["ARRETE"]

    def test_lists_with_keyword_first(self):
        # Arrange
        lines = initialize_lines(
            [
                "VU",
                "- le titre premier du livre V du code de l'environnement ;",
                "- le décret n° 77-1133 du 21 septembre 1977 et notamment ses articles 17 et 20 ;",
                "ARRETE",
            ]
        )

        # Act
        soup = BeautifulSoup()
        header = soup.new_tag("header")
        lines = _parse_visas_or_motifs(soup, header, lines, "visa")

        # Assert
        assert str(header) == normalized_html_str(
            """
            <header>
                <div>VU</div>
                <div class="dsr-visa">
                    - le titre premier du livre V du code de l'environnement ;
                </div>
                <div class="dsr-visa">
                    - le décret n° 77-1133 du 21 septembre 1977 et notamment ses articles 17 et 20 ;
                </div>
            </header>
            """
        )
        assert text_segments_to_str(lines) == ["ARRETE"]

    def test_lists_with_keyword_in_bullet(self):
        # Arrange
        lines = initialize_lines(
            [
                (
                    "- Considérant qu’aux termes de l’article L. 512-1 du code de l’environnement "
                    "relatif aux installations classées pour la protection de l’environnement, "
                    "l’autorisation ne peut être accordée que si les dangers ou inconvénients "
                    "de l’installation peuvent être prévenus par des mesures que spécifie "
                    "l’arrêté préfectoral ;"
                ),
                (
                    "- Considérant que les conditions d’aménagement et d’exploitation, telles "
                    "qu’elles sont définies par le présent arrêté, permettent de prévenir "
                    "les dangers et inconvénients de l’installation pour les intérêts mentionnés "
                    "à l’article L. 512-1 du code de l’environnement, notamment pour la commodité "
                    "du voisinage, pour la santé, la sécurité, la salubrité publiques et pour la "
                    "protection de la nature et de l’environnement ;"
                ),
                "ARRETE",
            ]
        )

        # Act
        soup = BeautifulSoup()
        header = soup.new_tag("header")
        lines = _parse_visas_or_motifs(soup, header, lines, "motif")

        # Assert
        assert str(header) == normalized_html_str(
            """
            <header>
                <div class="dsr-motifs">
                    - Considérant qu’aux termes de l’article L. 512-1 du code de l’environnement
                    relatif aux installations classées pour la protection de l’environnement,
                    l’autorisation ne peut être accordée que si les dangers ou inconvénients
                    de l’installation peuvent être prévenus par des mesures que spécifie
                    l’arrêté préfectoral ;
                </div>
                <div class="dsr-motifs">
                    - Considérant que les conditions d’aménagement et d’exploitation, telles
                    qu’elles sont définies par le présent arrêté, permettent de prévenir
                    les dangers et inconvénients de l’installation pour les intérêts mentionnés
                    à l’article L. 512-1 du code de l’environnement, notamment pour la commodité
                    du voisinage, pour la santé, la sécurité, la salubrité publiques et pour la
                    protection de la nature et de l’environnement ;
                </div>
            </header>
            """
        )
        assert text_segments_to_str(lines) == ["ARRETE"]

    def test_lists_with_keyword_in_bullet_next_is_list_too(self):
        # Arrange
        lines = initialize_lines(
            [
                "CONSIDÉRANT :",
                (
                    "- qu’aux termes de l’article L. 512-1 du code de l’environnement relatif aux "
                    "installations classées pour la protection de l’environnement, l’autorisation "
                    "ne peut être accordée que si les dangers ou inconvénients de l’installation "
                    "peuvent être prévenus par des mesures que spécifie l’arrêté préfectoral ;"
                ),
                (
                    "- que les conditions d’aménagement et d’exploitation, telles qu’elles sont "
                    "définies par le présent arrêté, permettent de prévenir les dangers "
                    "et inconvénients de l’installation pour les intérêts mentionnés à "
                    "l’article L. 512-1 du code de l’environnement, notamment pour la commodité "
                    "du voisinage, pour la santé, la sécurité, la salubrité publiques et "
                    "pour la protection de la nature et de l’environnement ;"
                ),
                "ARRETE",
            ]
        )

        # Act
        soup = BeautifulSoup()
        header = soup.new_tag("header")
        lines = _parse_visas_or_motifs(soup, header, lines, "motif")

        # Assert
        assert str(header) == normalized_html_str(
            """
            <header>
                <div>CONSIDÉRANT :</div>
                <div class="dsr-motifs">
                    - qu’aux termes de l’article L. 512-1 du code de l’environnement relatif
                    aux installations classées pour la protection de l’environnement,
                    l’autorisation ne peut être accordée que si les dangers ou inconvénients
                    de l’installation peuvent être prévenus par des mesures que spécifie
                    l’arrêté préfectoral ;
                </div>
                <div class="dsr-motifs">
                    - que les conditions d’aménagement et d’exploitation, telles qu’elles sont
                    définies par le présent arrêté, permettent de prévenir les dangers et
                    inconvénients de l’installation pour les intérêts mentionnés
                    à l’article L. 512-1 du code de l’environnement, notamment pour la commodité
                    du voisinage, pour la santé, la sécurité, la salubrité publiques et
                    pour la protection de la nature et de l’environnement ;
                </div>
            </header>
            """
        )
        assert text_segments_to_str(lines) == ["ARRETE"]

    def test_without_keyword_nor_bullet(self):
        # Arrange
        lines = initialize_lines(
            [
                "VU",
                "le Code de l'Environnement,",
                "la nomenclature des installations classées,",
                "le dossier déposé à l'appui de sa demande,",
                "ARRETE",
            ]
        )

        # Act
        soup = BeautifulSoup()
        header = soup.new_tag("header")
        lines = _parse_visas_or_motifs(soup, header, lines, "visa")

        # Assert
        assert str(header) == normalized_html_str(
            """
            <header>
                <div>VU</div>
                <div class="dsr-visa">le Code de l'Environnement,</div>
                <div class="dsr-visa">la nomenclature des installations classées,</div>
                <div class="dsr-visa">le dossier déposé à l'appui de sa demande,</div>
            </header>
            """
        )
        assert text_segments_to_str(lines) == ["ARRETE"]

    def test_with_nested_list(self):
        # Arrange
        lines = initialize_lines(
            [
                "VU",
                "l'avis des directeurs départementaux des services consultés :",
                "- territoires et de la mer,",
                "- architecture et patrimoine,",
                "- incendie et secours,",
                "la nomenclature des installations classées,",
                "ARRETE",
            ]
        )

        # Act
        soup = BeautifulSoup()
        header = soup.new_tag("header")
        lines = _parse_visas_or_motifs(soup, header, lines, "visa")

        # Assert
        assert str(header) == normalized_html_str(
            """
            <header>
                <div>VU</div>
                <div class="dsr-visa">
                    l'avis des directeurs départementaux des services consultés :
                    <ul>
                        <li>- territoires et de la mer,</li>
                        <li>- architecture et patrimoine,</li>
                        <li>- incendie et secours,</li>
                    </ul>
                </div>
                <div class="dsr-visa">la nomenclature des installations classées,</div>
            </header>
            """
        )
        assert text_segments_to_str(lines) == ["ARRETE"]

    def test_with_nested_list_bullet(self):
        # Arrange
        lines = initialize_lines(
            [
                "VU",
                "- les avis :",
                "  - de la Direction Départementale de l’Equipement en date du 3 octobre 2000,",
                (
                    "  - de la Direction Départementale de l’Agriculture et de la Forêt en date "
                    "du 6 octobre 2000,"
                ),
                "- la nomenclature des installations classées,",
                "ARRETE",
            ]
        )

        # Act
        soup = BeautifulSoup()
        header = soup.new_tag("header")
        lines = _parse_visas_or_motifs(soup, header, lines, "visa")

        # Assert
        assert str(header) == normalized_html_str(
            """
            <header>
                <div>VU</div>
                <div class="dsr-visa">
                    - les avis :
                    <ul>
                        <li>- de la Direction Départementale de l’Equipement en date du 3 octobre 2000,</li>
                        <li>- de la Direction Départementale de l’Agriculture et de la Forêt en date
                        du 6 octobre 2000,</li>
                    </ul>
                </div>
                <div class="dsr-visa">- la nomenclature des installations classées,</div>
            </header>
            """  # noqa: E501
        )
        assert text_segments_to_str(lines) == ["ARRETE"]

    def test_with_whitespace(self):
        # Arrange
        lines = initialize_lines(
            [
                "V u :",
                "le Code de l'Environnement,",
                "la nomenclature des installations classées,",
                "le dossier déposé à l'appui de sa demande,",
                "ARRETE",
            ]
        )

        # Act
        soup = BeautifulSoup()
        header = soup.new_tag("header")
        lines = _parse_visas_or_motifs(soup, header, lines, "visa")

        # Assert
        assert str(header) == normalized_html_str(
            """
            <header>
                <div>V u :</div>
                <div class="dsr-visa">le Code de l'Environnement,</div>
                <div class="dsr-visa">la nomenclature des installations classées,</div>
                <div class="dsr-visa">le dossier déposé à l'appui de sa demande,</div>
            </header>
            """
        )
        assert text_segments_to_str(lines) == ["ARRETE"]
