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

from .core import make_segmentation_tag
from .basic_elements import (
    _list_indentation,
    parse_lists,
    parse_tables,
    parse_blockquotes,
    parse_images,
    parse_addresses,
    render_inline_quotes,
    render_table,
    render_table_description,
    render_list,
    render_address,
    render_blockquote,
)
from .testing import assert_elements_equal, make_text_spans
from arretify.utils.testing import (
    create_document_context,
    normalized_html_str,
    assert_html_list_equal,
)
from arretify.law_data.french_addresses import ALL_STREET_NAMES


class BaseTestCase(unittest.TestCase):
    def setUp(self):
        self.context = create_document_context()
        self.soup = self.context.soup


class TestListIndentation(BaseTestCase):

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


class TestParseTables(BaseTestCase):

    def test_simple_table(self):
        # Arrange
        elements = make_text_spans(
            self.soup,
            "| Polluant | Concentration maximale en mg/l |",
            "|---------|---------------------------------|",
            "| MES     | 35                               |",
            "| DCO     | 125                              |",
            "| Hydrocarbures totaux | 10                             |",
            "END",
        )

        # Act
        elements = parse_tables(self.context, elements)

        # Assert
        assert_elements_equal(
            elements,
            [
                make_segmentation_tag(
                    self.soup,
                    "table",
                    contents=make_text_spans(
                        self.soup,
                        "| Polluant | Concentration maximale en mg/l |",
                        "|---------|---------------------------------|",
                        "| MES     | 35                               |",
                        "| DCO     | 125                              |",
                        "| Hydrocarbures totaux | 10                             |",
                    ),
                ),
                *make_text_spans(self.soup, "END"),
            ],
            ignore_text_span_data=True,
        )

    def test_table_description(self):
        # Arrange
        elements = make_text_spans(
            self.soup,
            "| Polluant | Concentration maximale en mg/l |",
            "|---------|---------------------------------|",
            "| MES     | 35                               |",
            "(*) bla bla",
            "Polluant : Matières en suspension (MES)",
            "END",
        )

        # Act
        result = parse_tables(self.context, elements)

        # Assert
        assert_elements_equal(
            result,
            [
                make_segmentation_tag(
                    self.soup,
                    "table",
                    contents=make_text_spans(
                        self.soup,
                        "| Polluant | Concentration maximale en mg/l |",
                        "|---------|---------------------------------|",
                        "| MES     | 35                               |",
                    ),
                ),
                make_segmentation_tag(
                    self.soup,
                    "table_description",
                    contents=make_text_spans(
                        self.soup, "(*) bla bla", "Polluant : Matières en suspension (MES)"
                    ),
                ),
                *make_text_spans(self.soup, "END"),
            ],
            ignore_text_span_data=True,
        )

    def test_parse_tables_with_tag_at_end(self):
        # Arrange
        elements = [
            *make_text_spans(
                self.soup,
                "| Polluant | Concentration maximale en mg/l |",
                "|---------|---------------------------------|",
                "| MES     | 35                               |",
                "| DCO     | 125                              |",
            ),
            make_segmentation_tag(self.soup, "page_separator", data=dict(page_index=1)),
            *make_text_spans(self.soup, "END"),
        ]

        # Act
        result = parse_tables(self.context, elements)

        # Assert
        assert_elements_equal(
            result,
            [
                make_segmentation_tag(
                    self.soup,
                    "table",
                    contents=make_text_spans(
                        self.soup,
                        "| Polluant | Concentration maximale en mg/l |",
                        "|---------|---------------------------------|",
                        "| MES     | 35                               |",
                        "| DCO     | 125                              |",
                    ),
                ),
                make_segmentation_tag(self.soup, "page_separator", data=dict(page_index=1)),
                *make_text_spans(self.soup, "END"),
            ],
            ignore_text_span_data=True,
        )


class TestParseList(BaseTestCase):

    def test_simple_list(self):
        # Arrange
        elements = make_text_spans(self.soup, "- Item 1", "- Item 2", "- Item 3", "END")

        # Act
        result = parse_lists(self.context, elements)

        # Assert
        assert_elements_equal(
            result,
            [
                make_segmentation_tag(
                    self.soup,
                    "list",
                    contents=make_text_spans(self.soup, "- Item 1", "- Item 2", "- Item 3"),
                ),
                *make_text_spans(self.soup, "END"),
            ],
            ignore_text_span_data=True,
        )

    def test_nested_list(self):
        # Arrange
        elements = make_text_spans(
            self.soup,
            "- Item 1",
            "  - Subitem 1.1",
            "  - Subitem 1.2",
            "- Item 2",
        )

        # Act
        result = parse_lists(self.context, elements)

        # Assert
        assert_elements_equal(
            result,
            [
                make_segmentation_tag(
                    self.soup,
                    "list",
                    contents=make_text_spans(
                        self.soup, "- Item 1", "  - Subitem 1.1", "  - Subitem 1.2", "- Item 2"
                    ),
                ),
            ],
            ignore_text_span_data=True,
        )

    def test_continuing_previous_sentence(self):
        # Arrange
        elements = make_text_spans(
            self.soup,
            "- Item 1",
            "this is a continuation of the previous sentence.",
            "- Item 2",
            "END",
        )

        # Act
        result = parse_lists(self.context, elements)

        # Assert
        assert_elements_equal(
            result,
            [
                make_segmentation_tag(
                    self.soup,
                    "list",
                    contents=[
                        make_segmentation_tag(
                            self.soup,
                            "text_span",
                            contents=[
                                "- Item 1",
                                " this is a continuation of the previous sentence.",
                            ],
                        ),
                        *make_text_spans(self.soup, "- Item 2"),
                    ],
                ),
                *make_text_spans(self.soup, "END"),
            ],
            ignore_text_span_data=True,
            ignore_data_if_omitted=True,
        )


class TestParseBlockQuote(BaseTestCase):

    def test_simple_blockquote(self):
        # Arrange
        elements = [
            make_segmentation_tag(self.soup, "some_tag"),
            *make_text_spans(
                self.soup,
                '"This is',
                'a blockquote"',
                "END",
            ),
        ]

        # Act
        result = parse_blockquotes(self.context, elements)

        # Assert
        assert_elements_equal(
            result,
            [
                make_segmentation_tag(self.soup, "some_tag"),
                make_segmentation_tag(
                    self.soup,
                    "blockquote",
                    contents=make_text_spans(self.soup, "This is", "a blockquote"),
                ),
                *make_text_spans(self.soup, "END"),
            ],
            ignore_text_span_data=True,
        )

    def test_blockquote_nested_list(self):
        # Arrange
        elements = make_text_spans(
            self.soup,
            '"bla bla',
            "blo blo :",
            "- Item 1",
            '- Item 2"',
            "END",
        )

        # Act
        result = parse_blockquotes(self.context, elements)

        # Assert
        assert_elements_equal(
            result,
            [
                make_segmentation_tag(
                    self.soup,
                    "blockquote",
                    contents=[
                        *make_text_spans(
                            self.soup,
                            "bla bla",
                            "blo blo :",
                        ),
                        make_segmentation_tag(
                            self.soup,
                            "list",
                            contents=make_text_spans(
                                self.soup,
                                "- Item 1",
                                "- Item 2",
                            ),
                        ),
                    ],
                ),
                *make_text_spans(self.soup, "END"),
            ],
            ignore_text_span_data=True,
        )

    def test_blockquote_one_liner_nested_blockquote(self):
        # Arrange
        elements = make_text_spans(
            self.soup,
            '"bla bla',
            '"blo blo"',
            'bli bli"',
            "END",
        )

        # Act
        result = parse_blockquotes(self.context, elements)

        # Assert
        assert_elements_equal(
            result,
            [
                make_segmentation_tag(
                    self.soup,
                    "blockquote",
                    contents=make_text_spans(self.soup, "bla bla", '"blo blo"', "bli bli"),
                ),
                *make_text_spans(self.soup, "END"),
            ],
            ignore_text_span_data=True,
        )

    def test_blockquote_nested_inline_quote(self):
        # Arrange
        elements = make_text_spans(
            self.soup,
            '"bla bla',
            'blo blo "haha"',
            'bli bli"',
            "END",
        )

        # Act
        result = parse_blockquotes(self.context, elements)

        # Assert
        assert_elements_equal(
            result,
            [
                make_segmentation_tag(
                    self.soup,
                    "blockquote",
                    contents=make_text_spans(
                        self.soup,
                        "bla bla",
                        'blo blo "haha"',
                        "bli bli",
                    ),
                ),
                *make_text_spans(self.soup, "END"),
            ],
            ignore_text_span_data=True,
        )

    def test_blockquote_one_line(self):
        # Arrange
        elements = make_text_spans(
            self.soup,
            '"bla bla"',
            "END",
        )

        # Act
        result = parse_blockquotes(self.context, elements)

        # Assert
        assert_elements_equal(
            result,
            [
                make_segmentation_tag(
                    self.soup,
                    "blockquote",
                    contents=make_text_spans(self.soup, "bla bla"),
                ),
                *make_text_spans(self.soup, "END"),
            ],
            ignore_text_span_data=True,
        )


class TestParseInlineQuotes(BaseTestCase):

    def test_inline_quote(self):
        # Arrange
        line = 'bla bla "haha" bli bli'

        # Act
        result = render_inline_quotes(self.context, line)

        # Assert
        assert [str(element) for element in result] == [
            "bla bla ",
            "<q>haha</q>",
            " bli bli",
        ]


class TestRenderTable(BaseTestCase):

    def test_render_table_with_page_separators(self):
        # Arrange
        tag = make_segmentation_tag(
            self.soup,
            "table",
            contents=[
                *make_text_spans(self.soup, "| Column 1 | Column 2 |", "|----------|----------|"),
                make_segmentation_tag(self.soup, "page_separator", data=dict(page_index=1)),
                *make_text_spans(
                    self.soup,
                    "| Row 1    | Data 1   |",
                ),
                make_segmentation_tag(self.soup, "page_separator", data=dict(page_index=2)),
                *make_text_spans(
                    self.soup,
                    "| Row 2    | Data 2   |",
                ),
            ],
        )

        # Act
        table_tag = render_table(self.context, tag)

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


class TestRenderTableDescription(BaseTestCase):

    def test_render_table_description_with_page_separators(self):
        # Arrange
        tag = make_segmentation_tag(
            self.soup,
            "table_description",
            contents=[
                *make_text_spans(self.soup, "This is a description of the table."),
                make_segmentation_tag(self.soup, "page_separator", data=dict(page_index=1)),
                *make_text_spans(self.soup, "This is another part of the description."),
            ],
        )

        # Act
        table_description_elements = list(render_table_description(self.context, tag))

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


class TestRenderList(BaseTestCase):

    def test_render_list_with_page_separator(self):
        # Arrange
        tag = make_segmentation_tag(
            self.soup,
            "list",
            contents=[
                *make_text_spans(self.soup, "- Item 1"),
                make_segmentation_tag(self.soup, "page_separator", data=dict(page_index=1)),
                *make_text_spans(self.soup, "- Item 2"),
            ],
        )

        # Act
        list_tag = render_list(self.context, tag)

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
        tag = make_segmentation_tag(
            self.soup,
            "list",
            contents=[
                *make_text_spans(
                    self.soup, "- Item 1", "  - Subitem 1.1", "  - Subitem 1.2", "- Item 2"
                ),
            ],
        )

        # Act
        list_tag = render_list(self.context, tag)

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
        tag = make_segmentation_tag(
            self.soup,
            "list",
            contents=[
                make_segmentation_tag(
                    self.soup,
                    "text_span",
                    contents=["- Item 1", " This is a continuation of the previous sentence."],
                ),
                *make_text_spans(self.soup, "- Item 2"),
            ],
        )

        # Act
        list_tag = render_list(self.context, tag)

        # Assert
        assert normalized_html_str(str(list_tag)) == normalized_html_str(
            """
            <ul>
                <li>- Item 1 This is a continuation of the previous sentence.</li>
                <li>- Item 2</li>
            </ul>
            """
        )


class TestParseImage(BaseTestCase):

    def test_parse_image(self):
        # Arrange
        elements = make_text_spans(
            self.soup,
            "![Image description](image_url.jpg)",
            "END",
        )

        # Act
        result = parse_images(self.context, elements)

        # Assert
        assert_elements_equal(
            result,
            [
                make_segmentation_tag(
                    self.soup,
                    "image",
                    contents=make_text_spans(self.soup, "![Image description](image_url.jpg)"),
                    data=dict(),
                ),
                *make_text_spans(self.soup, "END"),
            ],
            ignore_text_span_data=True,
        )


class TestParseAddresses(BaseTestCase):

    def test_simple_address(self):
        # Arrange

        elements = ["Some text before ", "123 bis rue de la Paix, 75002 Paris.", " Some text after"]

        # Act
        result = parse_addresses(self.context, elements)

        # Assert
        assert_elements_equal(
            result,
            [
                "Some text before ",
                make_segmentation_tag(self.soup, "address", contents=["123 bis rue de la Paix"]),
                ", 75002 Paris. Some text after",
            ],
            ignore_text_span_data=True,
        )

    def test_street_name_greedy(self):
        # Arrange
        assert "rue jean" in ALL_STREET_NAMES
        assert "rue jean moulin" in ALL_STREET_NAMES
        elements = [
            "Some text before ",
            "123 bis rue jean moulin, 75002 Paris.",
            " Some text after",
        ]

        # Act
        result = parse_addresses(self.context, elements)

        # Assert
        assert_elements_equal(
            result,
            [
                "Some text before ",
                make_segmentation_tag(self.soup, "address", contents=["123 bis rue jean moulin"]),
                ", 75002 Paris. Some text after",
            ],
            ignore_text_span_data=True,
        )


class TestRenderAddress(BaseTestCase):

    def test_render_address(self):
        # Arrange
        tag = make_segmentation_tag(self.soup, "address", contents=["123 bis rue de la Paix"])

        # Act
        address_tag = render_address(self.context, tag)

        # Assert
        assert normalized_html_str(str(address_tag)) == normalized_html_str(
            """
            <address>123 bis rue de la Paix</address>
            """
        )


class TestRenderBlockQuote(BaseTestCase):

    def test_render_blockquote(self):
        # Arrange
        tag = make_segmentation_tag(
            self.soup,
            "blockquote",
            contents=make_text_spans(self.soup, "This is", "a blockquote"),
        )

        # Act
        blockquote_tag = render_blockquote(self.context, tag)

        # Assert
        assert normalized_html_str(str(blockquote_tag)) == normalized_html_str(
            """
            <blockquote>
                <p>This is</p>
                <p>a blockquote</p>
            </blockquote>
            """
        )
