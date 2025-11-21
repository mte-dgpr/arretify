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
from typing import Callable, Sequence

from bs4 import BeautifulSoup

from arretify.utils.files import is_ocr_pages_dir, is_ocr_path, is_pdf_path

from .settings import DEFAULT_ARRETE_TEMPLATE, OCR_FILE_EXTENSION
from .step_markdown_cleaning import step_markdown_cleaning
from .step_segmentation import step_segmentation
from .types import DocumentContext, SessionContext

PipelineStep = Callable[[DocumentContext], DocumentContext]


def run_pipeline(
    document_context: DocumentContext,
    steps: Sequence[PipelineStep] | None = None,
) -> DocumentContext:
    if steps is None:
        steps = [
            step_markdown_cleaning,
            step_segmentation,
        ]

    for step in steps:
        document_context = step(document_context)
    return document_context


def load_pdf_file(
    session_context: SessionContext,
    input_path: Path,
    arrete_template: str = DEFAULT_ARRETE_TEMPLATE,
) -> DocumentContext:
    if not is_pdf_path(input_path):
        raise ValueError(f"Input path {input_path} is not a file.")

    return DocumentContext.from_session_context(
        session_context,
        input_path=input_path,
        pdf=input_path.read_bytes(),
        soup=BeautifulSoup(arrete_template, features="html.parser"),
    )


def load_ocr_file(
    session_context: SessionContext,
    input_path: Path,
    arrete_template: str = DEFAULT_ARRETE_TEMPLATE,
) -> DocumentContext:
    page_ocr: str

    if not is_ocr_path(input_path):
        raise ValueError(f"Input path {input_path} is not a file.")

    with open(input_path, "r", encoding="utf-8") as f:
        page_ocr = f.read()

    return DocumentContext.from_session_context(
        session_context,
        input_path=input_path,
        pages=[page_ocr],
        soup=BeautifulSoup(arrete_template, features="html.parser"),
    )


def load_ocr_pages(
    session_context: SessionContext,
    input_path: Path,
    arrete_template: str = DEFAULT_ARRETE_TEMPLATE,
) -> DocumentContext:
    if not is_ocr_pages_dir(input_path):
        raise ValueError(f"Input path {input_path} is not a directory.")

    file_paths = sorted(input_path.glob(f"*{OCR_FILE_EXTENSION}"), key=lambda p: int(p.stem))
    pages_ocr: list[str] = []
    for file_path in file_paths:
        with open(file_path, "r", encoding="utf-8") as file:
            pages_ocr.append(file.read())

    return DocumentContext.from_session_context(
        session_context,
        input_path=input_path,
        pages=pages_ocr,
        soup=BeautifulSoup(arrete_template, features="html.parser"),
    )


def load_html_file(
    session_context: SessionContext,
    input_path: Path,
) -> DocumentContext:
    if not input_path.is_file():
        raise ValueError(f"Input path {input_path} is not a file.")

    with open(input_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    soup = BeautifulSoup(html_content, features="html.parser")
    return DocumentContext.from_session_context(
        session_context,
        input_path=input_path,
        soup=soup,
    )


def save_html_file(
    output_path: Path,
    document_context: DocumentContext,
) -> DocumentContext:
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(document_context.soup.prettify())
    return document_context
