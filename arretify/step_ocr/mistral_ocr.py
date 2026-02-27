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
import logging
from dataclasses import replace as dataclass_replace
from pathlib import Path
from typing import Iterable

from arretify._vendor import mistralai
from arretify.types import DocumentContext
from arretify.utils.ocr_document import OcrDocument, Page, save_ocr_document, set_asset

_LOGGER = logging.getLogger(__name__)


def mistral_ocr(
    document_context: DocumentContext,
    ocr_document_dir: Path | None,
) -> DocumentContext:
    if not document_context.mistral_client:
        raise ValueError("MistralAI client is not initialized")

    pages: list[Page] = []
    for ocr_page in _call_mistral_ocr_api(document_context):
        page_index = ocr_page.index + 1

        # Determine dir_path for this page
        page_dir = None
        if ocr_document_dir is not None:
            page_dir = ocr_document_dir / str(page_index)

        # Create page with optional dir_path
        page = Page(index=page_index, dir_path=page_dir)

        # Add main content
        set_asset(page, "main.md", ocr_page.markdown)

        # Add header if present
        if isinstance(ocr_page.header, str):
            set_asset(page, "header.md", ocr_page.header)

        # Add footer if present
        if isinstance(ocr_page.footer, str):
            set_asset(page, "footer.md", ocr_page.footer)

        # Add images
        for image in ocr_page.images:
            if not isinstance(image.image_base64, str):
                _LOGGER.warning(f"Skipping image with unsupported format in page {page_index}")
                continue
            set_asset(page, image.id, image.image_base64)

        # Add tables
        for table in ocr_page.tables or []:
            set_asset(page, table.id, table.content)

        pages.append(page)

    ocr_document = OcrDocument(pages=pages)
    if ocr_document_dir is not None:
        _LOGGER.debug(f"Saved OCR document to {ocr_document_dir}")
        save_ocr_document(ocr_document, ocr_document_dir)

    return dataclass_replace(
        document_context,
        ocr_document=ocr_document,
    )


def _call_mistral_ocr_api(
    document_context: DocumentContext,
) -> Iterable[mistralai.models.OCRPageObject]:
    if not document_context.mistral_client:
        raise ValueError("MistralAI client is not initialized")
    if not document_context.pdf:
        raise ValueError("Parsing context does not contain a PDF file")

    file_name = (
        document_context.input_path.name if document_context.input_path else "unnamed_file.pdf"
    )
    _LOGGER.debug(f"Starting OCR process with MistralAI for {file_name}...")

    # Upload PDF file to Mistral's OCR service
    uploaded_file = document_context.mistral_client.files.upload(
        file=dict(
            file_name=file_name,
            content=document_context.pdf,
        ),
        purpose="ocr",
    )

    # Get URL for the uploaded file
    signed_url = document_context.mistral_client.files.get_signed_url(
        file_id=uploaded_file.id, expiry=1
    )

    # Process PDF with OCR including embedded images
    api_response = document_context.mistral_client.ocr.process(
        model=document_context.settings.mistral_ocr_model,
        document=dict(type="document_url", document_url=signed_url.url),
        include_image_base64=True,
        extract_footer=True,
        extract_header=True,
        table_format="html",
    )

    return api_response.pages
