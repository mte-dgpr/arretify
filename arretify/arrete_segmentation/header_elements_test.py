import unittest

from bs4 import BeautifulSoup

from arretify.parsing_utils.source_mapping import initialize_lines
from .header_elements import (
    ENTITY_PATTERN,
    HONORARY_PATTERN,
    SUPPLEMENTARY_MOTIF_INFORMATION_PATTERN,
    _join_split_pile_with_pattern,
    _parse_visas_or_motifs,
    _parse_arrete_title_info,
)
from arretify.utils.testing import normalized_html_str, make_testing_function_for_children_list


process_parse_arrete_title_info = make_testing_function_for_children_list(
    _parse_arrete_title_info,
)


class TestJoinSplitPile(unittest.TestCase):

    def test_entity(self):
        pile = [
            (
                "Préfecture du Doubs DIRECTION DES COLLECTIVITÉS LOCALES "
                "ET DE L'ENVIRONNEMENT BUREAU DE L'ENVIRONNEMENT"
            )
        ]
        assert _join_split_pile_with_pattern(pile, pattern=ENTITY_PATTERN) == [
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
        assert _join_split_pile_with_pattern(pile, pattern=HONORARY_PATTERN) == [
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
        assert _join_split_pile_with_pattern(
            pile, pattern=SUPPLEMENTARY_MOTIF_INFORMATION_PATTERN
        ) == [
            "APRĖS communication du projet d'arrêté à l'exploitant ;",
            "SUR proposition du secrétaire général de la préfecture du Haut-Rhin ;",
        ]


class TestParseArreteTitleInfo(unittest.TestCase):

    def test_parse_date(self):
        assert (
            process_parse_arrete_title_info(
                """
                Arrêté du 22 fevrier 2023 portant modification de l'autorisation d'exploiter
                une unité de valorisation énergétique de combustibles solides de
                récupération (CSR), de déchets d'activité économique (DAE) et d'ordures
                ménagères (OM) sur le territoire de la commune de Bantzenheim à la
                société B+T ENERGIE France Sas
            """
            )
            == [
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
            ]
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
        assert _text_segments_to_str(lines) == ["ARRETE"]

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
        assert _text_segments_to_str(lines) == ["ARRETE"]

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
        assert _text_segments_to_str(lines) == ["ARRETE"]

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
        assert _text_segments_to_str(lines) == ["ARRETE"]

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
        assert _text_segments_to_str(lines) == ["ARRETE"]

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
                        <li>territoires et de la mer,</li>
                        <li>architecture et patrimoine,</li>
                        <li>incendie et secours,</li>
                    </ul>
                </div>
                <div class="dsr-visa">la nomenclature des installations classées,</div>
            </header>
            """
        )
        assert _text_segments_to_str(lines) == ["ARRETE"]

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
                        <li>de la Direction Départementale de l’Equipement en date du 3 octobre 2000,</li>
                        <li>de la Direction Départementale de l’Agriculture et de la Forêt en date
                        du 6 octobre 2000,</li>
                    </ul>
                </div>
                <div class="dsr-visa">- la nomenclature des installations classées,</div>
            </header>
            """  # noqa: E501
        )
        assert _text_segments_to_str(lines) == ["ARRETE"]


def _text_segments_to_str(segments):
    return [segment.contents for segment in segments]
