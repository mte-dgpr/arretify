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
from .basic_elements import (
    list_indentation,
    parse_lists,
    parse_tables,
    parse_blockquotes,
    render_inline_quotes,
)
from .testing import assert_node_flows_equal, _l


class TestListIndentation(unittest.TestCase):

    def test_correct_indentation(self):
        # Arrange
        line = "    - Item in list"

        # Act
        result = list_indentation(line)

        # Assert
        assert result == 4, "Should return the correct indentation level"

    def test_no_indentation(self):
        # Arrange
        line = "- Item in list"

        # Act
        result = list_indentation(line)

        # Assert
        assert result == 0, "Should return zero for no indentation"

    def test_not_a_list_element(self):
        # Arrange
        line = "This is not a list item"

        # Act / Assert
        with self.assertRaises(ValueError) as context:
            list_indentation(line)
        assert (
            str(context.exception) == "Expected line to be a list element"
        ), "Should raise ValueError for non-list lines"


class TestParseTables(unittest.TestCase):

    def test_simple_table(self):
        # Arrange
        lines = _l(
            "| Polluant | Concentration maximale en mg/l |",
            "|---------|---------------------------------|",
            "| MES     | 35                               |",
            "| DCO     | 125                              |",
            "| Hydrocarbures totaux | 10                             |",
            "END",
        )

        # Act
        node_flow = parse_tables(lines)

        # Assert
        assert_node_flows_equal(
            node_flow,
            [
                Node(
                    type="table",
                    children=[
                        _l(
                            "| Polluant | Concentration maximale en mg/l |",
                            "|---------|---------------------------------|",
                            "| MES     | 35                               |",
                            "| DCO     | 125                              |",
                            "| Hydrocarbures totaux | 10                             |",
                        )
                    ],
                ),
                _l("END"),
            ],
        )

    def test_table_description(self):
        # Arrange
        lines = _l(
            "| Polluant | Concentration maximale en mg/l |",
            "|---------|---------------------------------|",
            "| MES     | 35                               |",
            "(*) bla bla",
            "END",
        )

        # Act
        node_flow = parse_tables(lines)

        # Assert
        assert_node_flows_equal(
            node_flow,
            [
                Node(
                    type="table",
                    children=[
                        _l(
                            "| Polluant | Concentration maximale en mg/l |",
                            "|---------|---------------------------------|",
                            "| MES     | 35                               |",
                        ),
                    ],
                ),
                Node(
                    type="table_description",
                    children=[
                        _l("(*) bla bla"),
                    ],
                ),
                _l("END"),
            ],
        )


class TestParseList(unittest.TestCase):

    def test_simple_list(self):
        # Arrange
        lines = _l("- Item 1", "- Item 2", "- Item 3", "END")

        # Act
        node_flow = parse_lists(lines)

        # Assert
        assert_node_flows_equal(
            node_flow,
            [
                Node(
                    type="list",
                    children=[
                        _l("- Item 1", "- Item 2", "- Item 3"),
                    ],
                ),
                _l("END"),
            ],
        )

    def test_nested_list(self):
        # Arrange
        lines = _l(
            "- Item 1",
            "  - Subitem 1.1",
            "  - Subitem 1.2",
            "- Item 2",
        )

        # Act
        node_flow = parse_lists(lines)

        # Assert
        print(node_flow)
        assert_node_flows_equal(
            node_flow,
            [
                Node(
                    type="list",
                    children=[_l("- Item 1", "  - Subitem 1.1", "  - Subitem 1.2", "- Item 2")],
                ),
            ],
        )


class TestParseBlockQuote(unittest.TestCase):

    def test_blockquote_nested_list(self):
        # Arrange
        lines = _l(
            '"bla bla',
            "blo blo :",
            "- Item 1",
            '- Item 2"',
            "END",
        )

        # Act
        node_flow = parse_blockquotes(lines)

        # Assert
        assert_node_flows_equal(
            node_flow,
            [
                Node(
                    type="blockquote",
                    children=[
                        _l(
                            "bla bla",
                            "blo blo :",
                        ),
                        Node(
                            type="list",
                            children=[
                                _l(
                                    "- Item 1",
                                    "- Item 2",
                                ),
                            ],
                        ),
                    ],
                ),
                _l("END"),
            ],
        )

    def test_blockquote_one_liner_nested_blockquote(self):
        # Arrange
        lines = _l(
            '"bla bla',
            '"blo blo"',
            'bli bli"',
            "END",
        )

        # Act
        node_flow = parse_blockquotes(lines)

        # Assert
        assert_node_flows_equal(
            node_flow,
            [
                Node(
                    type="blockquote",
                    children=[
                        _l("bla bla", '"blo blo"', "bli bli"),
                    ],
                ),
                _l("END"),
            ],
        )

    def test_blockquote_nested_inline_quote(self):
        # Arrange
        lines = _l(
            '"bla bla',
            'blo blo "haha"',
            'bli bli"',
            "END",
        )

        # Act
        node_flow = parse_blockquotes(lines)

        # Assert
        assert_node_flows_equal(
            node_flow,
            [
                Node(
                    type="blockquote",
                    children=[
                        _l(
                            "bla bla",
                            'blo blo "haha"',
                            "bli bli",
                        )
                    ],
                ),
                _l("END"),
            ],
        )

    def test_blockquote_one_line(self):
        # Arrange
        lines = _l(
            '"bla bla"',
            "END",
        )

        # Act
        node_flow = parse_blockquotes(lines)

        # Assert
        assert_node_flows_equal(
            node_flow,
            [
                Node(
                    type="blockquote",
                    children=[
                        _l("bla bla"),
                    ],
                ),
                _l("END"),
            ],
        )


class TestParseInlineQuotes(unittest.TestCase):

    def setUp(self):
        self.soup = BeautifulSoup("", "html.parser")

    def test_inline_quote(self):
        # Arrange
        line = 'bla bla "haha" bli bli'

        # Act
        result = render_inline_quotes(self.soup, line)

        # Assert
        assert [str(element) for element in result] == [
            "bla bla ",
            "<q>haha</q>",
            " bli bli",
        ]
