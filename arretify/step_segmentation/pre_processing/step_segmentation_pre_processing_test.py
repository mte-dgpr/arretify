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
from dataclasses import replace as dataclass_replace

from arretify.semantic_tag_specs import PageHeaderSpec, PageSeparatorData, PageSeparatorSpec
from arretify.step_segmentation.semantic_tag_specs import (
    TextSpanSegmentationData,
    TextSpanSegmentationSpec,
)
from arretify.step_segmentation.testing import (
    BaseTestCaseSegmentation,
    assert_segmentation_element_lists_equal,
)
from arretify.utils.html_create import wrap_in_tag
from arretify.utils.ocr_document import OcrDocument, Page, set_asset

from .step_segmentation_pre_processing import step_segmentation_pre_processing


class TestStepSegmentationPreProcessing(BaseTestCaseSegmentation):

    def setUp(self):
        super().setUp()
        self.soup_extend([self.make_tag("body")])

    def test_step_segmentation_pre_processing(self):
        # Arrange
        page1 = Page(index=1)
        set_asset(page1, "header.md", "Page 1")
        set_asset(page1, "main.md", "# Article 1  \n\nSome content here.\n\n")

        page2 = Page(index=2)
        set_asset(page2, "main.md", "## Article 2\n\nMore content here.\n")

        pages = [page1, page2]

        ocr_document = OcrDocument(
            pages=pages,
        )

        # Act
        result = step_segmentation_pre_processing(self.context, ocr_document)

        # Assert
        assert_segmentation_element_lists_equal(
            result,
            [
                self.make_semantic_tag(PageSeparatorSpec, data=PageSeparatorData(page_index=0)),
                self.make_semantic_tag(
                    PageHeaderSpec,
                    contents=wrap_in_tag(self.soup, "div", ["Page 1"]),
                ),
                self.make_semantic_tag(
                    TextSpanSegmentationSpec,
                    contents=["Article 1  "],
                    data=TextSpanSegmentationData(start=[1, 0, 0], end=[1, 0, 10]),
                ),
                self.make_semantic_tag(
                    TextSpanSegmentationSpec,
                    contents=["Some content here."],
                    data=TextSpanSegmentationData(start=[1, 1, 0], end=[1, 1, 17]),
                ),
                self.make_semantic_tag(PageSeparatorSpec, data=PageSeparatorData(page_index=1)),
                self.make_semantic_tag(
                    TextSpanSegmentationSpec,
                    contents=["Article 2"],
                    data=TextSpanSegmentationData(start=[2, 0, 0], end=[2, 0, 8]),
                ),
                self.make_semantic_tag(
                    TextSpanSegmentationSpec,
                    contents=["More content here."],
                    data=TextSpanSegmentationData(start=[2, 1, 0], end=[2, 1, 17]),
                ),
            ],
        )
