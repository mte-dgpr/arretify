import re
from typing import List, Iterator

from bs4 import BeautifulSoup

from bench_convertisseur_xml.utils.html import PageElementOrString
from bench_convertisseur_xml.utils.text import remove_accents


START_OCR_BUG_IGNORE = '<!-- START : OCR-BUG-IGNORE -->'
END_OCR_BUG_IGNORE = '<!-- END : OCR-BUG-IGNORE -->'


def clean_ocrized_file(lines: List[str]) -> List[str]:
    soup = BeautifulSoup()
    lines = list(_remove_ocr_bug_ignore(lines))
    lines = [ _clean_markdown(line) for line in lines ]
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
    """Detect sentence starting wit lowercase character."""
    return bool(re.match(r"^[a-z]", remove_accents(line)))


def _clean_markdown(text: str) -> str:
    # Remove newline at the end
    text = re.sub(r'[\n\r]+$', '', text)

    # Remove * at the beginning only if not followed by space
    text = re.sub(r"^\*+(?!\s)", "", text)

    # Remove * at the end only if not preceded by space
    text = re.sub(r"(?<!\s)\*+$", "", text)

    # Remove any number of # or whitespaces at the beginning of the sentence
    text = re.sub(r"^[#\s]+", "", text)

    return text


def _is_not_information(line: str) -> bool:

    patterns_to_ignore = [
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
        r'^apr[eè]s\b',

        # French Republic
        r"r[eé]publique fran[cç]aise",
        # French national motto
        r"(libert[eé]|[eé]galit[eé]|fraternit[eé])",
        # Phone numbers
        r'\d{2}[\s.]\d{2}[\s.]\d{2}[\s.]\d{2}[\s.]\d{2}'
    ]
    pattern = '|'.join(f'(?:{pattern})' for pattern in patterns_to_ignore)

    search_result = bool(re.search(pattern, line, re.IGNORECASE))

    return search_result


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