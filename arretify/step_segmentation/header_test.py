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
    render_header_element,
    _parse_header_element,
    _parse_header_element_fuzzy,
)
from .testing import assert_elements_equal, _l
from .core import Node


class TestParseVisaAndMotifs(unittest.TestCase):

    def test_variant_simple(self):
        # Arrange
        elements = _l(
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
                    children=_l(
                        (
                            "Vu le code de l'environnement, et notamment ses titres "
                            "1er et 4 des parties réglementaires et législatives du livre V ;"
                        )
                    ),
                ),
                Node(
                    type="visa",
                    children=_l(
                        (
                            "Vu la nomenclature des installations classées codifiée à l'annexe "
                            "de l'article R511-9 du code de l'environnement ;"
                        )
                    ),
                ),
            ],
        )

    def test_variant_simple_interrupted_by_random_text(self):
        # Arrange
        elements = [
            *_l("Vu bla"),
            *_l("Ceci est du texte aléatoire qui n'est pas un visa."),
            *_l("Vu blo"),
        ]

        # Act
        result = list(parse_visa_and_motif_elements(elements))

        # Assert
        assert_elements_equal(
            result,
            [
                Node(
                    type="visa",
                    children=_l("Vu bla"),
                ),
                *_l("Ceci est du texte aléatoire qui n'est pas un visa."),
                Node(
                    type="visa",
                    children=_l("Vu blo"),
                ),
            ],
        )

    def test_variant_simple_inside_list(self):
        # Arrange
        elements = [
            Node(
                type="list",
                children=_l(
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
                    children=_l(
                        "- Considérant que blabla ;",
                    ),
                ),
                Node(
                    type="motif",
                    children=_l(
                        "- Considérant que bloblo ;",
                    ),
                ),
            ],
        )

    def test_variant_simple_page_separator_interrupting_sentence(self):
        # Arrange
        elements = [
            *_l("Vu le code de l'environnement, et notamment ses titres 1er et 4"),
            Node(
                type="page_separator",
                children=[],
            ),
            *_l("des parties réglementaires et législatives du livre V ;"),
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
                        *_l("Vu le code de l'environnement, et notamment ses titres 1er et 4"),
                        Node(
                            type="page_separator",
                            children=[],
                        ),
                        *_l("des parties réglementaires et législatives du livre V ;"),
                    ],
                ),
            ],
        )

    def test_variant_implicit_list(self):
        # Arrange
        elements = _l(
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
                *_l("CONSIDÉRANT : "),
                Node(
                    type="motif",
                    children=_l("que blabla ;"),
                ),
                Node(
                    type="motif",
                    children=_l("que bloblo ;"),
                ),
                Node(
                    type="motif",
                    children=_l("qu'en application de blibli ;"),
                ),
            ],
        )

    def test_variant_implicit_list_interrupted_by_page_footer(self):
        # Arrange
        elements = [
            *_l(
                "Vu : ",
                (
                    "le code de l'environnement, et notamment ses titres "
                    "1er et 4 des parties réglementaires et législatives du livre V ;"
                ),
            ),
            Node(
                type="page_footer",
                children=_l("page 1"),
            ),
            *_l(
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
                *_l(
                    "Vu : ",
                ),
                Node(
                    type="visa",
                    children=_l(
                        "le code de l'environnement, et notamment ses titres "
                        "1er et 4 des parties réglementaires et législatives du livre V ;"
                    ),
                ),
                Node(
                    type="page_footer",
                    children=_l("page 1"),
                ),
                Node(
                    type="visa",
                    children=_l(
                        "la nomenclature des installations classées codifiée à l'annexe "
                        "de l'article R511-9 du code de l'environnement ;"
                    ),
                ),
            ],
        )

    def test_variant_explicit_list(self):
        # Arrange
        elements = [
            *_l("Vu : "),
            Node(
                type="list",
                children=_l(
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
                *_l("Vu : "),
                Node(
                    type="visa",
                    children=_l("- le code de l'environnement ;"),
                ),
                Node(
                    type="visa",
                    children=_l("- la nomenclature des installations classées ;"),
                ),
            ],
        )

    def test_variant_explicit_list_interrupted(self):
        # Arrange
        elements = [
            *_l("Vu : "),
            Node(
                type="list",
                children=_l(
                    "- le code de l'environnement ;",
                ),
            ),
            *_l("Ceci est du texte aléatoire qui n'est pas un visa."),
            Node(
                type="list",
                children=_l(
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
                *_l("Vu : "),
                Node(
                    type="visa",
                    children=_l("- le code de l'environnement ;"),
                ),
                *_l("Ceci est du texte aléatoire qui n'est pas un visa."),
                Node(
                    type="visa",
                    children=_l("- la nomenclature des installations classées ;"),
                ),
            ],
        )

    def test_variant_explicit_list_vu_inside_list_element(self):
        # Arrange
        elements = [
            *_l("Vu : "),
            Node(
                type="list",
                children=_l(
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
                *_l("Vu : "),
                Node(
                    type="visa",
                    children=_l("- le code de l'environnement ;"),
                ),
                Node(
                    type="visa",
                    children=_l("- la nomenclature des installations classées ;"),
                ),
                Node(
                    type="visa",
                    children=_l("- vu la demande déposée par la société XYZ ;"),
                ),
            ],
        )

    def test_variant_simple_with_list_inside_and_interrupted_by_age_separator(self):
        # Arrange
        elements = [
            *_l(
                "Considérant que la demande de modification sollicitée "
                "le 19 juillet 2021 porte sur :"
            ),
            Node(
                type="page_separator",
                children=[],
            ),
            Node(
                type="list",
                children=_l(
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
                        *_l(
                            "Considérant que la demande de modification sollicitée "
                            "le 19 juillet 2021 porte sur :"
                        ),
                        Node(
                            type="page_separator",
                            children=[],
                        ),
                        Node(
                            type="list",
                            children=_l(
                                "- la modification de l'installation de stockage de déchets "
                                "non dangereux ;",
                                "- la mise en conformité avec les exigences réglementaires ;",
                            ),
                        ),
                    ],
                ),
            ],
        )


class TestRenderHeaderElement(unittest.TestCase):

    def setUp(self):
        self.soup = BeautifulSoup("", features="html.parser")

    def test_render_header_element(self):
        # Arrange
        node = Node(
            type="emblem",
            children=_l(
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
        elements = _l(
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
                    children=_l(
                        "liberte",
                        "égalité",
                        "fraternité",
                    ),
                ),
            ],
        )

    def test_parse_header_element_fuzzy(self):
        # Arrange
        elements = _l(
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
                    children=_l(
                        "prefecture de la région",
                        "basée à Naboo",
                    ),
                ),
                *_l(
                    "Arrêté du 1er janvier 2020",
                ),
            ],
        )
