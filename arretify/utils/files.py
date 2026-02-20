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
from pathlib import Path

from arretify.settings import OCR_FILE_EXTENSION
from arretify.utils.pages import PAGE_JSON_FILE_NAME


def is_pdf_path(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() == ".pdf"


def is_standalone_ocr_path(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() == OCR_FILE_EXTENSION


def is_ocr_pages_dir(path: Path) -> bool:
    return path.is_dir() and all(_is_ocr_page_dir(child) for child in path.iterdir())


def _is_ocr_page_dir(path: Path) -> bool:
    if not path.is_dir() or not path.stem.isdigit():
        return False
    has_page_json = any(file_path.name == PAGE_JSON_FILE_NAME for file_path in path.iterdir())
    return has_page_json
