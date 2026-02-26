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
from arretify.utils.ocr_document import Page, set_asset

from .pages_to_single_html import pages_to_single_html


class TestPagesToSingleHtml(BaseTestCaseSegmentation):

    def setUp(self):
        super().setUp()
        self.soup_extend([self.make_tag("body")])

    def test_page_separators_inserted_and_text_spans_created(self):
        # Arrange
        page1 = Page(index=1)
        set_asset(page1, "main.md", "Line 1\nLine 2\nLine 3")
        page2 = Page(index=2)
        set_asset(page2, "main.md", "Line 4\nLine 5")
        page3 = Page(index=3)
        set_asset(page3, "main.md", "Line 6")
        pages = [page1, page2, page3]

        # Act
        result = pages_to_single_html(self.context, pages)

        # Assert
        assert_segmentation_element_lists_equal(
            result,
            [
                self.make_semantic_tag(PageSeparatorSpec, data=PageSeparatorData(page_index=0)),
                self.make_semantic_tag(
                    TextSpanSegmentationSpec,
                    contents=["Line 1"],
                    data=TextSpanSegmentationData(start=[1, 0, 0], end=[1, 0, 5]),
                ),
                self.make_semantic_tag(
                    TextSpanSegmentationSpec,
                    contents=["Line 2"],
                    data=TextSpanSegmentationData(start=[1, 1, 0], end=[1, 1, 5]),
                ),
                self.make_semantic_tag(
                    TextSpanSegmentationSpec,
                    contents=["Line 3"],
                    data=TextSpanSegmentationData(start=[1, 2, 0], end=[1, 2, 5]),
                ),
                self.make_semantic_tag(PageSeparatorSpec, data=PageSeparatorData(page_index=1)),
                self.make_semantic_tag(
                    TextSpanSegmentationSpec,
                    contents=["Line 4"],
                    data=TextSpanSegmentationData(start=[2, 0, 0], end=[2, 0, 5]),
                ),
                self.make_semantic_tag(
                    TextSpanSegmentationSpec,
                    contents=["Line 5"],
                    data=TextSpanSegmentationData(start=[2, 1, 0], end=[2, 1, 5]),
                ),
                self.make_semantic_tag(PageSeparatorSpec, data=PageSeparatorData(page_index=2)),
                self.make_semantic_tag(
                    TextSpanSegmentationSpec,
                    contents=["Line 6"],
                    data=TextSpanSegmentationData(start=[3, 0, 0], end=[3, 0, 5]),
                ),
            ],
        )

    def test_with_header_and_footer(self):
        # Arrange
        page = Page(index=1)
        set_asset(page, "header.md", "Header content")
        set_asset(page, "main.md", "Main line")
        set_asset(page, "footer.md", "Footer content")
        pages = [page]

        # Act
        result = pages_to_single_html(self.context, pages)

        # Assert
        assert_segmentation_element_lists_equal(
            result,
            [
                self.make_semantic_tag(PageSeparatorSpec, data=PageSeparatorData(page_index=0)),
                self.make_semantic_tag(
                    PageHeaderSpec,
                    contents=wrap_in_tag(self.soup, "div", ["Header content"]),
                ),
                self.make_semantic_tag(
                    TextSpanSegmentationSpec,
                    contents=["Main line"],
                    data=TextSpanSegmentationData(start=[1, 0, 0], end=[1, 0, 8]),
                ),
                self.make_semantic_tag(
                    PageFooterSpec,
                    contents=wrap_in_tag(self.soup, "div", ["Footer content"]),
                ),
            ],
        )
