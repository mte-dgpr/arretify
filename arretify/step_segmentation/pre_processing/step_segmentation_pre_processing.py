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

from typing import Iterator

from arretify.utils.ocr_document import get_or_load_asset_content, OcrDocument
from arretify.types import DocumentContext, ProtectedTagOrStr
from arretify.utils.functional import iter_func_to_list
from arretify.utils.ocr_document import OcrDocument
from arretify.utils.strings import join_on_newlines, split_on_newlines

from .basic_elements import parse_basic_elements
from .markdown_cleaning import clean_markdown
from .ocr_cleaning import clean_ocr, is_useful_line


@iter_func_to_list
def step_segmentation_pre_processing(
    document_context: DocumentContext,
    ocr_document: OcrDocument,
) -> Iterator[ProtectedTagOrStr]:
    """
    Pre-processes the contents of the document for later segmentation.
    """
    for page in ocr_document.pages:
        # Get main content
        main_content = get_or_load_asset_content(page.assets["main.md"])
        lines = split_on_newlines(main_content)

        # Clean input markdown
        lines = [clean_markdown(line) for line in lines]
        lines = [line for line in lines if is_useful_line(line)]
        lines = [clean_ocr(line) for line in lines]

        # Create new page with cleaned content
        page.assets["main.md"].content = join_on_newlines(lines)

        yield from parse_basic_elements(document_context, page)
