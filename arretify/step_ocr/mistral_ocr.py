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

_LOGGER = logging.getLogger(__name__)


def mistral_ocr(
    document_context: DocumentContext,
    replace_images_placeholders: bool,
    ocr_pages_dir: Path | None,
) -> DocumentContext:
    if not document_context.mistral_client:
        raise ValueError("MistralAI client is not initialized")

    ocr_pages: list[str] = []
    for i, page in enumerate(_call_mistral_ocr_api(document_context)):
        page_ocr = page.markdown

        if replace_images_placeholders:
            for image in page.images:
                page_ocr = page_ocr.replace(
                    f"![{image.id}]({image.id})",
                    f"![{image.id}]({image.image_base64})",
                )

        ocr_pages.append(page_ocr)
        page_index = i + 1
        if ocr_pages_dir is not None:
            page_ocr_filepath = ocr_pages_dir / f"{page_index}.md"
            with open(page_ocr_filepath, "w", encoding="utf-8") as f:
                f.write(page_ocr)
            _LOGGER.debug(f"Saved OCR page {page_index} to {page_ocr_filepath}")

    return dataclass_replace(
        document_context,
        pages=ocr_pages,
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
        file={
            "file_name": file_name,
            "content": document_context.pdf,
        },
        purpose="ocr",
    )

    # Get URL for the uploaded file
    signed_url = document_context.mistral_client.files.get_signed_url(
        file_id=uploaded_file.id, expiry=1
    )

    # Process PDF with OCR including embedded images
    api_response = document_context.mistral_client.ocr.process(
        model=document_context.settings.mistral_ocr_model,
        document={"type": "document_url", "document_url": signed_url.url},
        include_image_base64=True,
    )

    return api_response.pages
