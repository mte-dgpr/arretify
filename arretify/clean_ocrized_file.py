from arretify.utils.markdown_cleaning import clean_markdown
from arretify.regex_utils import (
    PatternProxy,
    Settings,
)
from arretify.parsing_utils.source_mapping import (
    TextSegments,
    combine_text_segments,
)


CONTINUING_SENTENCE_PATTERN = PatternProxy(r"^[a-z]", settings=Settings(ignore_case=False))
"""Detect if this is a continuing sentence."""

EMPTY_LINE_PATTERN = PatternProxy(r"^\s*$")
"""Detect if the sentence is empty or full of whitespaces."""


def clean_ocrized_file(lines: TextSegments) -> TextSegments:

    # Clean input markdown
    lines = [clean_markdown(line) for line in lines]

    # Remove empty lines
    lines = [line for line in lines if not _is_empty_line(line.contents)]

    # Assemble continuing lines
    stitched_lines: TextSegments = []
    for line in lines:
        if _is_continuing_sentence(line.contents) and stitched_lines:
            # TODO-PROCESS-TAG
            stitched_lines[-1] = combine_text_segments(
                stitched_lines[-1].contents + " " + line.contents,
                [stitched_lines[-1], line],
            )
        else:
            stitched_lines.append(line)

    return stitched_lines


def _is_continuing_sentence(line: str) -> bool:
    """Detect sentence starting with lowercase character."""
    return bool(CONTINUING_SENTENCE_PATTERN.match(line))


def _is_empty_line(line: str) -> bool:
    return bool(EMPTY_LINE_PATTERN.search(line))
