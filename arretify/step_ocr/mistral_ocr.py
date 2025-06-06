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
from typing import List, Iterable
from dataclasses import replace as dataclass_replace
from shutil import rmtree

from arretify._vendor import mistralai

from arretify.types import DocumentContext
from arretify.parsing_utils.source_mapping import initialize_lines


_LOGGER = logging.getLogger(__name__)


def mistral_ocr(
    document_context: DocumentContext,
    replace_images_placeholders: bool = True,
) -> DocumentContext:
    if not document_context.mistral_client:
        raise ValueError("MistralAI client is not initialized")

    # Save the OCR result to a tmp directory
    pages_ocr_dir = document_context.settings.tmp_dir / f"{document_context.filename}_ocr"
    if pages_ocr_dir.is_dir():
        rmtree(pages_ocr_dir, ignore_errors=True)
    pages_ocr_dir.mkdir(parents=True, exist_ok=True)
    _LOGGER.info(f"Created OCR pages dir : {pages_ocr_dir}")

    pages_ocr: List[str] = []
    for i, page in enumerate(
        _call_mistral_ocr_api(
            document_context,
            replace_images_placeholders=replace_images_placeholders,
        )
    ):
        page_ocr = page.markdown

        if replace_images_placeholders:
            for image in page.images:
                page_ocr = page_ocr.replace(
                    f"![{image.id}]({image.id})",
                    f"![{image.id}]({image.image_base64})",
                )

        pages_ocr.append(page_ocr)
        page_index = i + 1
        page_ocr_filepath = pages_ocr_dir / f"{page_index}.md"
        with open(page_ocr_filepath, "w", encoding="utf-8") as f:
            f.write(page_ocr)
        _LOGGER.debug(f"Saved OCR page {page_index} to {page_ocr_filepath}")

    return dataclass_replace(
        document_context,
        lines=initialize_lines([line for page_ocr in pages_ocr for line in page_ocr.split("\n")]),
    )


def _call_mistral_ocr_api(
    document_context: DocumentContext,
    replace_images_placeholders: bool = True,
    max_retries: int = 5,
) -> Iterable[mistralai.models.OCRPageObject]:
    if not document_context.mistral_client:
        raise ValueError("MistralAI client is not initialized")
    if not document_context.pdf:
        raise ValueError("Parsing context does not contain a PDF file")

    _LOGGER.info(f"Starting OCR process with MistralAI for {document_context.filename}...")

    cnt_retries = 0
    while cnt_retries < max_retries:
        try:
            # Upload PDF file to Mistral's OCR service
            uploaded_file = document_context.mistral_client.files.upload(
                file={
                    "file_name": document_context.filename,
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

        except mistralai.models.sdkerror.SDKError as err:
            cnt_retries += 1
            _LOGGER.debug(err)
            _LOGGER.debug("OCR failed: Retrying %d/%d", cnt_retries, max_retries)

        break

    if cnt_retries >= max_retries:
        raise ValueError("OCR failed: max retries reached!")

    return api_response.pages
