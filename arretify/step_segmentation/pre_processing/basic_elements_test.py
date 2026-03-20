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
from arretify.utils.html_create import wrap_in_tag
from arretify.utils.ocr_document import Page, create_asset

from .basic_elements import (
    parse_basic_elements,
    render_image_and_embed_base64,
    render_link_and_embed_content,
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


class TestRenderLinkAndEmbedContent(BaseTestCaseSegmentation):

    def test_embeds_local_html_table(self):
        # Arrange
        page = Page(index=1)
        create_asset(page, "table.html", "<table><tr><td>A</td><td>B</td></tr></table>")

        # Act
        result = render_link_and_embed_content(self.context, page, 0, "[See table](table.html)")

        # Assert
        assert len(result) == 1
        assert result[0].name == "table"

    def test_deals_with_frame_misdetected_as_table(self):
        # Arrange
        page = Page(index=2)
        create_asset(
            page,
            "frame.html",
            "<table><tr><td>Line 1<br/>Line 2<br/>Line 3</td></tr></table>",
        )

        # Act
        result = render_link_and_embed_content(self.context, page, 5, "[Frame](frame.html)")

        # Assert - frame content is extracted as separate text segmentation tags
        assert_segmentation_element_lists_equal(
            result,
            [
                self.make_semantic_tag(
                    TextSpanSegmentationSpec,
                    contents=["Line 1"],
                    data=TextSpanSegmentationData(start=[2, 5, 0], end=[2, 5, 5]),
                ),
                self.make_semantic_tag(
                    TextSpanSegmentationSpec,
                    contents=["Line 2"],
                    data=TextSpanSegmentationData(start=[2, 5, 0], end=[2, 5, 5]),
                ),
                self.make_semantic_tag(
                    TextSpanSegmentationSpec,
                    contents=["Line 3"],
                    data=TextSpanSegmentationData(start=[2, 5, 0], end=[2, 5, 5]),
                ),
            ],
        )

    def test_skips_external_url(self):
        # Arrange
        page = Page(index=1)

        # Act
        result = render_link_and_embed_content(
            self.context, page, 0, "[Link](https://example.com/table.html)"
        )

        # Assert
        assert len(result) == 1
        assert result[0].name == "a"
        assert result[0].get("href") == "https://example.com/table.html"

    def test_skips_non_html_file(self):
        # Arrange
        page = Page(index=1)
        create_asset(page, "doc.pdf", "some content")

        # Act
        result = render_link_and_embed_content(self.context, page, 0, "[Doc](doc.pdf)")

        # Assert
        assert len(result) == 1
        assert result[0].name == "a"

    def test_returns_link_when_html_has_multiple_root_elements(self):
        # Arrange
        page = Page(index=1)
        create_asset(page, "multi.html", "<p>One</p><p>Two</p>")

        # Act
        result = render_link_and_embed_content(self.context, page, 0, "[Multi](multi.html)")

        # Assert
        assert len(result) == 1
        assert result[0].name == "a"

    def test_returns_link_when_html_root_is_not_table(self):
        # Arrange
        page = Page(index=1)
        create_asset(page, "para.html", "<p>Some paragraph</p>")

        # Act
        result = render_link_and_embed_content(self.context, page, 0, "[Para](para.html)")

        # Assert
        assert len(result) == 1
        assert result[0].name == "a"
