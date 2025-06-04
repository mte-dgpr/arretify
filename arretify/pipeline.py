from typing import Callable, List
from pathlib import Path

from bs4 import BeautifulSoup

from .parsing_utils.source_mapping import initialize_lines
from .types import ParsingContext, SessionContext
from .settings import DEFAULT_ARRETE_TEMPLATE, OCR_FILE_EXTENSION
from .step_segmentation import step_segmentation
from .clean_ocrized_file import clean_ocrized_file


PipelineStep = Callable[[ParsingContext], ParsingContext]


def run_pipeline(
    parsing_context: ParsingContext,
    steps: List[PipelineStep] | None = None,
) -> ParsingContext:
    if steps is None:
        steps = [
            clean_ocrized_file,
            step_segmentation,
        ]

    for step in steps:
        parsing_context = step(parsing_context)
    return parsing_context


def load_pdf_file(
    session_context: SessionContext,
    input_path: Path,
    arrete_template: str = DEFAULT_ARRETE_TEMPLATE,
) -> ParsingContext:
    if not input_path.is_file():
        raise ValueError(f"Input path {input_path} is not a file.")

    return ParsingContext.from_session_context(
        session_context,
        filename=input_path.stem,
        pdf=input_path.read_bytes(),
        soup=BeautifulSoup(arrete_template, features="html.parser"),
    )


def load_ocr_file(
    session_context: SessionContext,
    input_path: Path,
    arrete_template: str = DEFAULT_ARRETE_TEMPLATE,
) -> ParsingContext:
    raw_lines: List[str] = []

    if not input_path.is_file():
        raise ValueError(f"Input path {input_path} is not a file.")

    with open(input_path, "r", encoding="utf-8") as f:
        raw_lines = f.readlines()

    return ParsingContext.from_session_context(
        session_context,
        filename=input_path.stem,
        lines=initialize_lines(raw_lines),
        soup=BeautifulSoup(arrete_template, features="html.parser"),
    )


def load_ocr_pages(
    session_context: SessionContext,
    input_path: Path,
    arrete_template: str = DEFAULT_ARRETE_TEMPLATE,
) -> ParsingContext:
    raw_lines: List[str] = []

    if not input_path.is_dir():
        raise ValueError(f"Input path {input_path} is not a directory.")

    file_paths = sorted(input_path.glob(f"*{OCR_FILE_EXTENSION}"), key=lambda p: int(p.stem))
    for file_path in file_paths:
        with open(file_path, "r", encoding="utf-8") as file:
            raw_lines.extend(file.readlines())

    return ParsingContext.from_session_context(
        session_context,
        filename=input_path.name,
        lines=initialize_lines(raw_lines),
        soup=BeautifulSoup(arrete_template, features="html.parser"),
    )


def save_html_file(
    output_path: Path,
    parsing_context: ParsingContext,
) -> None:
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(parsing_context.soup.prettify())
