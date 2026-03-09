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
from pathlib import Path
from shutil import rmtree
from uuid import uuid4

from arretify.types import DocumentContext
from arretify.utils.sentinel import Sentinel

from .mistral_ocr import mistral_ocr

_LOGGER = logging.getLogger(__name__)
# Sentinel value, used to check that the kwarg `ocr_document_dir`
# is not provided by the user.
_OCR_DOCUMENT_DIR_SENTINEL = Sentinel("ocr_document_dir")


def step_ocr(
    document_context: DocumentContext,
    ocr_document_dir: Path | None | Sentinel = _OCR_DOCUMENT_DIR_SENTINEL,
) -> DocumentContext:
    if not document_context.pdf:
        raise ValueError("Parsing context does not contain a PDF file")

    # Default factory for OCR document directory
    # Varies depending on the environment.
    ocr_document_dir_: Path | None
    if ocr_document_dir is _OCR_DOCUMENT_DIR_SENTINEL:
        # In development, by default store document in tmp directory configured in settings.
        if document_context.settings.env == "development":
            ocr_document_dir_ = get_tmp_ocr_document_dir(document_context)
        # In production, by default do not store OCR document.
        else:
            ocr_document_dir_ = None
    else:
        assert isinstance(ocr_document_dir, (Path, type(None)))
        ocr_document_dir_ = ocr_document_dir

    return mistral_ocr(
        document_context,
        ocr_document_dir=ocr_document_dir_,
    )


def get_tmp_ocr_document_dir(document_context: DocumentContext) -> Path:
    prefix = document_context.input_path.name if document_context.input_path else str(uuid4())
    ocr_document_dir = document_context.settings.tmp_dir / f"{prefix}_ocr"
    if ocr_document_dir.is_dir():
        rmtree(ocr_document_dir, ignore_errors=True)
    ocr_document_dir.mkdir(parents=True, exist_ok=True)
    _LOGGER.info(f"Created OCR document dir : {ocr_document_dir}")
    return ocr_document_dir
