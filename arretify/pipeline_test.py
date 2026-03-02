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

from arretify.pipeline import load_ocr_files, load_pdf_file, load_standalone_ocr_file
from arretify.settings import Settings
from arretify.types import SessionContext
from arretify.utils.ocr_document import (
    OcrDocument,
    Page,
    create_asset,
    get_or_load_asset_content,
    save_ocr_document,
)


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
        document_context = load_pdf_file(self.session_context, input_path)

        # Assert
        assert document_context is not None
        assert document_context.input_path == input_path
        assert document_context.pdf == b"dummy pdf content"
        assert document_context.protected_soup is not None

    def test_load_standalone_ocr_file(self):
        # Arrange
        input_path = mock.Mock(spec=Path)
        input_path.is_file.return_value = True
        input_path.suffix = ".md"
        input_path.read_text.return_value = "line1\nline2"

        # Act
        document_context = load_standalone_ocr_file(self.session_context, input_path)

        # Assert
        assert document_context is not None
        assert document_context.input_path == input_path
        assert len(document_context.ocr_document.pages) == 1
        assert document_context.ocr_document.pages[0].index == 1
        assert (
            get_or_load_asset_content(document_context.ocr_document.pages[0].assets["main.md"])
            == "line1\nline2"
        )
        assert document_context.protected_soup is not None

    def test_load_ocr_document(self):
        """
        We make sure pages are opened in the right order
        (page number and not file name order).
        """

        with tempfile.TemporaryDirectory() as tmpdir:
            # Arrange
            input_path = Path(tmpdir)
            page1 = Page(index=1)
            create_asset(page1, "main.md", "content of file 1")
            page2 = Page(index=2)  # Note: different naming to test sorting
            create_asset(page2, "main.md", "content of file 2")
            page10 = Page(index=10)
            create_asset(page10, "main.md", "content of file 10")
            ocr_document = OcrDocument(pages=[page1, page2, page10])
            save_ocr_document(ocr_document, input_path)

            # Act
            document_context = load_ocr_files(self.session_context, input_path)

            # Assert
            assert document_context.input_path == input_path
            assert len(document_context.ocr_document.pages) == 3

            page1 = document_context.ocr_document.pages[0]
            assert page1.index == 1
            assert get_or_load_asset_content(page1.assets["main.md"]) == "content of file 1"

            page2 = document_context.ocr_document.pages[1]
            assert page2.index == 2
            assert get_or_load_asset_content(page2.assets["main.md"]) == "content of file 2"

            page3 = document_context.ocr_document.pages[2]
            assert page3.index == 10
            assert get_or_load_asset_content(page3.assets["main.md"]) == "content of file 10"

            assert document_context.protected_soup is not None
