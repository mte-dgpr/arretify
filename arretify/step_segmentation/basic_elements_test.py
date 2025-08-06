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
    _list_indentation,
    parse_lists,
    parse_tables,
    parse_blockquotes,
    parse_images,
    render_inline_quotes,
    render_table,
    render_table_description,
    render_list,
)
from .testing import assert_elements_equal, _l, make_text_spans
from arretify.utils.testing import normalized_html_str, assert_html_list_equal


class TestListIndentation(unittest.TestCase):

    def test_correct_indentation(self):
        # Arrange
        line = "    - Item in list"

        # Act
        result = _list_indentation(line)

        # Assert
        assert result == 4, "Should return the correct indentation level"

    def test_no_indentation(self):
        # Arrange
        line = "- Item in list"

        # Act
        result = _list_indentation(line)

        # Assert
        assert result == 0, "Should return zero for no indentation"

    def test_not_a_list_element(self):
        # Arrange
        line = "This is not a list item"

        # Act / Assert
        with self.assertRaises(ValueError) as context:
            _list_indentation(line)
        assert (
            str(context.exception) == "Expected line to be a list element"
        ), "Should raise ValueError for non-list lines"


class TestParseTables(unittest.TestCase):

    def test_simple_table(self):
        # Arrange
        elements = make_text_spans(
            "| Polluant | Concentration maximale en mg/l |",
            "|---------|---------------------------------|",
            "| MES     | 35                               |",
            "| DCO     | 125                              |",
            "| Hydrocarbures totaux | 10                             |",
            "END",
        )

        # Act
        elements = parse_tables(elements)

        # Assert
        assert_elements_equal(
            elements,
            [
                Node(
                    type="table",
                    children=make_text_spans(
                        "| Polluant | Concentration maximale en mg/l |",
                        "|---------|---------------------------------|",
                        "| MES     | 35                               |",
                        "| DCO     | 125                              |",
                        "| Hydrocarbures totaux | 10                             |",
                    ),
                ),
                *make_text_spans("END"),
            ],
        )

    def test_table_description(self):
        # Arrange
        elements = make_text_spans(
            "| Polluant | Concentration maximale en mg/l |",
            "|---------|---------------------------------|",
            "| MES     | 35                               |",
            "(*) bla bla",
            "Polluant : Matières en suspension (MES)",
            "END",
        )

        # Act
        result = parse_tables(elements)

        # Assert
        assert_elements_equal(
            result,
            [
                Node(
                    type="table",
                    children=make_text_spans(
                        "| Polluant | Concentration maximale en mg/l |",
                        "|---------|---------------------------------|",
                        "| MES     | 35                               |",
                    ),
                ),
                Node(
                    type="table_description",
                    children=make_text_spans(
                        "(*) bla bla", "Polluant : Matières en suspension (MES)"
                    ),
                ),
                *make_text_spans("END"),
            ],
        )

    def test_parse_tables_with_node_at_end(self):
        # Arrange
        elements = [
            *make_text_spans(
                "| Polluant | Concentration maximale en mg/l |",
                "|---------|---------------------------------|",
                "| MES     | 35                               |",
                "| DCO     | 125                              |",
            ),
            Node(
                type="page_separator",
                children=[],
                data=dict(page_index=1),
            ),
            *make_text_spans("END"),
        ]

        # Act
        result = parse_tables(elements)

        # Assert
        assert_elements_equal(
            result,
            [
                Node(
                    type="table",
                    children=make_text_spans(
                        "| Polluant | Concentration maximale en mg/l |",
                        "|---------|---------------------------------|",
                        "| MES     | 35                               |",
                        "| DCO     | 125                              |",
                    ),
                ),
                Node(
                    type="page_separator",
                    children=[],
                    data=dict(page_index=1),
                ),
                *make_text_spans("END"),
            ],
        )


class TestParseList(unittest.TestCase):

    def test_simple_list(self):
        # Arrange
        elements = make_text_spans("- Item 1", "- Item 2", "- Item 3", "END")

        # Act
        result = parse_lists(elements)

        # Assert
        assert_elements_equal(
            result,
            [
                Node(
                    type="list",
                    children=make_text_spans("- Item 1", "- Item 2", "- Item 3"),
                ),
                *make_text_spans("END"),
            ],
        )

    def test_nested_list(self):
        # Arrange
        elements = make_text_spans(
            "- Item 1",
            "  - Subitem 1.1",
            "  - Subitem 1.2",
            "- Item 2",
        )

        # Act
        result = parse_lists(elements)

        # Assert
        assert_elements_equal(
            result,
            [
                Node(
                    type="list",
                    children=make_text_spans(
                        "- Item 1", "  - Subitem 1.1", "  - Subitem 1.2", "- Item 2"
                    ),
                ),
            ],
        )

    def test_text_segment_continuing_previous_sentence(self):
        # Arrange
        elements = make_text_spans(
            "- Item 1",
            "this is a continuation of the previous sentence.",
            "- Item 2",
            "END",
        )

        # Act
        result = parse_lists(elements)

        # Assert
        assert_elements_equal(
            result,
            [
                Node(
                    type="list",
                    children=[
                        Node(
                            type="text_span",
                            children=_l(
                                "- Item 1", "this is a continuation of the previous sentence."
                            ),
                        ),
                        *make_text_spans("- Item 2"),
                    ],
                ),
                *make_text_spans("END"),
            ],
        )


class TestParseBlockQuote(unittest.TestCase):

    def test_simple_blockquote(self):
        # Arrange
        elements = [
            Node(type="some_node", children=[]),
            *make_text_spans(
                '"This is',
                'a blockquote"',
                "END",
            ),
        ]

        # Act
        result = parse_blockquotes(elements)

        # Assert
        assert_elements_equal(
            result,
            [
                Node(type="some_node", children=[]),
                Node(
                    type="blockquote",
                    children=make_text_spans("This is", "a blockquote"),
                ),
                *make_text_spans("END"),
            ],
        )

    def test_blockquote_nested_list(self):
        # Arrange
        lines = make_text_spans(
            '"bla bla',
            "blo blo :",
            "- Item 1",
            '- Item 2"',
            "END",
        )

        # Act
        result = parse_blockquotes(lines)

        # Assert
        assert_elements_equal(
            result,
            [
                Node(
                    type="blockquote",
                    children=[
                        *make_text_spans(
                            "bla bla",
                            "blo blo :",
                        ),
                        Node(
                            type="list",
                            children=make_text_spans(
                                "- Item 1",
                                "- Item 2",
                            ),
                        ),
                    ],
                ),
                *make_text_spans("END"),
            ],
        )

    def test_blockquote_one_liner_nested_blockquote(self):
        # Arrange
        elements = make_text_spans(
            '"bla bla',
            '"blo blo"',
            'bli bli"',
            "END",
        )

        # Act
        result = parse_blockquotes(elements)

        # Assert
        assert_elements_equal(
            result,
            [
                Node(
                    type="blockquote",
                    children=make_text_spans("bla bla", '"blo blo"', "bli bli"),
                ),
                *make_text_spans("END"),
            ],
        )

    def test_blockquote_nested_inline_quote(self):
        # Arrange
        elements = make_text_spans(
            '"bla bla',
            'blo blo "haha"',
            'bli bli"',
            "END",
        )

        # Act
        result = parse_blockquotes(elements)

        # Assert
        assert_elements_equal(
            result,
            [
                Node(
                    type="blockquote",
                    children=make_text_spans(
                        "bla bla",
                        'blo blo "haha"',
                        "bli bli",
                    ),
                ),
                *make_text_spans("END"),
            ],
        )

    def test_blockquote_one_line(self):
        # Arrange
        elements = make_text_spans(
            '"bla bla"',
            "END",
        )

        # Act
        result = parse_blockquotes(elements)

        # Assert
        assert_elements_equal(
            result,
            [
                Node(
                    type="blockquote",
                    children=make_text_spans("bla bla"),
                ),
                *make_text_spans("END"),
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


class TestRenderTable(unittest.TestCase):

    def setUp(self):
        self.soup = BeautifulSoup("", "html.parser")

    def test_render_table_with_page_separators(self):
        # Arrange
        node = Node(
            type="table",
            children=[
                *make_text_spans("| Column 1 | Column 2 |", "|----------|----------|"),
                Node(
                    type="page_separator",
                    children=[],
                    data=dict(page_index=1),
                ),
                *make_text_spans(
                    "| Row 1    | Data 1   |",
                ),
                Node(
                    type="page_separator",
                    children=[],
                    data=dict(page_index=2),
                ),
                *make_text_spans(
                    "| Row 2    | Data 2   |",
                ),
            ],
        )

        # Act
        table_tag = render_table(self.soup, node)

        # Assert
        assert normalized_html_str(str(table_tag)) == normalized_html_str(
            """
            <table>
                <thead>
                    <tr>
                        <th>Column 1</th>
                        <th>Column 2<a class="arretify-page_separator" data-page_index="1"></a></th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>Row 1</td>
                        <td>Data 1<a class="arretify-page_separator" data-page_index="2"></a></td>
                    </tr>
                    <tr>
                        <td>Row 2</td>
                        <td>Data 2</td>
                    </tr>
                </tbody>
            </table>
            """
        )


class TestRenderTableDescription(unittest.TestCase):

    def setUp(self):
        self.soup = BeautifulSoup("", "html.parser")

    def test_render_table_description_with_page_separators(self):
        # Arrange
        node = Node(
            type="table_description",
            children=[
                *make_text_spans("This is a description of the table."),
                Node(
                    type="page_separator",
                    children=[],
                    data=dict(page_index=1),
                ),
                *make_text_spans("This is another part of the description."),
            ],
        )

        # Act
        table_description_elements = list(render_table_description(self.soup, node))

        # Assert
        assert_html_list_equal(
            table_description_elements,
            [
                "<br/>",
                "This is a description of the table.",
                '<a class="arretify-page_separator" data-page_index="1"></a>',
                "<br/>",
                "This is another part of the description.",
            ],
        )


class TestRenderList(unittest.TestCase):
    def setUp(self):
        self.soup = BeautifulSoup("", "html.parser")

    def test_render_list_with_page_separator(self):
        # Arrange
        node = Node(
            type="list",
            children=[
                *make_text_spans("- Item 1"),
                Node(
                    type="page_separator",
                    children=[],
                    data=dict(page_index=1),
                ),
                *make_text_spans("- Item 2"),
            ],
        )

        # Act
        list_tag = render_list(self.soup, node)

        # Assert
        assert normalized_html_str(str(list_tag)) == normalized_html_str(
            """
            <ul>
                <li>- Item 1<a class="arretify-page_separator" data-page_index="1"></a></li>
                <li>- Item 2</li>
            </ul>
            """
        )

    def test_render_nested_list(self):
        # Arrange
        node = Node(
            type="list",
            children=[
                *make_text_spans("- Item 1", "  - Subitem 1.1", "  - Subitem 1.2", "- Item 2"),
            ],
        )

        # Act
        list_tag = render_list(self.soup, node)

        # Assert
        assert normalized_html_str(str(list_tag)) == normalized_html_str(
            """
            <ul>
                <li>- Item 1
                    <ul>
                        <li>- Subitem 1.1</li>
                        <li>- Subitem 1.2</li>
                    </ul>
                </li>
                <li>- Item 2</li>
            </ul>
            """
        )

    def test_render_list_text_span(self):
        # Arrange
        node = Node(
            type="list",
            children=[
                Node(
                    type="text_span",
                    children=_l("- Item 1", "This is a continuation of the previous sentence."),
                ),
                *make_text_spans("- Item 2"),
            ],
        )

        # Act
        list_tag = render_list(self.soup, node)

        # Assert
        assert normalized_html_str(str(list_tag)) == normalized_html_str(
            """
            <ul>
                <li>- Item 1 This is a continuation of the previous sentence.</li>
                <li>- Item 2</li>
            </ul>
            """
        )


class TestParseImage(unittest.TestCase):

    def test_parse_image(self):
        # Arrange
        elements = make_text_spans(
            "![Image description](image_url.jpg)",
            "END",
        )

        # Act
        result = parse_images(elements)

        # Assert
        assert_elements_equal(
            result,
            [
                Node(
                    type="image",
                    data=dict(),
                    children=make_text_spans("![Image description](image_url.jpg)"),
                ),
                *make_text_spans("END"),
            ],
        )
