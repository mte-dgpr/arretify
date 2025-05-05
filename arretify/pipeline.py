from typing import Callable, List
from pathlib import Path

from bs4 import BeautifulSoup

from .parsing_utils.source_mapping import initialize_lines
from .types import ParsingContext, SessionContext, TextSegments
from .settings import DEFAULT_ARRETE_TEMPLATE
from .step_segmentation import step_segmentation
from .clean_ocrized_file import clean_ocrized_file


CleaningPipelineStep = Callable[[TextSegments], TextSegments]
ParsingPipelineStep = Callable[[ParsingContext], ParsingContext]


def ocr_to_html(
    session_context: SessionContext,
    lines: TextSegments,
    arrete_template: str = DEFAULT_ARRETE_TEMPLATE,
    cleaning_steps: List[CleaningPipelineStep] | None = None,
    parsing_steps: List[ParsingPipelineStep] | None = None,
) -> ParsingContext:
    if cleaning_steps is None:
        cleaning_steps = [
            clean_ocrized_file,
        ]

    if parsing_steps is None:
        parsing_steps = [
            step_segmentation,
        ]

    return execute_parsing_pipeline(
        ParsingContext.from_session_context(
            session_context,
            lines=execute_cleaning_pipeline(
                lines=lines,
                steps=cleaning_steps,
            ),
            soup=BeautifulSoup(arrete_template, features="html.parser"),
        ),
        steps=parsing_steps,
    )


def execute_cleaning_pipeline(
    lines: TextSegments, steps: List[CleaningPipelineStep]
) -> TextSegments:
    for step in steps:
        lines = step(lines)
    return lines


def execute_parsing_pipeline(
    parsing_context: ParsingContext, steps: List[ParsingPipelineStep]
) -> ParsingContext:
    for step in steps:
        parsing_context = step(parsing_context)
    return parsing_context


def load_ocr_file(
    input_path: Path,
) -> TextSegments:
    with open(input_path, "r", encoding="utf-8") as f:
        raw_lines = f.readlines()
    return initialize_lines(raw_lines)


def save_html_file(
    output_path: Path,
    parsing_context: ParsingContext,
) -> None:
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(parsing_context.soup.prettify())
