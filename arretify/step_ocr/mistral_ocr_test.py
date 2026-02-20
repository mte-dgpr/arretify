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

from bs4 import BeautifulSoup

from arretify._vendor import mistralai
from arretify.settings import Settings
from arretify.types import DocumentContext, SessionContext
from arretify.utils.pages import get_or_load_asset

from .mistral_ocr import mistral_ocr


class TestMistralOcr(unittest.TestCase):
    def test_mistral_ocr_with_pages_dir(self):
        """Test mistral_ocr creates pages and saves them when ocr_pages_dir is provided."""
        # Arrange
        mock_ocr_pages = [
            mistralai.models.OCRPageObject(
                index=0,
                markdown="# Page 1 Content",
                header="Page 1 Header",
                footer="Page 1 Footer",
                images=[
                    mistralai.models.OCRImageObject(
                        id="img-001",
                        top_left_x=10,
                        top_left_y=20,
                        bottom_right_x=100,
                        bottom_right_y=200,
                        image_base64="base64imagedata1",
                    )
                ],
                tables=[
                    mistralai.models.OCRTableObject(
                        id="table-001",
                        content="<table><tr><td>Data 1</td></tr></table>",
                        format_="html",
                    )
                ],
                dimensions=None,
            ),
            mistralai.models.OCRPageObject(
                index=1,
                markdown="# Page 2 Content",
                header=None,
                footer=None,
                images=[],
                tables=[],
                dimensions=None,
            ),
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            ocr_pages_dir = Path(temp_dir)

            # Create a mock document context
            settings = mock.Mock(spec=Settings)
            soup = BeautifulSoup("<html></html>", "html.parser")
            mistral_client = mock.Mock(spec=mistralai.Mistral)

            document_context = DocumentContext.from_session_context(
                SessionContext(
                    settings=settings,
                    mistral_client=mistral_client,
                ),
                soup=soup,
                input_path=Path("test.pdf"),
                pdf=b"fake pdf content",
            )

            # Mock _call_mistral_ocr_api
            with mock.patch(
                "arretify.step_ocr.mistral_ocr._call_mistral_ocr_api", return_value=mock_ocr_pages
            ) as mock_call_api:
                # Act
                result_context = mistral_ocr(document_context, ocr_pages_dir)

            # Assert
            # Verify API was called with correct context
            mock_call_api.assert_called_once_with(document_context)

            # Verify pages were created
            assert result_context.pages is not None
            assert len(result_context.pages) == 2

            # Verify first page
            page1 = result_context.pages[0]
            assert page1.index == 1
            assert get_or_load_asset(page1, "main.md") == "# Page 1 Content"
            assert get_or_load_asset(page1, "header.md") == "Page 1 Header"
            assert get_or_load_asset(page1, "footer.md") == "Page 1 Footer"
            assert get_or_load_asset(page1, "img-001.b64") == "base64imagedata1"
            assert (
                get_or_load_asset(page1, "table-001.html")
                == "<table><tr><td>Data 1</td></tr></table>"
            )

            # Verify second page
            page2 = result_context.pages[1]
            assert page2.index == 2
            assert get_or_load_asset(page2, "main.md") == "# Page 2 Content"

            # Verify files were saved
            page1_dir = ocr_pages_dir / "1"
            assert page1_dir.exists()
            assert (page1_dir / "main.md").exists()
            assert (page1_dir / "header.md").exists()
            assert (page1_dir / "footer.md").exists()
            assert (page1_dir / "img-001.b64").exists()
            assert (page1_dir / "table-001.html").exists()
            assert (page1_dir / "page.json").exists()

            page2_dir = ocr_pages_dir / "2"
            assert page2_dir.exists()
            assert (page2_dir / "main.md").exists()
            assert (page2_dir / "page.json").exists()

    def test_mistral_ocr_without_pages_dir(self):
        """Test mistral_ocr creates pages in-memory when ocr_pages_dir is None."""
        # Arrange
        mock_ocr_pages = [
            mistralai.models.OCRPageObject(
                index=0,
                markdown="# In-memory Content",
                header="In-memory Header",
                footer=None,
                images=[],
                tables=[],
                dimensions=None,
            ),
        ]

        # Create a mock document context
        settings = mock.Mock(spec=Settings)
        soup = BeautifulSoup("<html></html>", "html.parser")
        mistral_client = mock.Mock(spec=mistralai.Mistral)

        document_context = DocumentContext.from_session_context(
            SessionContext(
                settings=settings,
                mistral_client=mistral_client,
            ),
            soup=soup,
            input_path=Path("test.pdf"),
            pdf=b"fake pdf content",
        )

        # Mock _call_mistral_ocr_api
        with mock.patch(
            "arretify.step_ocr.mistral_ocr._call_mistral_ocr_api", return_value=mock_ocr_pages
        ) as mock_call_api:
            # Act
            result_context = mistral_ocr(document_context, ocr_pages_dir=None)

        # Assert
        mock_call_api.assert_called_once_with(document_context)

        # Verify pages were created in memory
        assert len(result_context.pages) == 1

        page = result_context.pages[0]
        assert page.index == 1
        assert get_or_load_asset(page, "main.md") == "# In-memory Content"
        assert get_or_load_asset(page, "header.md") == "In-memory Header"

        # Verify no dir_path is set (in-memory only)
        assert page.dir_path is None
