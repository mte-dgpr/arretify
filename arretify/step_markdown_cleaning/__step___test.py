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
from dataclasses import replace as dataclass_replace

from arretify.utils.ocr_document import OcrDocument, Page, get_or_load_asset, set_asset
from arretify.utils.testing import create_document_context

from .__step__ import step_markdown_cleaning


class TestStepMarkdownCleaning(unittest.TestCase):
    def test_step_markdown_cleaning_basic(self):
        # Arrange
        page1 = Page(index=1)
        set_asset(page1, "main.md", "# Article 1  \n\nSome text with extra  spaces.\n\n")

        page2 = Page(index=2)
        set_asset(page2, "main.md", "## Article 2\n\nMore content here  .\n")

        ocr_document = OcrDocument(pages=[page1, page2])

        document_context = dataclass_replace(
            create_document_context(),
            ocr_document=ocr_document,
        )
        content_1_before = get_or_load_asset(page1, "main.md")
        content_2_before = get_or_load_asset(page2, "main.md")

        # Act
        result = step_markdown_cleaning(document_context)

        # Assert
        assert result.ocr_document is not None
        assert len(result.ocr_document.pages) == 2

        # For both pages, test that content was modified, but still contains relevant text.
        content_1_after = result.ocr_document.pages[0].assets["main.md"]
        assert len(content_1_before) > 0
        assert content_1_before != content_1_after
        assert "Article 1" in content_1_before

        content_2_after = result.ocr_document.pages[1].assets["main.md"]
        assert len(content_2_before) > 0
        assert content_2_before != content_2_after
        assert "Article 2" in content_2_before
