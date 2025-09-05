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

from arretify.utils.testing import normalized_html_str
from .header import (
    parse_visa_and_motif_elements,
    _parse_header_element,
    _parse_header_element_fuzzy,
    render_header_element,
    render_visa_motif,
    rendre_arrete_title,
)
from .testing import assert_elements_equal, make_text_spans
from .core import Node


class TestParseVisaAndMotifs(unittest.TestCase):

    def test_variant_simple(self):
        # Arrange
        elements = make_text_spans(
            (
                "Vu le code de l'environnement, et notamment ses titres "
                "1er et 4 des parties réglementaires et législatives du livre V ;"
            ),
            (
                "Vu la nomenclature des installations classées codifiée à l'annexe "
                "de l'article R511-9 du code de l'environnement ;"
            ),
        )

        # Act
        result = list(parse_visa_and_motif_elements(elements))

        # Assert
        assert_elements_equal(
            result,
            [
                Node(
                    type="visa",
                    children=make_text_spans(
                        (
                            "Vu le code de l'environnement, et notamment ses titres "
                            "1er et 4 des parties réglementaires et législatives du livre V ;"
                        )
                    ),
                ),
                Node(
                    type="visa",
                    children=make_text_spans(
                        (
                            "Vu la nomenclature des installations classées codifiée à l'annexe "
                            "de l'article R511-9 du code de l'environnement ;"
                        )
                    ),
                ),
            ],
            ignore_text_span_data=True,
        )

    def test_variant_simple_interrupted_by_random_text(self):
        # Arrange
        elements = [
            *make_text_spans("Vu bla"),
            *make_text_spans("Ceci est du texte aléatoire qui n'est pas un visa."),
            *make_text_spans("Vu blo"),
        ]

        # Act
        result = list(parse_visa_and_motif_elements(elements))

        # Assert
        assert_elements_equal(
            result,
            [
                Node(
                    type="visa",
                    children=make_text_spans("Vu bla"),
                ),
                *make_text_spans("Ceci est du texte aléatoire qui n'est pas un visa."),
                Node(
                    type="visa",
                    children=make_text_spans("Vu blo"),
                ),
            ],
            ignore_text_span_data=True,
        )

    def test_variant_simple_inside_list(self):
        # Arrange
        elements = [
            Node(
                type="list",
                children=make_text_spans(
                    "- Considérant que blabla ;",
                    "- Considérant que bloblo ;",
                ),
            ),
        ]

        # Act
        result = parse_visa_and_motif_elements(elements)

        # Assert
        assert_elements_equal(
            result,
            [
                Node(
                    type="motif",
                    children=make_text_spans(
                        "- Considérant que blabla ;",
                    ),
                ),
                Node(
                    type="motif",
                    children=make_text_spans(
                        "- Considérant que bloblo ;",
                    ),
                ),
            ],
            ignore_text_span_data=True,
        )

    def test_variant_simple_page_separator_interrupting_sentence(self):
        # Arrange
        elements = [
            *make_text_spans("Vu le code de l'environnement, et notamment ses titres 1er et 4"),
            Node(
                type="page_separator",
                children=[],
            ),
            *make_text_spans("des parties réglementaires et législatives du livre V ;"),
        ]

        # Act
        result = list(parse_visa_and_motif_elements(elements))

        # Assert
        assert_elements_equal(
            result,
            [
                Node(
                    type="visa",
                    children=[
                        *make_text_spans(
                            "Vu le code de l'environnement, et notamment ses titres 1er et 4"
                        ),
                        Node(
                            type="page_separator",
                            children=[],
                        ),
                        *make_text_spans("des parties réglementaires et législatives du livre V ;"),
                    ],
                ),
            ],
            ignore_text_span_data=True,
        )

    def test_variant_implicit_list(self):
        # Arrange
        elements = make_text_spans(
            "CONSIDÉRANT : ",
            "que blabla ;",
            "que bloblo ;",
            "qu'en application de blibli ;",
        )

        # Act
        result = list(parse_visa_and_motif_elements(elements))

        # Assert
        assert_elements_equal(
            result,
            [
                *make_text_spans("CONSIDÉRANT : "),
                Node(
                    type="motif",
                    children=make_text_spans("que blabla ;"),
                ),
                Node(
                    type="motif",
                    children=make_text_spans("que bloblo ;"),
                ),
                Node(
                    type="motif",
                    children=make_text_spans("qu'en application de blibli ;"),
                ),
            ],
            ignore_text_span_data=True,
        )

    def test_variant_implicit_list_interrupted_by_page_footer(self):
        # Arrange
        elements = [
            *make_text_spans(
                "Vu : ",
                (
                    "le code de l'environnement, et notamment ses titres "
                    "1er et 4 des parties réglementaires et législatives du livre V ;"
                ),
            ),
            Node(
                type="page_footer",
                children=make_text_spans("page 1"),
            ),
            *make_text_spans(
                (
                    "la nomenclature des installations classées codifiée à l'annexe "
                    "de l'article R511-9 du code de l'environnement ;"
                )
            ),
        ]

        # Act
        result = list(parse_visa_and_motif_elements(elements))

        # Assert
        assert_elements_equal(
            result,
            [
                *make_text_spans(
                    "Vu : ",
                ),
                Node(
                    type="visa",
                    children=make_text_spans(
                        "le code de l'environnement, et notamment ses titres "
                        "1er et 4 des parties réglementaires et législatives du livre V ;"
                    ),
                ),
                Node(
                    type="page_footer",
                    children=make_text_spans("page 1"),
                ),
                Node(
                    type="visa",
                    children=make_text_spans(
                        "la nomenclature des installations classées codifiée à l'annexe "
                        "de l'article R511-9 du code de l'environnement ;"
                    ),
                ),
            ],
            ignore_text_span_data=True,
        )

    def test_variant_explicit_list(self):
        # Arrange
        elements = [
            *make_text_spans("Vu : "),
            Node(
                type="list",
                children=make_text_spans(
                    "- le code de l'environnement ;",
                    "- la nomenclature des installations classées ;",
                ),
            ),
        ]

        # Act
        result = list(parse_visa_and_motif_elements(elements))

        # Assert
        assert_elements_equal(
            result,
            [
                *make_text_spans("Vu : "),
                Node(
                    type="visa",
                    children=make_text_spans("- le code de l'environnement ;"),
                ),
                Node(
                    type="visa",
                    children=make_text_spans("- la nomenclature des installations classées ;"),
                ),
            ],
            ignore_text_span_data=True,
        )

    def test_variant_explicit_list_interrupted(self):
        # Arrange
        elements = [
            *make_text_spans("Vu : "),
            Node(
                type="list",
                children=make_text_spans(
                    "- le code de l'environnement ;",
                ),
            ),
            *make_text_spans("Ceci est du texte aléatoire qui n'est pas un visa."),
            Node(
                type="list",
                children=make_text_spans(
                    "- la nomenclature des installations classées ;",
                ),
            ),
        ]

        # Act
        result = list(parse_visa_and_motif_elements(elements))

        # Assert
        assert_elements_equal(
            result,
            [
                *make_text_spans("Vu : "),
                Node(
                    type="visa",
                    children=make_text_spans("- le code de l'environnement ;"),
                ),
                *make_text_spans("Ceci est du texte aléatoire qui n'est pas un visa."),
                Node(
                    type="visa",
                    children=make_text_spans("- la nomenclature des installations classées ;"),
                ),
            ],
            ignore_text_span_data=True,
        )

    def test_variant_explicit_list_vu_inside_list_element(self):
        # Arrange
        elements = [
            *make_text_spans("Vu : "),
            Node(
                type="list",
                children=make_text_spans(
                    "- le code de l'environnement ;",
                    "- la nomenclature des installations classées ;",
                    "- vu la demande déposée par la société XYZ ;",
                ),
            ),
        ]

        # Act
        result = list(parse_visa_and_motif_elements(elements))

        # Assert
        assert_elements_equal(
            result,
            [
                *make_text_spans("Vu : "),
                Node(
                    type="visa",
                    children=make_text_spans("- le code de l'environnement ;"),
                ),
                Node(
                    type="visa",
                    children=make_text_spans("- la nomenclature des installations classées ;"),
                ),
                Node(
                    type="visa",
                    children=make_text_spans("- vu la demande déposée par la société XYZ ;"),
                ),
            ],
            ignore_text_span_data=True,
        )

    def test_variant_simple_with_list_inside_and_interrupted_by_age_separator(self):
        # Arrange
        elements = [
            *make_text_spans(
                "Considérant que la demande de modification sollicitée "
                "le 19 juillet 2021 porte sur :"
            ),
            Node(
                type="page_separator",
                children=[],
            ),
            Node(
                type="list",
                children=make_text_spans(
                    "- la modification de l'installation de stockage de déchets non dangereux ;",
                    "- la mise en conformité avec les exigences réglementaires ;",
                ),
            ),
        ]

        # Act
        result = list(parse_visa_and_motif_elements(elements))

        # Assert
        assert_elements_equal(
            result,
            [
                Node(
                    type="motif",
                    children=[
                        *make_text_spans(
                            "Considérant que la demande de modification sollicitée "
                            "le 19 juillet 2021 porte sur :"
                        ),
                        Node(
                            type="page_separator",
                            children=[],
                        ),
                        Node(
                            type="list",
                            children=make_text_spans(
                                "- la modification de l'installation de stockage de déchets "
                                "non dangereux ;",
                                "- la mise en conformité avec les exigences réglementaires ;",
                            ),
                        ),
                    ],
                ),
            ],
            ignore_text_span_data=True,
        )


class TestRenderHeaderElement(unittest.TestCase):

    def setUp(self):
        self.soup = BeautifulSoup("", features="html.parser")

    def test_render_header_element(self):
        # Arrange
        node = Node(
            type="emblem",
            children=make_text_spans(
                "liberté égalité fraternité",
            ),
        )

        # Act
        rendered = render_header_element(self.soup, node)

        # Assert
        assert normalized_html_str(str(rendered)) == normalized_html_str(
            """
            <div class="arretify-emblem">
                <div>liberté</div>
                <div>égalité</div>
                <div>fraternité</div>
            </div>
            """
        )


class TestParseHeaderElement(unittest.TestCase):

    def test_parse_header_element(self):
        # Arrange
        elements = make_text_spans(
            "liberte",
            "égalité",
            "fraternité",
        )

        # Act
        elements = _parse_header_element(elements, "emblem")

        # Assert
        assert_elements_equal(
            elements,
            [
                Node(
                    type="emblem",
                    children=make_text_spans(
                        "liberte",
                        "égalité",
                        "fraternité",
                    ),
                ),
            ],
            ignore_text_span_data=True,
        )

    def test_parse_header_element_fuzzy(self):
        # Arrange
        elements = make_text_spans(
            "prefecture de la région",
            "basée à Naboo",
            # Arrete title : should not be included in the entity
            "Arrêté du 1er janvier 2020",
        )

        # Act
        elements = _parse_header_element_fuzzy(elements, "entity")

        # Assert
        assert_elements_equal(
            elements,
            [
                Node(
                    type="entity",
                    children=make_text_spans(
                        "prefecture de la région",
                        "basée à Naboo",
                    ),
                ),
                *make_text_spans(
                    "Arrêté du 1er janvier 2020",
                ),
            ],
            ignore_text_span_data=True,
        )


class TestRenderVisaMotif(unittest.TestCase):

    def setUp(self):
        self.soup = BeautifulSoup("", features="html.parser")

    def test_render_simple(self):
        # Arrange
        node = Node(
            type="visa",
            children=make_text_spans(
                "Vu le code de l'environnement, et notamment ses titres "
                "1er et 4 des parties réglementaires et législatives du livre V ;",
            ),
        )

        # Act
        rendered = render_visa_motif(self.soup, node)

        # Assert
        assert normalized_html_str(str(rendered)) == normalized_html_str(
            """
            <div class="arretify-visa">
                Vu le code de l'environnement, et notamment ses titres
                1er et 4 des parties réglementaires et législatives du livre V ;
            </div>
            """
        )


class TestRenderArreteTitle(unittest.TestCase):

    def setUp(self):
        self.soup = BeautifulSoup("", features="html.parser")

    def test_render_arrete_title(self):
        # Arrange
        node = Node(
            type="arrete_title",
            children=make_text_spans(
                "Arrêté du 1er janvier 2020",
            ),
        )

        # Act
        rendered = rendre_arrete_title(self.soup, node)

        # Assert
        assert normalized_html_str(str(rendered)) == normalized_html_str(
            """
            <div class="arretify-arrete_title">
                <h1>Arrêté du
                    <time class="arretify-date" datetime="2020-01-01">
                        1er janvier 2020
                    </time>
                </h1>
            </div>
            """
        )
