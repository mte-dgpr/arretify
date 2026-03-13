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
    Asset,
    OcrDocument,
    Page,
    create_asset,
    get_or_load_asset_content,
    load_ocr_document,
    save_ocr_document,
)


class TestPageModel(unittest.TestCase):

    def test_serialization_excludes_content(self):
        # Arrange
        page = Page(index=1)
        create_asset(page, "main.md", "Secret content")
        create_asset(page, "header.md", "Header content")

        # Act
        json_str = page.model_dump_json()

        # Assert
        data = json.loads(json_str)
        assert data["index"] == 1
        assert data["assets"] == {
            "main.md": {"name": "main.md"},
            "header.md": {"name": "header.md"},
        }


class TestSaveLoadDocument(unittest.TestCase):

    def test_save_and_load_document(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ocr_document_dir = Path(tmpdir) / "doc1"
            page1 = Page(index=1)
            page2 = Page(index=2)

            create_asset(page1, "main.md", "Main content of page 1")
            create_asset(page1, "header.md", "Header 1")
            create_asset(page2, "main.md", "Main content of page 2")
            create_asset(page2, "header.md", "Header 2")

            document = OcrDocument(ocr_model="mistral-ocr-2512", pages=[page1, page2])

            # Act - Save document
            save_ocr_document(document, ocr_document_dir)

            # Assert - Files created with correct content
            assert (ocr_document_dir / "1" / "main.md").read_text(
                encoding="utf-8"
            ) == "Main content of page 1"
            assert (ocr_document_dir / "1" / "header.md").read_text(encoding="utf-8") == "Header 1"
            assert (ocr_document_dir / "2" / "main.md").read_text(
                encoding="utf-8"
            ) == "Main content of page 2"
            assert (ocr_document_dir / "2" / "header.md").read_text(encoding="utf-8") == "Header 2"
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
            assert (
                get_or_load_asset_content(loaded_pages[0].assets["main.md"])
                == "Main content of page 1"
            )
            assert (
                get_or_load_asset_content(loaded_pages[1].assets["main.md"])
                == "Main content of page 2"
            )

    def test_save_document_loads_content_from_existing_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Arrange - Create source file on disk
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            source_file = source_dir / "original.md"
            source_file.write_text("Content from original location", encoding="utf-8")

            # Create page with asset pointing to existing file but asset is not loaded
            page = Page(index=1)
            page.assets["lazy.md"] = Asset(name="lazy.md", path=source_file, content=None)

            document = OcrDocument(pages=[page])

            # Act - Save document (should load content from source_file)
            target_dir = Path(tmpdir) / "target"
            save_ocr_document(document, target_dir)

            # Assert - Content was loaded from original path and saved to new location
            saved_content = (target_dir / "1" / "lazy.md").read_text(encoding="utf-8")
            assert saved_content == "Content from original location"


class TestCreateAsset(unittest.TestCase):

    def test_create_asset(self):
        # Arrange
        page = Page(index=1)

        # Act
        create_asset(page, "main.md", "Main content")
        create_asset(page, "header.md", "Header content")
        create_asset(page, "footer.md", None)

        # Assert
        assert page.assets["main.md"].content == "Main content"
        assert page.assets["header.md"].content == "Header content"
        assert page.assets["footer.md"].content is None


class TestGetOrLoadAssetContent(unittest.TestCase):

    def test_get_or_load_asset_in_memory(self):
        # Arrange
        asset = Asset(name="main.md", content="Main content")

        # Act
        content = get_or_load_asset_content(asset)

        # Assert
        assert content == "Main content"

    def test_get_or_load_asset_lazy_loading(self):
        # Arrange
        with tempfile.TemporaryDirectory() as tmpdir:
            asset_path = Path(tmpdir) / "main.md"
            asset_path.write_text("Content from disk", encoding="utf-8")
            asset = Asset(name="main.md", path=asset_path)

            # Act - lazy load
            content = get_or_load_asset_content(asset)

            # Assert
            assert content == "Content from disk"
            assert asset.content == "Content from disk"

    def test_get_or_load_asset_raises_when_no_asset_path(self):
        # Arrange
        asset = Asset(name="main.md", content=None, path=None)

        # Act & Assert
        with self.assertRaises(ValueError) as context:
            get_or_load_asset_content(asset)
        assert "without asset.path set" in str(context.exception)

    def test_get_or_load_asset_raises_when_file_not_found(self):
        # Arrange
        with tempfile.TemporaryDirectory() as tmpdir:
            asset_path = Path(tmpdir) / "main.md"
            # Create asset pointing to a non-existent file
            asset = Asset(name="main.md", path=asset_path)

            # Act & Assert
            with self.assertRaises(ValueError) as context:
                get_or_load_asset_content(asset)
            assert "not found" in str(context.exception)
