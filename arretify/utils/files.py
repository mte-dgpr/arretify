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


def is_pdf_path(file_path: Path) -> bool:
    return file_path.is_file() and file_path.suffix.lower() == ".pdf"


def is_ocr_path(file_path: Path) -> bool:
    return file_path.is_file() and file_path.suffix.lower() == OCR_FILE_EXTENSION


def is_ocr_pages_dir(file_path: Path) -> bool:
    return file_path.is_dir() and all(is_ocr_page_path(child) for child in file_path.iterdir())


def is_ocr_page_path(file_path: Path) -> bool:
    return is_ocr_path(file_path) and file_path.stem.isdigit()
