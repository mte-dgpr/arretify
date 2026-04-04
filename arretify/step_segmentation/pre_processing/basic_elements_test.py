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
from arretify.semantic_tag_specs import (
    PageFooterSpec,
    PageHeaderSpec,
    PageSeparatorData,
    PageSeparatorSpec,
)
from arretify.step_segmentation.semantic_tag_specs import (
    TextSpanSegmentationData,
    TextSpanSegmentationSpec,
)
from arretify.step_segmentation.testing import (
    BaseTestCaseSegmentation,
    assert_segmentation_element_lists_equal,
)
from arretify.utils.html import is_tag
from arretify.utils.html_create import wrap_in_tag
from arretify.utils.ocr_document import Page, create_asset

from .basic_elements import (
    load_tag_from_markdown_link,
    parse_basic_elements,
    render_frame_misdetected_as_table,
    render_image_and_embed_base64,
)


class TestParseBasicElements(BaseTestCaseSegmentation):

    def test_parse_basic_elements(self):
        # Arrange - page with header, text lines, an embedded image, and footer
        page = Page(index=2)
        create_asset(page, "header.md", "Header content")
        create_asset(
            page, "main.md", "Line 1\n![Photo](image_1.b64)\n[See table](table_1.html)\nLine 2"
        )
        create_asset(page, "image_1.b64", "data:image/png;base64,ABC123")
        create_asset(page, "table_1.html", "<table><tr><td>A</td><td>B</td></tr></table>")
        create_asset(page, "footer.md", "Footer content")

        # Act
        result = parse_basic_elements(self.context, page)

        # Assert
        assert_segmentation_element_lists_equal(
            result,
            [
                self.make_semantic_tag(PageSeparatorSpec, data=PageSeparatorData(page_index=1)),
                self.make_semantic_tag(
                    PageHeaderSpec,
                    contents=wrap_in_tag(self.soup, "div", ["Header content"]),
                ),
                self.make_semantic_tag(
                    TextSpanSegmentationSpec,
                    contents=["Line 1"],
                    data=TextSpanSegmentationData(start=[2, 0, 0], end=[2, 0, 5]),
                ),
                self.make_tag(
                    "img",
                    attrs=dict(alt="Photo", src="data:image/png;base64,ABC123"),
                ),
                self.make_tag(
                    "table",
                    contents=[
                        self.make_tag(
                            "tr",
                            contents=[
                                self.make_tag("td", contents=["A"]),
                                self.make_tag("td", contents=["B"]),
                            ],
                        )
                    ],
                ),
                self.make_semantic_tag(
                    TextSpanSegmentationSpec,
                    contents=["Line 2"],
                    data=TextSpanSegmentationData(start=[2, 3, 0], end=[2, 3, 5]),
                ),
                self.make_semantic_tag(
                    PageFooterSpec,
                    contents=wrap_in_tag(self.soup, "div", ["Footer content"]),
                ),
            ],
        )

    def test_frame_misdetected_as_table(self):
        # Arrange
        page = Page(index=2)
        create_asset(page, "main.md", "[Table](table.html)")
        create_asset(page, "table.html", "<table><tr><td>Line1<br/>Line2</td></tr></table>")

        # Act
        result = parse_basic_elements(self.context, page)

        # Assert
        assert_segmentation_element_lists_equal(
            result,
            [
                self.make_semantic_tag(PageSeparatorSpec, data=PageSeparatorData(page_index=1)),
                self.make_semantic_tag(
                    TextSpanSegmentationSpec,
                    contents=["Line1"],
                    data=TextSpanSegmentationData(start=[2, 0, 0], end=[2, 0, 4]),
                ),
                self.make_semantic_tag(
                    TextSpanSegmentationSpec,
                    contents=["Line2"],
                    data=TextSpanSegmentationData(start=[2, 0, 0], end=[2, 0, 4]),
                ),
            ],
        )

    def test_header_contains_title(self):
        # Arrange
        page = Page(index=1)
        create_asset(page, "header.md", "Article 1 - Bla\nBlo")
        create_asset(page, "main.md", "Some content")

        # Act
        result = parse_basic_elements(self.context, page)

        # Assert
        assert_segmentation_element_lists_equal(
            result,
            [
                self.make_semantic_tag(PageSeparatorSpec, data=PageSeparatorData(page_index=0)),
                self.make_semantic_tag(
                    TextSpanSegmentationSpec,
                    contents=["Article 1 - Bla"],
                    data=TextSpanSegmentationData(start=[1, 0, 0], end=[1, 0, 14]),
                ),
                self.make_semantic_tag(
                    TextSpanSegmentationSpec,
                    contents=["Blo"],
                    data=TextSpanSegmentationData(start=[1, 0, 0], end=[1, 0, 2]),
                ),
                self.make_semantic_tag(
                    TextSpanSegmentationSpec,
                    contents=["Some content"],
                    data=TextSpanSegmentationData(start=[1, 0, 0], end=[1, 0, 11]),
                ),
            ],
        )

    def test_header_contains_toc_title(self):
        # Arrange
        page = Page(index=1)
        create_asset(page, "header.md", "table des matieres")
        create_asset(page, "main.md", "Some content")

        # Act
        result = parse_basic_elements(self.context, page)

        # Assert
        assert_segmentation_element_lists_equal(
            result,
            [
                self.make_semantic_tag(PageSeparatorSpec, data=PageSeparatorData(page_index=0)),
                self.make_semantic_tag(
                    TextSpanSegmentationSpec,
                    contents=["table des matieres"],
                    data=TextSpanSegmentationData(start=[1, 0, 0], end=[1, 0, 17]),
                ),
                self.make_semantic_tag(
                    TextSpanSegmentationSpec,
                    contents=["Some content"],
                    data=TextSpanSegmentationData(start=[1, 0, 0], end=[1, 0, 11]),
                ),
            ],
        )


class TestRenderImageAndEmbedBase64(BaseTestCaseSegmentation):

    def test_embeds_local_b64_asset(self):
        # Arrange
        page = Page(index=1)
        create_asset(page, "photo.b64", "data:image/jpeg;base64,XYZ789")

        # Act
        result = render_image_and_embed_base64(page, "![Alt](photo.b64)")

        # Assert
        assert result == self.make_tag(
            "img", attrs=dict(alt="Alt", src="data:image/jpeg;base64,XYZ789")
        )

    def test_skips_external_url(self):
        # Arrange
        page = Page(index=1)

        # Act
        result = render_image_and_embed_base64(page, "![Alt](https://example.com/img.png)")

        # Assert
        assert result == self.make_tag(
            "img", attrs=dict(alt="Alt", src="https://example.com/img.png")
        )

    def test_skips_already_embedded_data_url(self):
        # Arrange
        page = Page(index=1)
        data_url = "data:image/png;base64,ALREADY"

        # Act
        result = render_image_and_embed_base64(page, f"![Alt]({data_url})")

        # Assert
        assert result == self.make_tag("img", attrs=dict(alt="Alt", src=data_url))


class TestLoadTagFromMarkdownLink(BaseTestCaseSegmentation):
    def test_loads_local_html_table_and_non_table(self):
        # Arrange
        page = Page(index=1)
        create_asset(page, "table.html", "<table><tr><td>A</td><td>B</td></tr></table>")
        create_asset(page, "para.html", "<p>Some paragraph</p>")
        # Act
        tag = load_tag_from_markdown_link(page, "[See table](table.html)")
        tag2 = load_tag_from_markdown_link(page, "[Para](para.html)")
        # Assert
        assert is_tag(tag, tag_name_in=["table"])
        assert is_tag(tag2, tag_name_in=["p"])

    def test_returns_none_for_external_url(self):
        # Arrange
        page = Page(index=1)
        # Act
        tag = load_tag_from_markdown_link(page, "[Link](https://example.com/table.html)")
        # Assert
        assert tag is None

    def test_returns_none_for_non_html_file(self):
        # Arrange
        page = Page(index=1)
        create_asset(page, "doc.pdf", "some content")
        # Act
        tag = load_tag_from_markdown_link(page, "[Doc](doc.pdf)")
        # Assert
        assert tag is None

    def test_returns_none_when_html_has_multiple_root_elements(self):
        # Arrange
        page = Page(index=1)
        create_asset(page, "multi.html", "<p>One</p><p>Two</p>")
        # Act
        tag = load_tag_from_markdown_link(page, "[Multi](multi.html)")
        # Assert
        assert tag is None


class TestRenderFrameMisdetectedAsTable(BaseTestCaseSegmentation):
    def test_extracts_lines(self):
        # Arrange
        page = Page(index=3)
        frame_tag = self.make_tag(
            "table",
            contents=[
                self.make_tag(
                    "tr",
                    contents=[
                        self.make_tag(
                            "td",
                            contents=[
                                "line1",
                                self.make_tag("br"),
                                "line2",
                                self.make_tag("br"),
                            ],
                        ),
                    ],
                )
            ],
        )
        # Act
        result = list(render_frame_misdetected_as_table(self.context, page, 2, frame_tag))
        # Assert
        assert_segmentation_element_lists_equal(
            result,
            [
                self.make_semantic_tag(
                    TextSpanSegmentationSpec,
                    contents=["line1"],
                    data=TextSpanSegmentationData(start=[3, 2, 0], end=[3, 2, 4]),
                ),
                self.make_semantic_tag(
                    TextSpanSegmentationSpec,
                    contents=["line2"],
                    data=TextSpanSegmentationData(start=[3, 2, 0], end=[3, 2, 4]),
                ),
            ],
        )

    def test_with_inline_tags_inside_table(self):
        # Arrange
        page = Page(index=3)
        frame_tag = self.make_tag(
            "table",
            contents=[
                self.make_tag(
                    "tr",
                    contents=[
                        self.make_tag(
                            "td",
                            contents=[
                                "line1 ",
                                self.make_tag("b", contents=["bold"]),
                                self.make_tag("br"),
                                "line2",
                            ],
                        ),
                    ],
                )
            ],
        )

        # Act
        result = list(render_frame_misdetected_as_table(self.context, page, 2, frame_tag))

        # Assert
        assert_segmentation_element_lists_equal(
            result,
            [
                self.make_semantic_tag(
                    TextSpanSegmentationSpec,
                    contents=[
                        "line1 ",
                        self.make_tag("b", contents=["bold"]),
                    ],
                    data=TextSpanSegmentationData(start=[3, 2, 0], end=[3, 2, 9]),
                ),
                self.make_semantic_tag(
                    TextSpanSegmentationSpec,
                    contents=["line2"],
                    data=TextSpanSegmentationData(start=[3, 2, 0], end=[3, 2, 4]),
                ),
            ],
        )
