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
import json
import tempfile
import unittest
from pathlib import Path

from arretify.utils.ocr_document import (
    OcrDocument,
    Page,
    get_or_load_asset,
    load_ocr_document,
    save_ocr_document,
    set_asset,
)


class TestOcrDocument(unittest.TestCase):

    def test_set_asset(self):
        # Arrange
        page = Page(index=1)

        # Act
        set_asset(page, "main.md", "Main content")
        set_asset(page, "header.md", "Header content")
        set_asset(page, "footer.md")

        # Assert
        assert page.assets["main.md"] == "Main content"
        assert page.assets["header.md"] == "Header content"
        assert page.assets["footer.md"] is None

    def test_get_or_load_asset_in_memory(self):
        # Arrange
        page = Page(index=1)
        set_asset(page, "main.md", "Main content")

        # Act
        content = get_or_load_asset(page, "main.md")

        # Assert
        assert content == "Main content"

    def test_get_or_load_asset_lazy_loading(self):
        # Arrange
        with tempfile.TemporaryDirectory() as tmpdir:
            page_dir = Path(tmpdir) / "1"
            page_dir.mkdir()

            main_file = page_dir / "main.md"
            main_file.write_text("Content from disk", encoding="utf-8")

            page = Page(index=1, dir_path=page_dir)
            set_asset(page, "main.md", None)

            # Act - lazy load
            content = get_or_load_asset(page, "main.md")

            # Assert
            assert content == "Content from disk"
            assert page.assets["main.md"] == "Content from disk"

    def test_get_or_load_asset_raises_when_no_dir_path(self):
        # Arrange
        page = Page(index=1)
        set_asset(page, "main.md", None)

        # Act & Assert
        with self.assertRaises(ValueError) as context:
            get_or_load_asset(page, "main.md")
        assert "without dir_path" in str(context.exception)

    def test_get_or_load_asset_raises_when_file_not_found(self):
        # Arrange
        with tempfile.TemporaryDirectory() as tmpdir:
            page_dir = Path(tmpdir) / "1"
            page_dir.mkdir()

            page = Page(index=1, dir_path=page_dir)
            set_asset(page, "main.md", None)

            # Act & Assert
            with self.assertRaises(ValueError) as context:
                get_or_load_asset(page, "main.md")
            assert "not found" in str(context.exception)

    def test_serialization_excludes_content(self):
        # Arrange
        page = Page(index=1)
        set_asset(page, "main.md", "Secret content")
        set_asset(page, "header.md", "Header content")

        # Act
        json_str = page.model_dump_json()

        # Assert
        data = json.loads(json_str)
        assert data["index"] == 1
        assert data["assets"] == {
            "main.md": None,
            "header.md": None,
        }

    def test_save_and_load_document(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ocr_document_dir = Path(tmpdir) / "doc1"
            page1 = Page(index=1)
            page2 = Page(index=2)

            set_asset(page1, "main.md", "Main content of page 1")
            set_asset(page1, "header.md", "Header 1")
            set_asset(page2, "main.md", "Main content of page 2")
            set_asset(page2, "header.md", "Header 2")

            document = OcrDocument(ocr_model="mistral-ocr-2512", pages=[page1, page2])

            # Act - Save document
            save_ocr_document(document, ocr_document_dir)

            # Assert - Asset files created
            for idx, content in [(1, "Main content of page 1"), (2, "Main content of page 2")]:
                page_dir = ocr_document_dir / str(idx)
                assert (page_dir / "main.md").exists()
                assert (page_dir / "header.md").exists()
                assert (page_dir / "main.md").read_text(encoding="utf-8").startswith("Main content")

            # Assert - Centralized ocr_document.json exists
            assert (ocr_document_dir / "ocr_document.json").exists()

            # Act - Load document
            loaded_doc = load_ocr_document(ocr_document_dir)
            assert loaded_doc.ocr_model == "mistral-ocr-2512"
            assert len(loaded_doc.pages) == 2
            loaded_pages = sorted(loaded_doc.pages, key=lambda p: p.index)

            # Assert - Metadata loaded
            assert loaded_pages[0].index == 1
            assert loaded_pages[1].index == 2
            assert set(loaded_pages[0].assets.keys()) == {"main.md", "header.md"}
            assert set(loaded_pages[1].assets.keys()) == {"main.md", "header.md"}

            # Assert - Content lazy loaded
            assert get_or_load_asset(loaded_pages[0], "main.md") == "Main content of page 1"
            assert get_or_load_asset(loaded_pages[1], "main.md") == "Main content of page 2"
