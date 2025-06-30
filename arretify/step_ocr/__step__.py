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
from typing import Callable
from pathlib import Path

from arretify.types import DocumentContext
from arretify.utils.sentinel import Sentinel
from .mistral_ocr import mistral_ocr, default_ocr_pages_dir


_LOGGER = logging.getLogger(__name__)
# Sentinel value, used to check that the kwarg `ocr_pages_dir_factory`
# is not provided by the user.
_OCR_PAGES_DIR_FACTORY_SENTINEL = Sentinel("ocr_pages_dir_factory")


def step_ocr(
    document_context: DocumentContext,
    replace_images_placeholders: bool = True,
    ocr_pages_dir_factory: (
        Callable[[DocumentContext], Path] | None | Sentinel
    ) = _OCR_PAGES_DIR_FACTORY_SENTINEL,
) -> DocumentContext:
    if not document_context.pdf:
        raise ValueError("Parsing context does not contain a PDF file")

    # Default factory for OCR pages directory
    # Varies depending on the environment.
    ocr_pages_dir_factory_: Callable[[DocumentContext], Path] | None = None
    if ocr_pages_dir_factory is _OCR_PAGES_DIR_FACTORY_SENTINEL:
        # In development, store pages in tmp directory configured in settings.
        if document_context.settings.env == "development":
            ocr_pages_dir_factory_ = default_ocr_pages_dir
        # In production, do not store OCR pages.
        else:
            ocr_pages_dir_factory_ = None

    return mistral_ocr(
        document_context,
        replace_images_placeholders=replace_images_placeholders,
        ocr_pages_dir_factory=ocr_pages_dir_factory_,
    )
