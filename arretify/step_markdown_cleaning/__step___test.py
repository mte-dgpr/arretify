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

from arretify.utils.pages import Page, create_asset, get_or_load_asset
from arretify.utils.testing import create_document_context

from .__step__ import step_markdown_cleaning


class TestStepMarkdownCleaning(unittest.TestCase):
    def test_step_markdown_cleaning_basic(self):
        # Arrange
        page1 = Page(index=1)
        create_asset(page1, "main.md", "# Article 1  \n\nSome text with extra  spaces.\n\n")

        page2 = Page(index=2)
        create_asset(page2, "main.md", "## Article 2\n\nMore content here  .\n")

        pages = [page1, page2]

        document_context = dataclass_replace(
            create_document_context(),
            pages=pages,
        )

        # Act
        result = step_markdown_cleaning(document_context)

        # Assert
        assert result.pages is not None
        assert len(result.pages) == 2

        # For both pages, test that content was modified, but still contains relevant text.
        main_content_1 = get_or_load_asset(result.pages[0], "main.md")
        assert len(main_content_1) > 0
        assert main_content_1 != pages[0].assets["main.md"]
        assert "Article 1" in main_content_1

        main_content_2 = get_or_load_asset(result.pages[1], "main.md")
        assert len(main_content_2) > 0
        assert main_content_2 != pages[1].assets["main.md"]
        assert "Article 2" in main_content_2
