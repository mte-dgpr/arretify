from pathlib import Path
from typing import List, Iterator

from bs4 import BeautifulSoup

from .sentence_rules import is_not_information
from .header import parse_header
from .main_content import parse_main_content
from .parse_section import (
    identify_unique_sections, filter_max_level_sections
)
from bench_convertisseur_xml.html_schemas import HEADER_SCHEMA, MAIN_SCHEMA
from bench_convertisseur_xml.utils.html import make_element
from bench_convertisseur_xml.utils.markdown import clean_markdown

TEMPLATE_PATH = Path(__file__).parent / 'template.html'
TEMPLATE_HTML = open(TEMPLATE_PATH, 'r', encoding='utf-8').read()

START_OCR_BUG_IGNORE = '<!-- START : OCR-BUG-IGNORE -->'
END_OCR_BUG_IGNORE = '<!-- END : OCR-BUG-IGNORE -->'


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


def parse_arrete(lines: List[str]):
    lines = list(_remove_ocr_bug_ignore(lines))
    lines = [ clean_markdown(line) for line in lines ]
    lines = [ line for line in lines if not is_not_information(line) ]

    # Define sections that will be parsed and detected in this document
    unique_sections = identify_unique_sections(lines)
    authorized_sections = filter_max_level_sections(unique_sections)

    soup = BeautifulSoup(TEMPLATE_HTML, features="html.parser")
    body = soup.body
    assert body

    header = make_element(soup, HEADER_SCHEMA)
    body.append(header)
    lines = parse_header(soup, header, lines, authorized_sections)

    main_content = make_element(soup, MAIN_SCHEMA)
    body.append(main_content)
    parse_main_content(soup, main_content, lines, authorized_sections)

    return soup