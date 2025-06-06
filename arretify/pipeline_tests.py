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
from unittest import mock
from pathlib import Path

from arretify.pipeline import (
    load_pdf_file,
    load_ocr_file,
    load_ocr_pages,
)
from arretify.types import SessionContext
from arretify.parsing_utils.source_mapping import initialize_lines
from arretify.settings import Settings


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
        input_path.stem = "dummy_path"

        # Act
        result = load_pdf_file(self.session_context, input_path)

        # Assert
        assert result is not None
        assert result.filename == "dummy_path"
        assert result.pdf == b"dummy pdf content"
        assert result.soup is not None

    def test_load_ocr_file(self):
        # Arrange
        input_path = mock.Mock(spec=Path)
        input_path.is_file.return_value = True
        input_path.stem = "dummy_path"
        m = mock.mock_open(read_data="line1\nline2")
        with mock.patch("builtins.open", m):
            # Act
            result = load_ocr_file(self.session_context, input_path)

            # Assert
            assert result is not None
            assert result.filename == "dummy_path"
            assert result.lines == initialize_lines(["line1\n", "line2"])
            assert result.soup is not None

    def test_load_ocr_pages(self):
        """
        We make sure pages are opened in the right order
        (page number and not file name order).
        """
        # Arrange
        input_path = mock.Mock(spec=Path)
        input_path.is_dir.return_value = True
        input_path.name = "dummy_directory"

        mock_file_path1 = mock.Mock(spec=Path)
        mock_file_path1.stem = "1"
        mock_file_path10 = mock.Mock(spec=Path)
        mock_file_path10.stem = "10"
        mock_file_path2 = mock.Mock(spec=Path)
        mock_file_path2.stem = "02"
        input_path.glob.return_value = [mock_file_path1, mock_file_path10, mock_file_path2]

        def _mock_file_open(*args, **kwargs):
            file_path = args[0]
            return mock.mock_open(
                read_data={
                    str(mock_file_path1): "content of file 1\n",
                    str(mock_file_path10): "content of file 10\n",
                    str(mock_file_path2): "content of file 2\n",
                }[str(file_path)]
            ).return_value

        with mock.patch("builtins.open", side_effect=_mock_file_open):
            # Act
            result = load_ocr_pages(self.session_context, input_path)

            # Assert
            assert result is not None
            assert result.filename == "dummy_directory"
            assert result.lines == initialize_lines(
                ["content of file 1\n", "content of file 2\n", "content of file 10\n"]
            )
            assert result.soup is not None
