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
from arretify.step_segmentation.document_elements import (
    _parse_page_footer,
    _parse_table_of_contents,
)
from arretify.utils.testing import normalized_html_str


class TestParsePageFooter(unittest.TestCase):

    def test_page_footer(self):
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
        lines = _parse_page_footer(soup, header, lines)

        # Assert
        assert str(header) == normalized_html_str(
            """
            <header>
                <div class="arretify-page_footer">
                    <div>Page 1/4</div>
                </div>
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
                <div class="arretify-table_of_contents">
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
                <div class="arretify-table_of_contents">
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
                <div class="arretify-table_of_contents">
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
                <div class="arretify-table_of_contents">
                    <div>Liste des articles</div>
                    <div>TITRE 1 - TITRE ..... page 1</div>
                    <div>CHAPITRE chapitre ..... page 5</div>
                </div>
            </header>
            """  # noqa: E501
        )
        assert text_segments_to_str(lines) == ["TITRE 1 - Titre"]
