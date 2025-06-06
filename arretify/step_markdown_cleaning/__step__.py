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

from arretify.regex_utils import PatternProxy
from arretify.types import DocumentContext
from .markdown_cleaning import clean_markdown
from .ocr_cleaning import clean_ocr


PUNCTUATION_LINE_PATTERN = PatternProxy(r"^[·.,;:!?'\s\-]*$")
"""Detect if the sentence contains only punctuation."""


def step_markdown_cleaning(document_context: DocumentContext) -> DocumentContext:
    if not document_context.lines:
        raise ValueError("Parsing context does not contain any lines to clean")

    # Clean input markdown
    lines = [clean_markdown(line) for line in document_context.lines]

    # Clean common OCR errors
    lines = [clean_ocr(line) for line in lines]

    # Remove punctuation lines
    lines = [line for line in lines if not _is_punctuation_line(line.contents)]

    return dataclass_replace(document_context, lines=lines)


def _is_punctuation_line(line: str) -> bool:
    return bool(PUNCTUATION_LINE_PATTERN.search(line))
