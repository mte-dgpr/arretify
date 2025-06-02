# TODO : Move to step folder ocr_cleaning
from dataclasses import replace as dataclass_replace

from arretify.utils.markdown_cleaning import clean_markdown
from arretify.regex_utils import (
    PatternProxy,
    join_with_or,
)
from arretify.types import ParsingContext


EMPTY_LINE_PATTERN = PatternProxy(r"^\s*$")
"""Detect if the sentence is empty or full of whitespaces."""

PUNCTUATION_LINE_PATTERN = PatternProxy(r"^[.,;:!?']+$")
"""Detect if the sentence contains only punctuation."""

FOOTER_PATTERN = PatternProxy(
    join_with_or(
        [
            # "X/YY"
            r"^\d+/\d+\s*$",
            # "Page X/YY"
            r"^page\s+\d+/\d+\s*$",
            # "Page X sur YY"
            r"^page\s+\d+\s+sur\s+\d+\s*$",
            # "Page X"
            r"^page\s+\d+$",
        ]
    )
)
"""Detect footer for numbering pages."""


def clean_ocrized_file(parsing_context: ParsingContext) -> ParsingContext:
    if not parsing_context.lines:
        raise ValueError("Parsing context does not contain any lines to clean")

    # Clean input markdown
    lines = [clean_markdown(line) for line in parsing_context.lines]

    # Remove empty lines
    lines = [line for line in lines if not _is_empty_line(line.contents)]

    # Remove punctuation lines
    lines = [line for line in lines if not _is_punctuation_line(line.contents)]

    # Remove footer lines
    lines = [line for line in lines if not _is_footer_line(line.contents)]

    return dataclass_replace(parsing_context, lines=lines)


def _is_empty_line(line: str) -> bool:
    return bool(EMPTY_LINE_PATTERN.search(line))


def _is_punctuation_line(line: str) -> bool:
    return bool(PUNCTUATION_LINE_PATTERN.search(line))


def _is_footer_line(line: str) -> bool:
    return bool(FOOTER_PATTERN.search(line))
