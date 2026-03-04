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

from arretify.errors import ErrorCodes
from arretify.law_data.french_addresses import ALL_STREET_NAMES
from arretify.semantic_tag_specs import AddressSpec, ErrorSpec, TableOfContentsSpec
from arretify.step_segmentation.semantic_tag_specs import (
    SEGMENTATION_TAG_NAME,
    BlockquoteSegmentationSpec,
    ListSegmentationSpec,
    TableDescriptionSegmentationSpec,
    TextSpanSegmentationData,
    TextSpanSegmentationSpec,
)
from arretify.utils.html_create import wrap_in_tag
from arretify.utils.html_semantic import create_semantic_tag_spec_no_data

from .basic_elements import (
    parse_addresses,
    parse_blockquotes,
    parse_lists,
    parse_tables,
    parse_tables_of_contents,
    parse_unknown_elements,
)
from .testing import BaseTestCaseSegmentation, assert_segmentation_element_lists_equal

SomeTagSpec = create_semantic_tag_spec_no_data(
    spec_name="segmentation:some_tag",
    tag_name=SEGMENTATION_TAG_NAME,
)


class TestParseTables(BaseTestCaseSegmentation):

    def test_table_description(self):
        # Arrange
        table = self.make_tag(
            "table",
            contents=[
                self.make_tag(
                    "thead",
                    contents=[
                        self.make_tag(
                            "tr",
                            contents=[
                                self.make_tag("th", contents=["Polluant"]),
                                self.make_tag("th", contents=["Concentration maximale en mg/l"]),
                            ],
                        )
                    ],
                ),
            ],
        )

        elements = [
            table,
            *self.make_text_spans(
                "(*) bla bla",
                "Polluant : Matières en suspension (MES)",
                "END",
            ),
        ]

        # Act
        result = parse_tables(self.context, elements)

        # Assert
        assert_segmentation_element_lists_equal(
            result,
            [
                table,
                self.make_semantic_tag(
                    TableDescriptionSegmentationSpec,
                    contents=self.make_text_spans(
                        "(*) bla bla", "Polluant : Matières en suspension (MES)"
                    ),
                ),
                *self.make_text_spans("END"),
            ],
        )


class TestParseList(BaseTestCaseSegmentation):

    def test_simple_list(self):
        # Arrange
        elements = self.make_text_spans("- Item 1", "- Item 2", "- Item 3", "END")

        # Act
        result = parse_lists(self.context, elements)

        # Assert
        assert_segmentation_element_lists_equal(
            result,
            [
                self.make_semantic_tag(
                    ListSegmentationSpec,
                    contents=self.make_text_spans("- Item 1", "- Item 2", "- Item 3"),
                ),
                *self.make_text_spans("END"),
            ],
        )

    def test_nested_list(self):
        # Arrange
        elements = self.make_text_spans(
            "- Item 1",
            "  - Subitem 1.1",
            "  - Subitem 1.2",
            "- Item 2",
        )

        # Act
        result = parse_lists(self.context, elements)

        # Assert
        assert_segmentation_element_lists_equal(
            result,
            [
                self.make_semantic_tag(
                    ListSegmentationSpec,
                    contents=self.make_text_spans(
                        "- Item 1", "  - Subitem 1.1", "  - Subitem 1.2", "- Item 2"
                    ),
                ),
            ],
        )

    def test_continuing_previous_sentence(self):
        # Arrange
        elements = [
            # Use precise data to ensure that the two spans are merged correctly
            self.make_semantic_tag(
                TextSpanSegmentationSpec,
                contents=[
                    "- Item 1",
                ],
                data=TextSpanSegmentationData(start=[0, 0, 0], end=[0, 0, 8]),
            ),
            self.make_semantic_tag(
                TextSpanSegmentationSpec,
                contents=[
                    "this is a continuation of the previous sentence.",
                ],
                data=TextSpanSegmentationData(start=[0, 1, 0], end=[0, 1, 48]),
            ),
            *self.make_text_spans("- Item 2", "END"),
        ]

        # Act
        result = parse_lists(self.context, elements)

        # Assert
        assert_segmentation_element_lists_equal(
            result,
            [
                self.make_semantic_tag(
                    ListSegmentationSpec,
                    contents=[
                        self.make_semantic_tag(
                            TextSpanSegmentationSpec,
                            contents=[
                                "- Item 1",
                                " this is a continuation of the previous sentence.",
                            ],
                            data=TextSpanSegmentationData(start=[0, 0, 0], end=[0, 1, 48]),
                        ),
                        *self.make_text_spans("- Item 2"),
                    ],
                ),
                *self.make_text_spans("END"),
            ],
        )


class TestParseBlockQuote(BaseTestCaseSegmentation):

    def test_simple_blockquote(self):
        # Arrange
        elements = [
            self.make_semantic_tag(SomeTagSpec),
            *self.make_text_spans(
                '"This is',
                'a blockquote"',
                "END",
            ),
        ]

        # Act
        result = parse_blockquotes(self.context, elements)

        # Assert
        assert_segmentation_element_lists_equal(
            result,
            [
                self.make_semantic_tag(SomeTagSpec),
                self.make_semantic_tag(
                    BlockquoteSegmentationSpec,
                    contents=self.make_text_spans("This is", "a blockquote"),
                ),
                *self.make_text_spans("END"),
            ],
        )

    def test_blockquote_nested_list(self):
        # Arrange
        elements = self.make_text_spans(
            '"bla bla',
            "blo blo :",
            "- Item 1",
            '- Item 2"',
            "END",
        )

        # Act
        result = parse_blockquotes(self.context, elements)

        # Assert
        assert_segmentation_element_lists_equal(
            result,
            [
                self.make_semantic_tag(
                    BlockquoteSegmentationSpec,
                    contents=[
                        *self.make_text_spans(
                            "bla bla",
                            "blo blo :",
                        ),
                        self.make_semantic_tag(
                            ListSegmentationSpec,
                            contents=self.make_text_spans(
                                "- Item 1",
                                "- Item 2",
                            ),
                        ),
                    ],
                ),
                *self.make_text_spans("END"),
            ],
        )

    def test_blockquote_one_liner_nested_blockquote(self):
        # Arrange
        elements = self.make_text_spans(
            '"bla bla',
            '"blo blo"',
            'bli bli"',
            "END",
        )

        # Act
        result = parse_blockquotes(self.context, elements)

        # Assert
        assert_segmentation_element_lists_equal(
            result,
            [
                self.make_semantic_tag(
                    BlockquoteSegmentationSpec,
                    contents=self.make_text_spans("bla bla", '"blo blo"', "bli bli"),
                ),
                *self.make_text_spans("END"),
            ],
        )

    def test_blockquote_nested_inline_quote(self):
        # Arrange
        elements = self.make_text_spans(
            '"bla bla',
            'blo blo "haha"',
            'bli bli"',
            "END",
        )

        # Act
        result = parse_blockquotes(self.context, elements)

        # Assert
        assert_segmentation_element_lists_equal(
            result,
            [
                self.make_semantic_tag(
                    BlockquoteSegmentationSpec,
                    contents=self.make_text_spans(
                        "bla bla",
                        'blo blo "haha"',
                        "bli bli",
                    ),
                ),
                *self.make_text_spans("END"),
            ],
        )

    def test_blockquote_one_line(self):
        # Arrange
        elements = self.make_text_spans(
            '"bla bla"',
            "END",
        )

        # Act
        result = parse_blockquotes(self.context, elements)

        # Assert
        assert_segmentation_element_lists_equal(
            result,
            [
                self.make_semantic_tag(
                    BlockquoteSegmentationSpec,
                    contents=self.make_text_spans("bla bla"),
                ),
                *self.make_text_spans("END"),
            ],
        )

    def test_blockquote_with_image_in_middle(self):
        # Arrange
        img_tag = self.make_tag("img", attrs=dict(src="photo.png", alt="Photo"))
        elements = [
            *self.make_text_spans('"bla bla'),
            img_tag,
            *self.make_text_spans('bli bli"', "END"),
        ]

        # Act
        result = parse_blockquotes(self.context, elements)

        # Assert
        assert_segmentation_element_lists_equal(
            result,
            [
                self.make_semantic_tag(
                    BlockquoteSegmentationSpec,
                    contents=[
                        *self.make_text_spans("bla bla"),
                        img_tag,
                        *self.make_text_spans("bli bli"),
                    ],
                ),
                *self.make_text_spans("END"),
            ],
        )


class TestParseAddresses(BaseTestCaseSegmentation):

    def test_simple_address(self):
        # Arrange

        elements = ["Some text before ", "123 bis rue de la Paix, 75002 Paris.", " Some text after"]

        # Act
        result = parse_addresses(self.context, elements)

        # Assert
        assert_segmentation_element_lists_equal(
            result,
            [
                "Some text before ",
                self.make_semantic_tag(AddressSpec, contents=["123 bis rue de la Paix"]),
                ", 75002 Paris. Some text after",
            ],
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
        assert_segmentation_element_lists_equal(
            result,
            [
                "Some text before ",
                self.make_semantic_tag(AddressSpec, contents=["123 bis rue jean moulin"]),
                ", 75002 Paris. Some text after",
            ],
        )


class TestParseTablesOfContents(BaseTestCaseSegmentation):

    def test_parse_tables_of_contents(self):
        # Arrange
        lines = self.make_text_spans(
            "Line 1", "Sommaire", "bla ..... page 1", "blo ..... page 2", "Line 2"
        )

        # Act
        elements = parse_tables_of_contents(self.context, lines)

        # Assert
        assert_segmentation_element_lists_equal(
            elements,
            [
                *self.make_text_spans("Line 1"),
                self.make_semantic_tag(
                    TableOfContentsSpec,
                    contents=wrap_in_tag(
                        self.soup,
                        "div",
                        [
                            "Sommaire",
                            "bla ..... page 1",
                            "blo ..... page 2",
                        ],
                    ),
                ),
                *self.make_text_spans("Line 2"),
            ],
        )


class TestParseUnknownElements(BaseTestCaseSegmentation):

    def test_parse_unknown_elements(self):
        # Arrange
        some_spec = create_semantic_tag_spec_no_data(
            spec_name="some_spec",
            tag_name="div",
            allowed_contents=tuple(),  # nothing allowed
        )
        other_spec = create_semantic_tag_spec_no_data(
            spec_name="other_spec",
            tag_name="div",
        )
        contents = [
            self.make_semantic_tag(other_spec),
            "Unknown str element",
            self.make_tag("span", contents=["Unknown tag element"]),
        ]

        # Act
        result = parse_unknown_elements(self.context, some_spec, contents)

        # Assert
        assert_segmentation_element_lists_equal(
            result,
            [
                self.make_semantic_tag(
                    ErrorSpec,
                    contents=[
                        self.make_semantic_tag(other_spec),
                    ],
                    data=ErrorSpec.data_model(error_codes=[ErrorCodes.unknown_content]),
                ),
                self.make_semantic_tag(
                    ErrorSpec,
                    contents=["Unknown str element"],
                    data=ErrorSpec.data_model(error_codes=[ErrorCodes.unknown_content]),
                ),
                self.make_semantic_tag(
                    ErrorSpec,
                    contents=[
                        self.make_tag("span", contents=["Unknown tag element"]),
                    ],
                    data=ErrorSpec.data_model(error_codes=[ErrorCodes.unknown_content]),
                ),
            ],
        )
