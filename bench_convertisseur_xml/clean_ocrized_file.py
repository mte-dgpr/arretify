import re
from typing import List, Iterator

from bs4 import BeautifulSoup

from bench_convertisseur_xml.utils.html import PageElementOrString
from bench_convertisseur_xml.utils.markdown import clean_markdown
from bench_convertisseur_xml.regex_utils import PatternProxy, join_with_or, Settings


START_OCR_BUG_IGNORE = '<!-- START : OCR-BUG-IGNORE -->'
END_OCR_BUG_IGNORE = '<!-- END : OCR-BUG-IGNORE -->'

CONTINUING_SENTENCE_PATTERN = PatternProxy(r"^[a-z]", settings=Settings(ignore_case=False))

IS_NOT_INFORMATION_PATTERN = PatternProxy(
    join_with_or([
        r'^\.\.\.',
        # Sentence starting with "```"
        r'^```',
        # Sentence starting with "---"
        r'^---',
        # Empty sentence or full of whitespaces
        r'^\s*$',
        # Sentence starting with "!"
        r'^!',

        # Bottom-page with format "X/YY"
        r'^\d+/\d+\s*$',
        # Bottom-page with format "Page X/YY"
        r'^page\s+\d+/\d+\s*$',
        # Bottom-page with format "Page X sur YY"
        r'^page\s+\d+\s+sur\s+\d+\s*$',
        # Bottom-page with format "Page X"
        r'^page\s+\d+$',

        # Sentence starting with "sur"
        r'^sur\b',
        # Sentence starting with "apres"
        r'^après\b',

        # French Republic
        r"république fran[cç]aise",
        # French national motto
        r"(liberté|égalité|fraternité)",
        # Phone numbers
        r'\d{2}[\s.]\d{2}[\s.]\d{2}[\s.]\d{2}[\s.]\d{2}',
        # Email address
        r'\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b',
    ])
)


def clean_ocrized_file(lines: List[str]) -> List[str]:
    soup = BeautifulSoup()
    lines = list(_remove_ocr_bug_ignore(lines))
    lines = [ clean_markdown(line) for line in lines ]
    lines = [ line for line in lines if not _is_not_information(line) ]

    stitched_lines: List[str] = []
    for line in lines:
        if _is_continuing_sentence(line) and stitched_lines:
            # TODO-PROCESS-TAG
            stitched_lines[-1] = stitched_lines[-1] + ' ' + line
        else:
            stitched_lines.append(line)
    
    return stitched_lines


def _is_continuing_sentence(line: str) -> bool:
    """Detect sentence starting with lowercase character."""
    return bool(CONTINUING_SENTENCE_PATTERN.match(line))


def _is_not_information(line: str) -> bool:
    return bool(IS_NOT_INFORMATION_PATTERN.search(line))


def _remove_ocr_bug_ignore(lines: List[str]) -> Iterator[str]:
    is_inside_ignore_section = False
    for line in lines:
        if END_OCR_BUG_IGNORE in line:    
            is_inside_ignore_section = False
            continue
        elif START_OCR_BUG_IGNORE in line:
            is_inside_ignore_section = True
            continue

        if not is_inside_ignore_section:
            yield line