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

from dataclasses import replace as dataclass_replace

from arretify.types import DocumentContext
from arretify.utils.pages import Page, get_or_load_asset, set_asset
from arretify.utils.strings import join_on_newlines, split_on_newlines

from .markdown_cleaning import clean_markdown
from .ocr_cleaning import clean_ocr, is_useful_line


def step_markdown_cleaning(document_context: DocumentContext) -> DocumentContext:
    if not document_context.pages:
        raise ValueError("Parsing context does not contain any pages to clean")

    cleaned_pages: list[Page] = []
    for page in document_context.pages:
        # Get main content
        main_content = get_or_load_asset(page, "main.md")
        lines = split_on_newlines(main_content)

        # Clean input markdown
        lines = [clean_markdown(line) for line in lines]

        # TODO-PROCESS-TAG
        # Remove lines that are not useful
        lines = [line for line in lines if is_useful_line(line)]

        # Clean common OCR errors
        lines = [clean_ocr(line) for line in lines]

        # Create new page with cleaned content
        set_asset(page, "main.md", join_on_newlines(lines))
        cleaned_pages.append(page)

    return dataclass_replace(document_context, pages=cleaned_pages)
