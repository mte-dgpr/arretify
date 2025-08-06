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

from .core import Node
from .document_elements import (
    initialize_document_structure,
    parse_tables_of_contents,
    render_table_of_contents,
)
from .testing import _l, assert_elements_equal, make_text_spans
from arretify.utils.testing import normalized_html_str


class TestInitializeDocumentStructure(unittest.TestCase):

    def test_page_separators_inserted(self):
        # Arrange
        lines = (
            _l(
                "Line 1",
                "Line 2",
                "Line 3",
            )
            + _l(
                "Line 4",
                "Line 5",
                page_index=1,
            )
            + _l(
                "Line 6",
                page_index=2,
            )
        )

        # Act
        result = list(initialize_document_structure(lines))

        # Assert
        assert_elements_equal(
            result,
            [
                Node(type="page_separator", data=dict(page_index=0), children=[]),
                *make_text_spans("Line 1", "Line 2", "Line 3"),
                Node(type="page_separator", data=dict(page_index=1), children=[]),
                *make_text_spans("Line 4", "Line 5"),
                Node(type="page_separator", data=dict(page_index=2), children=[]),
                *make_text_spans("Line 6"),
            ],
        )


class TestParseTablesOfContents(unittest.TestCase):

    def test_parse_tables_of_contents(self):
        # Arrange
        lines = make_text_spans(
            "Line 1", "Sommaire", "bla ..... page 1", "blo ..... page 2", "Line 2"
        )

        # Act
        elements = list(parse_tables_of_contents(lines))

        # Assert
        assert_elements_equal(
            elements,
            [
                *make_text_spans("Line 1"),
                Node(
                    type="table_of_contents",
                    data=dict(),
                    children=make_text_spans(
                        "Sommaire",
                        "bla ..... page 1",
                        "blo ..... page 2",
                    ),
                ),
                *make_text_spans("Line 2"),
            ],
        )


class TestRenderTableOfContents(unittest.TestCase):

    def setUp(self):
        self.soup = BeautifulSoup("", "html.parser")

    def test_simple_render(self):
        # Arrange
        node = Node(
            type="table_of_contents",
            children=[
                Node(type="text_span", children=_l("Sommaire")),
                Node(type="text_span", children=_l("bla ..... page 1")),
                Node(type="text_span", children=_l("blo ..... page 2")),
            ],
        )

        # Act
        rendered = render_table_of_contents(self.soup, node)

        # Assert
        assert normalized_html_str(str(rendered)) == normalized_html_str(
            """
            <div class="arretify-table_of_contents">
                <div>Sommaire</div>
                <div>bla ..... page 1</div>
                <div>blo ..... page 2</div>
            </div>
        """
        )
