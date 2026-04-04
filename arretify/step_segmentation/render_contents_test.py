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
from arretify.semantic_tag_specs import AlineaData, PageSeparatorData, PageSeparatorSpec
from arretify.step_segmentation.render_contents import (
    _list_indentation,
    render_alinea,
    render_blockquote,
    render_inline_quotes,
    render_list,
    render_section,
    render_section_title,
    render_table_description,
    render_text_span,
    render_visa_motif,
)
from arretify.step_segmentation.semantic_tag_specs import (
    AlineaSegmentationSpec,
    BlockquoteSegmentationSpec,
    ListSegmentationSpec,
    SectionSegmentationSpec,
    SectionTitleSegmentationData,
    SectionTitleSegmentationSpec,
    TableDescriptionSegmentationSpec,
    TextSpanSegmentationData,
    TextSpanSegmentationSpec,
    VisaSegmentationSpec,
)
from arretify.step_segmentation.testing import BaseTestCaseSegmentation
from arretify.utils.testing import assert_element_lists_equal, assert_elements_equal, parse_element


class TestListIndentation(BaseTestCaseSegmentation):

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


class TestRenderInlineQuotes(BaseTestCaseSegmentation):

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


class TestRenderTableDescription(BaseTestCaseSegmentation):

    def test_render_table_description_with_page_separators(self):
        # Arrange
        tag = self.make_semantic_tag(
            TableDescriptionSegmentationSpec,
            contents=[
                *self.make_text_spans("This is a description of the table."),
                self.make_semantic_tag(PageSeparatorSpec, data=PageSeparatorData(page_index=1)),
                *self.make_text_spans("This is another part of the description."),
            ],
        )

        # Act
        table_description_elements = list(render_table_description(self.context, tag))

        # Assert
        assert_element_lists_equal(
            table_description_elements,
            [
                parse_element("<br>"),
                "This is a description of the table.",
                parse_element('<a data-page_index="1" data-spec="page_separator"></a>'),
                parse_element("<br>"),
                "This is another part of the description.",
            ],
        )


class TestRenderList(BaseTestCaseSegmentation):

    def test_render_list_with_page_separator(self):
        # Arrange
        tag = self.make_semantic_tag(
            ListSegmentationSpec,
            contents=[
                *self.make_text_spans("- Item 1"),
                self.make_semantic_tag(PageSeparatorSpec, data=PageSeparatorData(page_index=1)),
                *self.make_text_spans("- Item 2"),
            ],
        )

        # Act
        list_tag = render_list(self.context, tag)

        # Assert
        assert_elements_equal(
            list_tag,
            parse_element(
                """
            <ul>
                <li>- Item 1<a data-spec="page_separator" data-page_index="1"></a></li>
                <li>- Item 2</li>
            </ul>
            """
            ),
        )

    def test_render_nested_list(self):
        # Arrange
        tag = self.make_semantic_tag(
            ListSegmentationSpec,
            contents=[
                *self.make_text_spans("- Item 1", "  - Subitem 1.1", "  - Subitem 1.2", "- Item 2"),
            ],
        )

        # Act
        list_tag = render_list(self.context, tag)

        # Assert
        assert_elements_equal(
            list_tag,
            parse_element(
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
            ),
        )

    def test_render_list_text_span(self):
        # Arrange
        tag = self.make_semantic_tag(
            ListSegmentationSpec,
            contents=[
                self.make_semantic_tag(
                    TextSpanSegmentationSpec,
                    contents=["- Item 1", " This is a continuation of the previous sentence."],
                    data=TextSpanSegmentationData(start=[0, 0, 0], end=[0, 1, 48]),
                ),
                *self.make_text_spans("- Item 2"),
            ],
        )

        # Act
        list_tag = render_list(self.context, tag)

        # Assert
        assert_elements_equal(
            list_tag,
            parse_element(
                """
            <ul>
                <li>- Item 1 This is a continuation of the previous sentence.</li>
                <li>- Item 2</li>
            </ul>
            """
            ),
        )

    def test_render_list_numbers(self):
        # Arrange
        tag = self.make_semantic_tag(
            ListSegmentationSpec,
            contents=[
                *self.make_text_spans(
                    " - First item",
                    "- Second item",
                ),
            ],
        )

        # Act
        list_tag = render_list(self.context, tag)

        # Assert
        assert_elements_equal(
            list_tag,
            parse_element(
                """
            <ul>
                <li>- First item</li>
                <li>- Second item</li>
            </ul>
            """
            ),
        )


class TestRenderBlockQuote(BaseTestCaseSegmentation):

    def test_render_blockquote(self):
        # Arrange
        tag = self.make_semantic_tag(
            BlockquoteSegmentationSpec,
            contents=self.make_text_spans("This is", "a blockquote"),
        )

        # Act
        blockquote_tag = render_blockquote(self.context, tag)

        # Assert
        assert_elements_equal(
            blockquote_tag,
            parse_element(
                """
            <blockquote>
                <p>This is</p>
                <p>a blockquote</p>
            </blockquote>
            """
            ),
        )


class TestRenderAlinea(BaseTestCaseSegmentation):

    def test_simple(self):
        # Arrange
        alinea = self.make_semantic_tag(
            AlineaSegmentationSpec,
            contents=self.make_text_spans("This is an alinea."),
            data=AlineaData(number="1"),
        )

        # Act
        result = render_alinea(self.context, alinea)

        # Assert
        assert_elements_equal(
            result,
            parse_element(
                """
            <div data-spec="alinea" data-number="1">
                This is an alinea.
            </div>
            """
            ),
        )


class TestRenderSection(BaseTestCaseSegmentation):

    def test_simple(self):
        # Arrange
        tag = self.make_semantic_tag(
            SectionSegmentationSpec,
            contents=[
                self.make_semantic_tag(
                    SectionTitleSegmentationSpec,
                    contents=self.make_text_spans("Article 1 : Disposition"),
                    data=SectionTitleSegmentationData(
                        level=0,
                        number="1",
                        title="Disposition",
                        type="article",
                    ),
                ),
                self.make_semantic_tag(
                    AlineaSegmentationSpec,
                    contents=self.make_text_spans("Bla bla bla ..."),
                    data=AlineaData(number="1"),
                ),
            ],
        )

        # Act
        result = render_section(self.context, tag)

        # Assert
        assert_elements_equal(
            result,
            parse_element(
                """
            <section data-spec="section" data-number="1" data-title="Disposition" data-type="article">
                <h2 data-level="0" data-spec="section_title">
                    Article 1 : Disposition
                </h2>
                <div data-spec="alinea" data-number="1">
                    Bla bla bla ...
                </div>
            </section>
            """  # noqa: E501
            ),
        )


class TestRenderSectionTitle(BaseTestCaseSegmentation):

    def test_simple(self):
        # Arrange
        section_title = self.make_semantic_tag(
            SectionTitleSegmentationSpec,
            contents=self.make_text_spans("Titre I - Introduction"),
            data=SectionTitleSegmentationData(
                level=0,
                number="I",
                title="Introduction",
                type="titre",
            ),
        )

        # Act
        result = render_section_title(self.context, section_title)

        # Assert
        assert_elements_equal(
            result,
            parse_element(
                """
            <h2 data-level="0" data-spec="section_title">
                Titre I - Introduction
            </h2>
            """
            ),
        )


class TestRenderVisaMotif(BaseTestCaseSegmentation):

    def test_render_simple(self):
        # Arrange
        tag = self.make_semantic_tag(
            VisaSegmentationSpec,
            contents=self.make_text_spans(
                "Vu le code de l'environnement, et notamment ses titres "
                "1er et 4 des parties réglementaires et législatives du livre V ;",
            ),
        )

        # Act
        rendered = render_visa_motif(self.context, tag)

        # Assert
        assert_elements_equal(
            rendered,
            parse_element(
                """
            <div data-spec="visa">
                Vu le code de l'environnement, et notamment ses titres 1er et 4 des parties réglementaires et législatives du livre V ;
            </div>
            """  # noqa: E501
            ),
        )


class TestRenderTextSpan(BaseTestCaseSegmentation):

    def test_inline_formatting_tag(self):
        # Arrange
        tag = self.make_semantic_tag(
            TextSpanSegmentationSpec,
            contents=["hello", self.make_tag("em", contents=["bla"])],
            data=TextSpanSegmentationData(start=[0, 0, 0], end=[0, 0, 0]),
        )

        # Act
        rendered = render_text_span(self.context, tag)

        # Assert
        assert_elements_equal(rendered, ["hello", self.make_tag("em", contents=["bla"])])
