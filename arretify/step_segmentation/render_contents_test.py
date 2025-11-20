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
from arretify.step_segmentation.core_test import BaseTestCase
from arretify.step_segmentation.render_contents import (
    _list_indentation,
    render_alinea,
    render_blockquote,
    render_inline_quotes,
    render_list,
    render_section,
    render_section_title,
    render_table,
    render_table_description,
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
    TableSegmentationSpec,
    TextSpanSegmentationData,
    TextSpanSegmentationSpec,
    VisaSegmentationSpec,
)
from arretify.step_segmentation.testing import make_text_spans
from arretify.utils.html_create import make_semantic_tag
from arretify.utils.testing import assert_html_list_equal, normalized_html_str


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


class TestRenderInlineQuotes(BaseTestCase):

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
        tag = make_semantic_tag(
            self.soup,
            TableSegmentationSpec,
            contents=[
                *make_text_spans(self.soup, "| Column 1 | Column 2 |", "|----------|----------|"),
                make_semantic_tag(
                    self.soup, PageSeparatorSpec, data=PageSeparatorData(page_index=1)
                ),
                *make_text_spans(
                    self.soup,
                    "| Row 1    | Data 1   |",
                ),
                make_semantic_tag(
                    self.soup, PageSeparatorSpec, data=PageSeparatorData(page_index=2)
                ),
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
                        <th>Column 2<a data-spec="page_separator" data-page_index="1"></a></th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>Row 1</td>
                        <td>Data 1<a data-spec="page_separator" data-page_index="2"></a></td>
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
        tag = make_semantic_tag(
            self.soup,
            TableDescriptionSegmentationSpec,
            contents=[
                *make_text_spans(self.soup, "This is a description of the table."),
                make_semantic_tag(
                    self.soup, PageSeparatorSpec, data=PageSeparatorData(page_index=1)
                ),
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
                '<a data-page_index="1" data-spec="page_separator"></a>',
                "<br/>",
                "This is another part of the description.",
            ],
        )


class TestRenderList(BaseTestCase):

    def test_render_list_with_page_separator(self):
        # Arrange
        tag = make_semantic_tag(
            self.soup,
            ListSegmentationSpec,
            contents=[
                *make_text_spans(self.soup, "- Item 1"),
                make_semantic_tag(
                    self.soup, PageSeparatorSpec, data=PageSeparatorData(page_index=1)
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
                <li>- Item 1<a data-spec="page_separator" data-page_index="1"></a></li>
                <li>- Item 2</li>
            </ul>
            """
        )

    def test_render_nested_list(self):
        # Arrange
        tag = make_semantic_tag(
            self.soup,
            ListSegmentationSpec,
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
        tag = make_semantic_tag(
            self.soup,
            ListSegmentationSpec,
            contents=[
                make_semantic_tag(
                    self.soup,
                    TextSpanSegmentationSpec,
                    contents=["- Item 1", " This is a continuation of the previous sentence."],
                    data=TextSpanSegmentationData(start=[0, 0, 0], end=[0, 1, 48]),
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

    def test_render_list_numbers(self):
        # Arrange
        tag = make_semantic_tag(
            self.soup,
            ListSegmentationSpec,
            contents=[
                *make_text_spans(
                    self.soup,
                    " - First item",
                    "- Second item",
                ),
            ],
        )

        # Act
        list_tag = render_list(self.context, tag)

        # Assert
        assert normalized_html_str(str(list_tag)) == normalized_html_str(
            """
            <ul>
                <li>- First item</li>
                <li>- Second item</li>
            </ul>
            """
        )


class TestRenderBlockQuote(BaseTestCase):

    def test_render_blockquote(self):
        # Arrange
        tag = make_semantic_tag(
            self.soup,
            BlockquoteSegmentationSpec,
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


class TestRenderAlinea(BaseTestCase):

    def test_simple(self):
        # Arrange
        alinea = make_semantic_tag(
            self.soup,
            AlineaSegmentationSpec,
            contents=make_text_spans(self.soup, "This is an alinea."),
            data=AlineaData(number="1"),
        )

        # Act
        result = render_alinea(self.context, alinea)

        # Assert
        assert normalized_html_str(str(result)) == normalized_html_str(
            """
            <div data-spec="alinea" data-number="1">
                This is an alinea.
            </div>
            """
        )


class TestRenderSection(BaseTestCase):

    def test_simple(self):
        # Arrange
        tag = make_semantic_tag(
            self.soup,
            SectionSegmentationSpec,
            contents=[
                make_semantic_tag(
                    self.soup,
                    SectionTitleSegmentationSpec,
                    contents=make_text_spans(self.soup, "Article 1 : Disposition"),
                    data=SectionTitleSegmentationData(
                        level=0,
                        number="1",
                        title="Disposition",
                        type="article",
                    ),
                ),
                make_semantic_tag(
                    self.soup,
                    AlineaSegmentationSpec,
                    contents=make_text_spans(self.soup, "Bla bla bla ..."),
                    data=AlineaData(number="1"),
                ),
            ],
        )

        # Act
        result = render_section(self.context, tag)

        # Assert
        assert normalized_html_str(str(result)) == normalized_html_str(
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
        )


class TestRenderSectionTitle(BaseTestCase):

    def test_simple(self):
        # Arrange
        section_title = make_semantic_tag(
            self.soup,
            SectionTitleSegmentationSpec,
            contents=make_text_spans(self.soup, "Titre I - Introduction"),
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
        assert normalized_html_str(str(result)) == normalized_html_str(
            """
            <h2 data-level="0" data-spec="section_title">
                Titre I - Introduction
            </h2>
            """
        )


class TestRenderVisaMotif(BaseTestCase):

    def test_render_simple(self):
        # Arrange
        tag = make_semantic_tag(
            self.soup,
            VisaSegmentationSpec,
            contents=make_text_spans(
                self.soup,
                "Vu le code de l'environnement, et notamment ses titres "
                "1er et 4 des parties réglementaires et législatives du livre V ;",
            ),
        )

        # Act
        rendered = render_visa_motif(self.context, tag)

        # Assert
        assert normalized_html_str(str(rendered)) == normalized_html_str(
            """
            <div data-spec="visa">
                Vu le code de l'environnement, et notamment ses titres
                1er et 4 des parties réglementaires et législatives du livre V ;
            </div>
            """
        )
