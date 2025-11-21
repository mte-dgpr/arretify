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
from pathlib import Path
from unittest import mock

from arretify.pipeline import load_ocr_file, load_ocr_pages, load_pdf_file
from arretify.settings import Settings
from arretify.types import SessionContext


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

    def test_load_ocr_file(self):
        # Arrange
        input_path = mock.Mock(spec=Path)
        input_path.is_file.return_value = True
        input_path.suffix = ".md"
        m = mock.mock_open(read_data="line1\nline2")
        with mock.patch("builtins.open", m):
            # Act
            result = load_ocr_file(self.session_context, input_path)

            # Assert
            assert result is not None
            assert result.input_path == input_path
            assert result.pages == ["line1\nline2"]
            assert result.protected_soup is not None

    def test_load_ocr_pages(self):
        """
        We make sure pages are opened in the right order
        (page number and not file name order).
        """
        # Arrange
        input_path = mock.Mock(spec=Path)
        input_path.is_dir.return_value = True

        mock_file_path1 = mock.Mock(spec=Path)
        mock_file_path1.stem = "1"
        mock_file_path1.suffix = ".md"
        mock_file_path10 = mock.Mock(spec=Path)
        mock_file_path10.stem = "10"
        mock_file_path10.suffix = ".md"
        mock_file_path2 = mock.Mock(spec=Path)
        mock_file_path2.stem = "02"
        mock_file_path2.suffix = ".md"

        input_path.glob.return_value = [mock_file_path1, mock_file_path10, mock_file_path2]
        input_path.iterdir.return_value = [
            mock_file_path1,
            mock_file_path10,
            mock_file_path2,
        ]

        def _mock_file_open(*args, **kwargs):
            file_path = args[0]
            return mock.mock_open(
                read_data={
                    str(mock_file_path1): "content of file 1",
                    str(mock_file_path10): "content of file 10",
                    str(mock_file_path2): "content of file 2",
                }[str(file_path)]
            ).return_value

        with mock.patch("builtins.open", side_effect=_mock_file_open):
            # Act
            result = load_ocr_pages(self.session_context, input_path)

            # Assert
            assert result is not None
            assert result.input_path == input_path
            assert result.pages == [
                "content of file 1",
                "content of file 2",
                "content of file 10",
            ]
            assert result.protected_soup is not None
