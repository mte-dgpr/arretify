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
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from arretify.pipeline import load_ocr_pages, load_pdf_file, load_standalone_ocr_file
from arretify.settings import Settings
from arretify.types import SessionContext
from arretify.utils.pages import Page, create_asset, get_or_load_asset, save_page


class TestFileLoadingFunctions(unittest.TestCase):

    def setUp(self):
        self.session_context = SessionContext(
            settings=Settings(),
        )

    def test_load_pdf_file(self):
        # Arrange
        input_path = mock.Mock(spec=Path)
        input_path.is_file.return_value = True
        input_path.read_bytes.return_value = b"dummy pdf content"
        input_path.suffix = ".pdf"

        # Act
        result = load_pdf_file(self.session_context, input_path)

        # Assert
        assert result is not None
        assert result.input_path == input_path
        assert result.pdf == b"dummy pdf content"
        assert result.protected_soup is not None

    def test_load_standalone_ocr_file(self):
        # Arrange
        input_path = mock.Mock(spec=Path)
        input_path.is_file.return_value = True
        input_path.suffix = ".md"
        m = mock.mock_open(read_data="line1\nline2")
        with mock.patch("builtins.open", m):
            # Act
            result = load_standalone_ocr_file(self.session_context, input_path)

            # Assert
            assert result is not None
            assert result.input_path == input_path
            assert len(result.pages) == 1
            assert result.pages[0].index == 1
            assert get_or_load_asset(result.pages[0], "main.md") == "line1\nline2"
            assert result.protected_soup is not None

    def test_load_ocr_pages(self):
        """
        We make sure pages are opened in the right order
        (page number and not file name order).
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Arrange - Create temporary directory structure with real files
            input_path = Path(tmpdir)

            page_dir1 = input_path / "1"
            page1 = Page(index=1, dir_path=page_dir1)
            create_asset(page1, "main.md", "content of file 1")
            save_page(page1)

            page_dir2 = input_path / "02"  # Note: different naming to test sorting
            page2 = Page(index=2, dir_path=page_dir2)
            create_asset(page2, "main.md", "content of file 2")
            save_page(page2)

            page_dir10 = input_path / "10"
            page10 = Page(index=10, dir_path=page_dir10)
            create_asset(page10, "main.md", "content of file 10")
            save_page(page10)

            # Act
            result = load_ocr_pages(self.session_context, input_path)

            # Assert
            assert result.input_path == input_path
            assert len(result.pages) == 3

            # Verify Page objects with correct indices and content order
            assert isinstance(result.pages[0], Page)
            assert result.pages[0].index == 1
            assert get_or_load_asset(result.pages[0], "main.md") == "content of file 1"

            assert isinstance(result.pages[1], Page)
            assert result.pages[1].index == 2
            assert get_or_load_asset(result.pages[1], "main.md") == "content of file 2"

            assert isinstance(result.pages[0], Page)
            assert result.pages[2].index == 10
            assert get_or_load_asset(result.pages[2], "main.md") == "content of file 10"

            assert result.protected_soup is not None
