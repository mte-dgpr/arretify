import unittest

from bs4 import BeautifulSoup

from arretify.parsing_utils.source_mapping import (
    initialize_lines,
    text_segments_to_str,
)
from arretify.step_segmentation.document_elements import (
    _is_footer,
    _parse_footer,
    _parse_table_of_contents,
)
from arretify.utils.testing import normalized_html_str


class TestFooterPattern(unittest.TestCase):

    def test_arrete_toc(self):
        text = "Arrêté suite ..... page 1"
        assert not _is_footer(text)


class TestParseFooter(unittest.TestCase):

    def test_footer(self):
        # Arrange
        lines = initialize_lines(
            [
                "Page 1/4",
                "Titre 1",
            ]
        )

        # Act
        soup = BeautifulSoup()
        header = soup.new_tag("header")
        lines = _parse_footer(soup, header, lines)

        # Assert
        assert str(header) == normalized_html_str(
            """
            <header>
                <div class="dsr-footer">Page 1/4</div>
            </header>
            """  # noqa: E501
        )
        assert text_segments_to_str(lines) == ["Titre 1"]


class TestParseTableOfContents(unittest.TestCase):

    def test_sommaire(self):
        # Arrange
        lines = initialize_lines(
            [
                "Sommaire",
                "1 Titre ..... 5",
                "1.1 Chapitre ..... 5",
                "1.1.1 Article ..... 5",
                "1 Titre",
            ]
        )

        # Act
        soup = BeautifulSoup()
        header = soup.new_tag("header")
        lines = _parse_table_of_contents(soup, header, lines)

        # Assert
        assert str(header) == normalized_html_str(
            """
            <header>
                <div class="dsr-table_of_contents">
                    <div>Sommaire</div>
                    <div>1 Titre ..... 5</div>
                    <div>1.1 Chapitre ..... 5</div>
                    <div>1.1.1 Article ..... 5</div>
                </div>
            </header>
            """  # noqa: E501
        )
        assert text_segments_to_str(lines) == ["1 Titre"]

    def test_sommaire_with_arrete(self):
        # Arrange
        lines = initialize_lines(
            [
                "Liste des chapitres",
                "Arrêté n D3 ..... 1",
                "TITRE 1 - TITRE ..... 5",
                "CHAPITRE 1.1 - CHAPITRE ..... 5",
                "TITRE 1 - TITRE",
            ]
        )

        # Act
        soup = BeautifulSoup()
        header = soup.new_tag("header")
        lines = _parse_table_of_contents(soup, header, lines)

        # Assert
        assert str(header) == normalized_html_str(
            """
            <header>
                <div class="dsr-table_of_contents">
                    <div>Liste des chapitres</div>
                    <div>Arrêté n D3 ..... 1</div>
                    <div>TITRE 1 - TITRE ..... 5</div>
                    <div>CHAPITRE 1.1 - CHAPITRE ..... 5</div>
                </div>
            </header>
            """  # noqa: E501
        )
        assert text_segments_to_str(lines) == ["TITRE 1 - TITRE"]

    def test_sommaire_non_contiguous(self):
        # Arrange
        lines = initialize_lines(
            [
                "Liste des articles",
                "TITRE 1 - TITRE ..... 1",
                "CHAPITRE chapitre ..... 5",
                "Article 1.1. article ..... 5",
                "CHAPITRE Autre chapitre ..... 5",
                "Article 1.1. Autre article ..... 5",
                "TITRE 1 - Titre",
            ]
        )

        # Act
        soup = BeautifulSoup()
        header = soup.new_tag("header")
        lines = _parse_table_of_contents(soup, header, lines)

        # Assert
        assert str(header) == normalized_html_str(
            """
            <header>
                <div class="dsr-table_of_contents">
                    <div>Liste des articles</div>
                    <div>TITRE 1 - TITRE ..... 1</div>
                    <div>CHAPITRE chapitre ..... 5</div>
                    <div>Article 1.1. article ..... 5</div>
                    <div>CHAPITRE Autre chapitre ..... 5</div>
                    <div>Article 1.1. Autre article ..... 5</div>
                </div>
            </header>
            """  # noqa: E501
        )
        assert text_segments_to_str(lines) == ["TITRE 1 - Titre"]

    def test_sommaire_page(self):
        # Arrange
        lines = initialize_lines(
            [
                "Liste des articles",
                "TITRE 1 - TITRE ..... page 1",
                "CHAPITRE chapitre ..... page 5",
                "TITRE 1 - Titre",
            ]
        )

        # Act
        soup = BeautifulSoup()
        header = soup.new_tag("header")
        lines = _parse_table_of_contents(soup, header, lines)

        # Assert
        assert str(header) == normalized_html_str(
            """
            <header>
                <div class="dsr-table_of_contents">
                    <div>Liste des articles</div>
                    <div>TITRE 1 - TITRE ..... page 1</div>
                    <div>CHAPITRE chapitre ..... page 5</div>
                </div>
            </header>
            """  # noqa: E501
        )
        assert text_segments_to_str(lines) == ["TITRE 1 - Titre"]
