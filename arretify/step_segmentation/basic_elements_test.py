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

from arretify.errors import ErrorCodes
from arretify.law_data.french_addresses import ALL_STREET_NAMES
from arretify.semantic_tag_specs import (
    AddressSpec,
    ErrorSpec,
    PageSeparatorData,
    PageSeparatorSpec,
    TableOfContentsSpec,
)
from arretify.step_segmentation.semantic_tag_specs import (
    SEGMENTATION_TAG_NAME,
    BlockquoteSegmentationSpec,
    ListSegmentationSpec,
    TableDescriptionSegmentationSpec,
    TableSegmentationSpec,
    TextSpanSegmentationData,
    TextSpanSegmentationSpec,
)
from arretify.utils.html_create import make_semantic_tag, make_tag, wrap_in_tag
from arretify.utils.html_semantic import create_semantic_tag_spec_no_data
from arretify.utils.testing import create_document_context

from .basic_elements import (
    parse_addresses,
    parse_blockquotes,
    parse_images,
    parse_lists,
    parse_tables,
    parse_tables_of_contents,
    parse_unknown_elements,
)
from .testing import assert_elements_equal, make_text_spans

SomeTagSpec = create_semantic_tag_spec_no_data(
    spec_name="segmentation:some_tag",
    tag_name=SEGMENTATION_TAG_NAME,
)


class BaseTestCase(unittest.TestCase):
    def setUp(self):
        self.context = create_document_context()
        self.soup = self.context.protected_soup


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
                make_semantic_tag(
                    self.soup,
                    TableSegmentationSpec,
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
                make_semantic_tag(
                    self.soup,
                    TableSegmentationSpec,
                    contents=make_text_spans(
                        self.soup,
                        "| Polluant | Concentration maximale en mg/l |",
                        "|---------|---------------------------------|",
                        "| MES     | 35                               |",
                    ),
                ),
                make_semantic_tag(
                    self.soup,
                    TableDescriptionSegmentationSpec,
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
            make_semantic_tag(self.soup, PageSeparatorSpec, data=PageSeparatorData(page_index=1)),
            *make_text_spans(self.soup, "END"),
        ]

        # Act
        result = parse_tables(self.context, elements)

        # Assert
        assert_elements_equal(
            result,
            [
                make_semantic_tag(
                    self.soup,
                    TableSegmentationSpec,
                    contents=make_text_spans(
                        self.soup,
                        "| Polluant | Concentration maximale en mg/l |",
                        "|---------|---------------------------------|",
                        "| MES     | 35                               |",
                        "| DCO     | 125                              |",
                    ),
                ),
                make_semantic_tag(
                    self.soup, PageSeparatorSpec, data=PageSeparatorData(page_index=1)
                ),
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
                make_semantic_tag(
                    self.soup,
                    ListSegmentationSpec,
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
                make_semantic_tag(
                    self.soup,
                    ListSegmentationSpec,
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
                make_semantic_tag(
                    self.soup,
                    ListSegmentationSpec,
                    contents=[
                        make_semantic_tag(
                            self.soup,
                            TextSpanSegmentationSpec,
                            contents=[
                                "- Item 1",
                                " this is a continuation of the previous sentence.",
                            ],
                            data=TextSpanSegmentationData(start=[0, 0, 0], end=[0, 1, 48]),
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
            make_semantic_tag(self.soup, SomeTagSpec),
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
                make_semantic_tag(self.soup, SomeTagSpec),
                make_semantic_tag(
                    self.soup,
                    BlockquoteSegmentationSpec,
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
                make_semantic_tag(
                    self.soup,
                    BlockquoteSegmentationSpec,
                    contents=[
                        *make_text_spans(
                            self.soup,
                            "bla bla",
                            "blo blo :",
                        ),
                        make_semantic_tag(
                            self.soup,
                            ListSegmentationSpec,
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
                make_semantic_tag(
                    self.soup,
                    BlockquoteSegmentationSpec,
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
                make_semantic_tag(
                    self.soup,
                    BlockquoteSegmentationSpec,
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
                make_semantic_tag(
                    self.soup,
                    BlockquoteSegmentationSpec,
                    contents=make_text_spans(self.soup, "bla bla"),
                ),
                *make_text_spans(self.soup, "END"),
            ],
            ignore_text_span_data=True,
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
                make_tag(
                    self.soup,
                    "img",
                    attrs=dict(src="image_url.jpg", alt="Image description"),
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
                make_semantic_tag(self.soup, AddressSpec, contents=["123 bis rue de la Paix"]),
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
                make_semantic_tag(self.soup, AddressSpec, contents=["123 bis rue jean moulin"]),
                ", 75002 Paris. Some text after",
            ],
            ignore_text_span_data=True,
        )


class TestParseTablesOfContents(unittest.TestCase):

    def setUp(self):
        self.context = create_document_context()
        self.soup = self.context.protected_soup

    def test_parse_tables_of_contents(self):
        # Arrange
        lines = make_text_spans(
            self.soup, "Line 1", "Sommaire", "bla ..... page 1", "blo ..... page 2", "Line 2"
        )

        # Act
        elements = parse_tables_of_contents(self.context, lines)

        # Assert
        assert_elements_equal(
            elements,
            [
                *make_text_spans(self.soup, "Line 1"),
                make_semantic_tag(
                    self.soup,
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
                *make_text_spans(self.soup, "Line 2"),
            ],
            ignore_text_span_data=True,
        )


class TestParseUnknownElements(BaseTestCase):

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
            make_semantic_tag(self.soup, other_spec),
            "Unknown str element",
            make_tag(self.soup, "span", contents=["Unknown tag element"]),
        ]

        # Act
        result = parse_unknown_elements(self.context, some_spec, contents)

        # Assert
        assert_elements_equal(
            result,
            [
                make_semantic_tag(
                    self.soup,
                    ErrorSpec,
                    contents=[
                        make_semantic_tag(self.soup, other_spec),
                    ],
                    data=ErrorSpec.data_model(error_codes=[ErrorCodes.unknown_content]),
                ),
                make_semantic_tag(
                    self.soup,
                    ErrorSpec,
                    contents=["Unknown str element"],
                    data=ErrorSpec.data_model(error_codes=[ErrorCodes.unknown_content]),
                ),
                make_semantic_tag(
                    self.soup,
                    ErrorSpec,
                    contents=[
                        make_tag(self.soup, "span", contents=["Unknown tag element"]),
                    ],
                    data=ErrorSpec.data_model(error_codes=[ErrorCodes.unknown_content]),
                ),
            ],
            ignore_text_span_data=True,
        )
