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

from arretify.utils.pages import (
    Page,
    create_asset,
    get_or_load_asset,
    load_page,
    save_page,
    set_asset,
)


class TestPage(unittest.TestCase):

    def test_create_asset(self):
        # Arrange
        page = Page(index=1)

        # Act
        create_asset(page, "main.md", "Main content")
        create_asset(page, "header.md", "Header content")
        create_asset(page, "footer.md")

        # Assert
        assert page.assets["main.md"] == "Main content"
        assert page.assets["header.md"] == "Header content"
        assert page.assets["footer.md"] is None

    def test_set_asset(self):
        # Arrange
        page = Page(index=1)
        create_asset(page, "main.md", None)

        # Act
        set_asset(page, "main.md", "New content")

        # Assert
        assert page.assets["main.md"] == "New content"

    def test_get_or_load_asset_in_memory(self):
        # Arrange
        page = Page(index=1)
        create_asset(page, "main.md", "Main content")

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
            create_asset(page, "main.md", None)

            # Act - lazy load
            content = get_or_load_asset(page, "main.md")

            # Assert
            assert content == "Content from disk"
            assert page.assets["main.md"] == "Content from disk"

    def test_get_or_load_asset_raises_when_no_dir_path(self):
        """Test that loading without dir_path raises ValueError."""
        # Arrange
        page = Page(index=1)
        create_asset(page, "main.md", None)

        # Act & Assert
        with self.assertRaises(ValueError) as context:
            get_or_load_asset(page, "main.md")
        assert "without dir_path" in str(context.exception)

    def test_get_or_load_asset_raises_when_file_not_found(self):
        """Test that loading non-existent file raises ValueError."""
        # Arrange
        with tempfile.TemporaryDirectory() as tmpdir:
            page_dir = Path(tmpdir) / "1"
            page_dir.mkdir()

            page = Page(index=1, dir_path=page_dir)
            create_asset(page, "main.md", None)

            # Act & Assert
            with self.assertRaises(ValueError) as context:
                get_or_load_asset(page, "main.md")
            assert "not found" in str(context.exception)

    def test_serialization_excludes_content(self):
        """Test that model_dump_json only includes asset names, not content."""
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
            "main.md": None,
            "header.md": None,
        }


class TestPageSaveLoad(unittest.TestCase):

    def test_save_and_load_page(self):
        """Test complete save/load roundtrip."""
        # Arrange
        with tempfile.TemporaryDirectory() as tmpdir:
            page_dir = Path(tmpdir) / "1"

            page = Page(index=1, dir_path=page_dir)
            create_asset(page, "main.md", "Main content of the page")
            create_asset(page, "header.md", "Header content")
            create_asset(page, "footer.md", "Footer content")
            create_asset(page, "image1.b64", "Image description")
            create_asset(page, "table1.html", "<table>Table content</table>")

            # Act - Save
            save_page(page)

            # Assert - Files created
            assert (page_dir / "main.md").exists()
            assert (page_dir / "header.md").exists()
            assert (page_dir / "footer.md").exists()
            assert (page_dir / "image1.b64").exists()
            assert (page_dir / "table1.html").exists()
            assert (page_dir / "page.json").exists()

            # Verify file content
            assert (page_dir / "main.md").read_text(encoding="utf-8") == "Main content of the page"
            assert (page_dir / "header.md").read_text(encoding="utf-8") == "Header content"

            # Act - Load
            loaded_page = load_page(page_dir)

            # Assert - Metadata loaded
            assert loaded_page.index == 1
            assert loaded_page.dir_path == page_dir
            assert set(loaded_page.assets.keys()) == {
                "main.md",
                "header.md",
                "footer.md",
                "image1.b64",
                "table1.html",
            }

            # Assert - Content lazy loaded
            assert get_or_load_asset(loaded_page, "main.md") == "Main content of the page"
            assert get_or_load_asset(loaded_page, "header.md") == "Header content"
            assert get_or_load_asset(loaded_page, "footer.md") == "Footer content"
            assert get_or_load_asset(loaded_page, "image1.b64") == "Image description"
            assert get_or_load_asset(loaded_page, "table1.html") == "<table>Table content</table>"
