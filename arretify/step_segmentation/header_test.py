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

from .header import (
    parse_visa_and_motif_elements,
    _create_visa_or_motif_nodes,
    VISA_PATTERN,
    MOTIF_PATTERN,
)
from .testing import assert_node_flows_equal, _l
from .core import Node


class TestCreateVisaOrMotifNodes(unittest.TestCase):
    def test_vu_simple(self):
        # Arrange
        node_flow = [
            _l(
                (
                    "Vu le code de l'environnement, et notamment ses titres "
                    "1er et 4 des parties réglementaires et législatives du livre V ;"
                ),
                (
                    "Vu la nomenclature des installations classées codifiée à l'annexe "
                    "de l'article R511-9 du code de l'environnement ;"
                ),
            )
        ]

        # Act
        node_flow = _create_visa_or_motif_nodes(node_flow, "visa", VISA_PATTERN)

        # Assert
        assert_node_flows_equal(
            node_flow,
            [
                Node(
                    type="visa",
                    children=[
                        _l(
                            "Vu le code de l'environnement, et notamment ses titres "
                            "1er et 4 des parties réglementaires et législatives du livre V ;"
                        )
                    ],
                ),
                Node(
                    type="visa",
                    children=[
                        _l(
                            "Vu la nomenclature des installations classées codifiée à l'annexe "
                            "de l'article R511-9 du code de l'environnement ;"
                        )
                    ],
                ),
            ],
        )

    def test_considerant_simple_list(self):
        # Arrange
        node_flow = [
            Node(
                type="list",
                children=[
                    _l(
                        "- Considérant que blabla ;",
                        "- Considérant que bloblo ;",
                    )
                ],
            ),
        ]

        # Act
        node_flow = _create_visa_or_motif_nodes(node_flow, "motif", MOTIF_PATTERN)

        # Assert
        assert_node_flows_equal(
            node_flow,
            [
                Node(
                    type="motif",
                    children=[
                        _l(
                            "- Considérant que blabla ;",
                        ),
                    ],
                ),
                Node(
                    type="motif",
                    children=[
                        _l(
                            "- Considérant que bloblo ;",
                        ),
                    ],
                ),
            ],
        )


class TestParseVisaAndMotifs(unittest.TestCase):

    def test_vu_simple(self):
        # Arrange
        node_flow = [
            Node(
                type="visa",
                children=[
                    _l(
                        "Vu le code de l'environnement, et notamment ses titres "
                        "1er et 4 des parties réglementaires et législatives du livre V ;"
                    )
                ],
            ),
            Node(
                type="visa",
                children=[
                    _l(
                        "Vu la nomenclature des installations classées codifiée à l'annexe "
                        "de l'article R511-9 du code de l'environnement ;"
                    )
                ],
            ),
        ]

        # Act
        expected = list(node_flow)
        node_flow = list(parse_visa_and_motif_elements(node_flow))

        # Assert
        assert_node_flows_equal(
            node_flow,
            expected,
        )

    def test_vu_simple_with_list_inside(self):
        # Arrange
        node_flow = [
            Node(type="visa", children=["VU :"]),
            Node(
                type="list",
                children=[
                    _l("- Item 1"),
                    _l("- Item 2"),
                ],
            ),
        ]

        # Act
        node_flow = list(parse_visa_and_motif_elements(node_flow))

        # Assert
        assert_node_flows_equal(
            node_flow,
            [
                Node(
                    type="visa",
                    children=[
                        _l("VU :"),
                        Node(
                            type="list",
                            children=[
                                _l("- Item 1"),
                                _l("- Item 2"),
                            ],
                        ),
                    ],
                ),
            ],
        )

    def test_vu_simple_interrupted_by_random_text(self):
        # Arrange
        node_flow = [
            _l("Vu bla"),
            _l("Ceci est du texte aléatoire qui n'est pas un visa."),
            _l("Vu blo"),
        ]

        # Act
        node_flow = list(parse_visa_and_motif_elements(node_flow))

        # Assert
        assert_node_flows_equal(
            node_flow,
            [
                Node(
                    type="visa",
                    children=[
                        _l("Vu bla"),
                    ],
                ),
                _l("Ceci est du texte aléatoire qui n'est pas un visa."),
                Node(
                    type="visa",
                    children=[
                        _l("Vu blo"),
                    ],
                ),
            ],
        )

    def test_vu_implicit_list(self):
        # Arrange
        node_flow = [
            _l(
                "CONSIDÉRANT : ",
                "que blabla ;",
                "que bloblo ;",
                "qu'en application de blibli ;",
            ),
        ]

        # Act
        node_flow = list(parse_visa_and_motif_elements(node_flow))

        # Assert
        assert_node_flows_equal(
            node_flow,
            [
                _l("CONSIDÉRANT : "),
                Node(
                    type="motif",
                    children=[
                        _l("que blabla ;"),
                    ],
                ),
                Node(
                    type="motif",
                    children=[
                        _l("que bloblo ;"),
                    ],
                ),
                Node(
                    type="motif",
                    children=[
                        _l("qu'en application de blibli ;"),
                    ],
                ),
            ],
        )

    def test_vu_implicit_list_interrupted_by_page_footer(self):
        # Arrange
        node_flow = [
            _l(
                "Vu : ",
                (
                    "le code de l'environnement, et notamment ses titres "
                    "1er et 4 des parties réglementaires et législatives du livre V ;"
                ),
            ),
            Node(
                type="page_footer",
                children=[_l("page 1")],
            ),
            _l(
                (
                    "la nomenclature des installations classées codifiée à l'annexe "
                    "de l'article R511-9 du code de l'environnement ;"
                )
            ),
        ]

        # Act
        node_flow = list(parse_visa_and_motif_elements(node_flow))

        # Assert
        assert_node_flows_equal(
            node_flow,
            [
                _l(
                    "Vu : ",
                ),
                Node(
                    type="visa",
                    children=[
                        _l(
                            "le code de l'environnement, et notamment ses titres "
                            "1er et 4 des parties réglementaires et législatives du livre V ;"
                        )
                    ],
                ),
                Node(
                    type="page_footer",
                    children=[_l("page 1")],
                ),
                Node(
                    type="visa",
                    children=[
                        _l(
                            "la nomenclature des installations classées codifiée à l'annexe "
                            "de l'article R511-9 du code de l'environnement ;"
                        )
                    ],
                ),
            ],
        )
        # Arrange
        node_flow = [
            _l(
                "CONSIDÉRANT : ",
                "que blabla ;",
                "que bloblo ;",
                "qu'en application de blibli ;",
            ),
        ]

        # Act
        node_flow = list(parse_visa_and_motif_elements(node_flow))

        # Assert
        assert_node_flows_equal(
            node_flow,
            [
                _l("CONSIDÉRANT : "),
                Node(
                    type="motif",
                    children=[
                        _l("que blabla ;"),
                    ],
                ),
                Node(
                    type="motif",
                    children=[
                        _l("que bloblo ;"),
                    ],
                ),
                Node(
                    type="motif",
                    children=[
                        _l("qu'en application de blibli ;"),
                    ],
                ),
            ],
        )

    def test_vu_explicit_list(self):
        # Arrange
        node_flow = [
            Node(type="visa", children=[_l("Vu : ")]),
            Node(
                type="list",
                children=[
                    _l(
                        "- le code de l'environnement ;",
                    ),
                    _l(
                        "- la nomenclature des installations classées ;",
                    ),
                ],
            ),
        ]

        # Act
        node_flow = list(parse_visa_and_motif_elements(node_flow))

        # Assert
        assert_node_flows_equal(
            node_flow,
            [
                _l("Vu : "),
                Node(
                    type="visa",
                    children=[
                        _l("- le code de l'environnement ;"),
                    ],
                ),
                Node(
                    type="visa",
                    children=[
                        _l("- la nomenclature des installations classées ;"),
                    ],
                ),
            ],
        )

    def test_vu_explicit_list_interrupted(self):
        # Arrange
        node_flow = [
            Node(type="visa", children=[_l("Vu : ")]),
            Node(
                type="list",
                children=[
                    _l(
                        "- le code de l'environnement ;",
                    ),
                ],
            ),
            _l("Ceci est du texte aléatoire qui n'est pas un visa."),
            Node(
                type="list",
                children=[
                    _l(
                        "- la nomenclature des installations classées ;",
                    ),
                ],
            ),
        ]

        # Act
        node_flow = list(parse_visa_and_motif_elements(node_flow))

        # Assert
        assert_node_flows_equal(
            node_flow,
            [
                _l("Vu : "),
                Node(
                    type="visa",
                    children=[
                        _l("- le code de l'environnement ;"),
                    ],
                ),
                _l("Ceci est du texte aléatoire qui n'est pas un visa."),
                Node(
                    type="visa",
                    children=[
                        _l("- la nomenclature des installations classées ;"),
                    ],
                ),
            ],
        )

        # Arrange
        node_flow = [
            Node(type="visa", children=[_l("Vu : ")]),
            Node(
                type="list",
                children=[
                    _l(
                        "- le code de l'environnement ;",
                        "- la nomenclature des installations classées ;",
                    ),
                ],
            ),
            Node(
                type="visa",
                children=[
                    _l("- vu la demande déposée par la société XYZ ;"),
                ],
            ),
        ]

        # Act
        node_flow = list(parse_visa_and_motif_elements(node_flow))

        # Assert
        assert_node_flows_equal(
            node_flow,
            [
                _l("Vu : "),
                Node(
                    type="visa",
                    children=[
                        _l("- le code de l'environnement ;"),
                    ],
                ),
                Node(
                    type="visa",
                    children=[
                        _l("- la nomenclature des installations classées ;"),
                    ],
                ),
                Node(
                    type="visa",
                    children=[_l("- vu la demande déposée par la société XYZ ;")],
                ),
            ],
        )
