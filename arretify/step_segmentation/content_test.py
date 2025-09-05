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
from .content import parse_section_titles, parse_sections, parse_alineas, render_alinea
from .core import Node
from .testing import (
    assert_elements_equal,
    _l,
    make_text_spans,
)


class TestParseSectionTitles(unittest.TestCase):

    def test_parse_section_titles(self):
        # Arrange
        elements = make_text_spans(
            "Titre I - Introduction",
            "1. Contexte",
            "bla bla bla",
            "2. Objectifs",
            "blo blo blo",
            "bli bli bli",
            "Titre II - Méthodologie",
            "blu blu blu",
            "ble ble ble",
        )

        # Act
        result = list(parse_section_titles(elements))

        # Assert
        assert_elements_equal(
            result,
            [
                Node(
                    type="section_title",
                    children=make_text_spans("Titre I - Introduction"),
                    data=dict(
                        level=0,
                        number="I",
                        title="Introduction",
                        type="titre",
                    ),
                ),
                Node(
                    type="section_title",
                    children=make_text_spans("1. Contexte"),
                    data=dict(
                        level=1,
                        number="1",
                        title="Contexte",
                        type="unknown",
                    ),
                ),
                *make_text_spans("bla bla bla"),
                Node(
                    type="section_title",
                    children=make_text_spans("2. Objectifs"),
                    data=dict(
                        level=1,
                        number="2",
                        title="Objectifs",
                        type="unknown",
                    ),
                ),
                *make_text_spans(
                    "blo blo blo",
                    "bli bli bli",
                ),
                Node(
                    type="section_title",
                    children=make_text_spans("Titre II - Méthodologie"),
                    data=dict(
                        level=0,
                        number="II",
                        title="Méthodologie",
                        type="titre",
                    ),
                ),
                *make_text_spans(
                    "blu blu blu",
                    "ble ble ble",
                ),
            ],
            ignore_text_span_data=True,
        )

    def test_reject_text_span_starting_with_inline_node(self):
        # Arrange
        elements = [
            *make_text_spans(
                "Titre I - Introduction",
            ),
            Node(
                type="text_span",
                children=[Node(type="address", children=make_text_spans("1 rue de l'avenir"))],
            ),
        ]

        # Act
        result = list(parse_section_titles(elements))

        # Assert
        assert_elements_equal(
            result,
            [
                Node(
                    type="section_title",
                    children=make_text_spans("Titre I - Introduction"),
                    data=dict(
                        level=0,
                        number="I",
                        title="Introduction",
                        type="titre",
                    ),
                ),
                Node(
                    type="text_span",
                    children=[Node(type="address", children=make_text_spans("1 rue de l'avenir"))],
                ),
            ],
            ignore_text_span_data=True,
        )


class TestParseSections(unittest.TestCase):

    def test_parse_sections(self):
        # Arrange
        elements = [
            *make_text_spans("bly bly bly"),
            Node(
                type="section_title",
                data=dict(level=1),
                children=make_text_spans("Titre I - Introduction"),
            ),
            Node(
                type="section_title",
                data=dict(level=2),
                children=make_text_spans("1. Contexte"),
            ),
            *make_text_spans("bla bla bla"),
            Node(
                type="section_title",
                data=dict(level=2),
                children=make_text_spans("2. Objectifs"),
            ),
            *make_text_spans(
                "blo blo blo",
                "bli bli bli",
            ),
            Node(
                type="section_title",
                data=dict(level=1),
                children=make_text_spans("Titre II - Méthodologie"),
            ),
            *make_text_spans(
                "blu blu blu",
                "ble ble ble",
            ),
        ]

        # Act
        result = list(parse_sections(elements, level=1))

        # Assert
        assert_elements_equal(
            result,
            [
                Node(
                    type="alinea",
                    children=make_text_spans("bly bly bly"),
                    data=dict(number="1"),
                ),
                Node(
                    type="section",
                    children=[
                        Node(
                            type="section_title",
                            children=make_text_spans("Titre I - Introduction"),
                        ),
                        Node(
                            type="section",
                            children=[
                                Node(type="section_title", children=make_text_spans("1. Contexte")),
                                Node(
                                    type="alinea",
                                    children=make_text_spans("bla bla bla"),
                                    data=dict(number="1"),
                                ),
                            ],
                        ),
                        Node(
                            type="section",
                            children=[
                                Node(
                                    type="section_title", children=make_text_spans("2. Objectifs")
                                ),
                                Node(
                                    type="alinea",
                                    children=make_text_spans("blo blo blo"),
                                    data=dict(number="1"),
                                ),
                                Node(
                                    type="alinea",
                                    children=make_text_spans("bli bli bli"),
                                    data=dict(number="2"),
                                ),
                            ],
                        ),
                    ],
                ),
                Node(
                    type="section",
                    children=[
                        Node(
                            type="section_title",
                            children=make_text_spans("Titre II - Méthodologie"),
                        ),
                        Node(
                            type="alinea",
                            children=make_text_spans("blu blu blu"),
                            data=dict(number="1"),
                        ),
                        Node(
                            type="alinea",
                            children=make_text_spans("ble ble ble"),
                            data=dict(number="2"),
                        ),
                    ],
                ),
            ],
            ignore_data_if_omitted=True,
            ignore_text_span_data=True,
        )

    def test_parse_sections_contents(self):
        # Arrange
        elements = [
            Node(
                type="section_title",
                data=dict(level=0),
                children=_l("1. Bla"),
            ),
            *_l("bla bla bla"),
            Node(
                type="section_title",
                data=dict(level=1),
                children=_l("1.1. Blabla"),
            ),
            *_l("bli bli bli"),
        ]

        # Act
        result = list(parse_sections(elements, level=0))

        # Assert
        assert_elements_equal(
            result,
            [
                Node(
                    type="section",
                    children=[
                        Node(
                            type="section_title",
                            children=_l("1. Bla"),
                        ),
                        Node(
                            type="alinea",
                            children=_l("bla bla bla"),
                            data=dict(number="1"),
                        ),
                        Node(
                            type="section",
                            children=[
                                Node(
                                    type="section_title",
                                    children=_l("1.1. Blabla"),
                                ),
                                Node(
                                    type="alinea",
                                    children=_l("bli bli bli"),
                                    data=dict(number="1"),
                                ),
                            ],
                        ),
                    ],
                ),
            ],
            ignore_data_if_omitted=True,
            ignore_text_span_data=True,
        )

    def test_parse_sections_missing_level(self):
        # Arrange
        elements = [
            Node(
                type="section_title",
                data=dict(level=0),
                children=_l("1. Bla"),
            ),
            Node(
                type="section_title",
                data=dict(level=2),
                children=_l("1.1.1. Blabla"),
            ),
        ]

        # Act
        result = list(parse_sections(elements, level=0))

        # Assert
        assert_elements_equal(
            result,
            [
                Node(
                    type="section",
                    children=[
                        Node(
                            type="section_title",
                            children=_l("1. Bla"),
                        ),
                        Node(
                            type="section",
                            children=[
                                Node(
                                    type="section_title",
                                    children=_l("1.1.1. Blabla"),
                                ),
                            ],
                        ),
                    ],
                ),
            ],
            ignore_data_if_omitted=True,
            ignore_text_span_data=True,
        )

    def test_parse_missing_title_current_level(self):
        # Arrange
        elements = [
            Node(
                type="section_title",
                data=dict(level=1),
                children=_l("1.1. bla"),
            ),
            Node(
                type="section_title",
                data=dict(level=2),
                children=_l("1.1.1. bla"),
            ),
            Node(
                type="section_title",
                data=dict(level=1),
                children=_l("1.2. bla"),
            ),
            Node(
                type="section_title",
                data=dict(level=0),
                children=_l("2. bla"),
            ),
            Node(
                type="section_title",
                data=dict(level=1),
                children=_l("2.1. bla"),
            ),
        ]

        # Act
        result = list(parse_sections(elements, level=0))

        # Assert
        assert_elements_equal(
            result,
            [
                Node(
                    type="section",
                    children=[
                        Node(
                            type="section_title",
                            children=_l("1.1. bla"),
                        ),
                        Node(
                            type="section",
                            children=[
                                Node(
                                    type="section_title",
                                    children=_l("1.1.1. bla"),
                                ),
                            ],
                        ),
                    ],
                ),
                Node(
                    type="section",
                    children=[
                        Node(
                            type="section_title",
                            children=_l("1.2. bla"),
                        ),
                    ],
                ),
                Node(
                    type="section",
                    children=[
                        Node(
                            type="section_title",
                            children=_l("2. bla"),
                        ),
                        Node(
                            type="section",
                            children=[
                                Node(
                                    type="section_title",
                                    children=_l("2.1. bla"),
                                ),
                            ],
                        ),
                    ],
                ),
            ],
            ignore_data_if_omitted=True,
            ignore_text_span_data=True,
        )


class TestParseAlineas(unittest.TestCase):

    def test_merge_if_continuing_sentence_and_page_separator(self):
        # Arrange
        elements = [
            *make_text_spans("This is a sentence that "),
            Node(
                type="page_separator",
                data=dict(page_index=1),
                children=[],
            ),
            *make_text_spans("continues on the next page."),
        ]

        # Act
        result = list(parse_alineas(elements))

        # Assert
        assert_elements_equal(
            result,
            [
                Node(
                    type="alinea",
                    children=[
                        *make_text_spans("This is a sentence that "),
                        Node(
                            type="page_separator",
                            data=dict(page_index=1),
                            children=[],
                        ),
                        *make_text_spans("continues on the next page."),
                    ],
                    data=dict(number="1"),
                ),
            ],
            ignore_text_span_data=True,
        )


class TestRenderAlinea(unittest.TestCase):

    def setUp(self):
        self.soup = BeautifulSoup("", features="html.parser")

    def test_simple(self):
        # Arrange
        alinea = Node(
            type="alinea",
            children=make_text_spans("This is an alinea."),
            data=dict(number="1"),
        )

        # Act
        result = render_alinea(self.soup, alinea)

        # Assert
        assert normalized_html_str(str(result)) == normalized_html_str(
            """
            <div class="arretify-alinea" data-number="1">
                This is an alinea.
            </div>
            """
        )
