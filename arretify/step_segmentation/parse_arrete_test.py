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

from .core import Node
from .parse_arrete import parse_arrete
from .testing import make_text_spans, assert_elements_equal


class TestParseArrete(unittest.TestCase):

    def test_simple(self):
        # Arrange
        pages = [
            (
                "Arrêté n° 123\n"
                "Article 1 : Disposition\n"
                "Bla bla bla ...\n"
                "Annexe 1 : Détails\n"
                "Bla bla bla ...\n"
            )
        ]

        # Act
        elements = parse_arrete(pages)

        # Assert
        assert_elements_equal(
            elements,
            [
                Node(
                    type="header",
                    children=[
                        Node(
                            type="page_separator",
                            children=[],
                        ),
                        Node(type="arrete_title", children=make_text_spans("Arrêté n° 123")),
                    ],
                ),
                Node(
                    type="main",
                    children=[
                        Node(
                            type="section",
                            children=[
                                Node(
                                    type="section_title",
                                    children=make_text_spans("Article 1 : Disposition"),
                                ),
                                Node(
                                    type="alinea",
                                    children=make_text_spans("Bla bla bla ..."),
                                ),
                            ],
                        ),
                    ],
                ),
                Node(
                    type="appendix",
                    children=[
                        Node(
                            type="section",
                            children=[
                                Node(
                                    type="section_title",
                                    children=make_text_spans("Annexe 1 : Détails"),
                                ),
                                Node(
                                    type="alinea",
                                    children=make_text_spans("Bla bla bla ..."),
                                ),
                            ],
                        ),
                    ],
                ),
            ],
            ignore_data_if_omitted=True,
            ignore_text_span_data=True,
        )

    def test_parse_text_span_inline_content_nodes(self):
        # Arrange
        pages = [
            (
                "Arrêté n° 123\n"
                "Article 1 : Disposition\n"
                # This address should be parsed as an address
                # node inside a text_span
                "Bla bla, 123 rue de la Paix, bla ..."
            )
        ]

        # Act
        elements = parse_arrete(pages)

        # Assert
        assert_elements_equal(
            elements,
            [
                Node(
                    type="header",
                    children=[
                        Node(
                            type="page_separator",
                            children=[],
                        ),
                        Node(type="arrete_title", children=make_text_spans("Arrêté n° 123")),
                    ],
                ),
                Node(
                    type="main",
                    children=[
                        Node(
                            type="section",
                            children=[
                                Node(
                                    type="section_title",
                                    children=make_text_spans("Article 1 : Disposition"),
                                ),
                                Node(
                                    type="alinea",
                                    children=[
                                        Node(
                                            type="text_span",
                                            children=[
                                                "Bla bla, ",
                                                Node(
                                                    type="address",
                                                    children=["123 rue de la Paix"],
                                                ),
                                                ", bla ...",
                                            ],
                                        )
                                    ],
                                ),
                            ],
                        ),
                    ],
                ),
            ],
            ignore_data_if_omitted=True,
            ignore_text_span_data=True,
        )
