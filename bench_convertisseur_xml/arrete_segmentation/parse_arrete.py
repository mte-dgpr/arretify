from pathlib import Path
from typing import List, Iterator

from bs4 import BeautifulSoup

from bench_convertisseur_xml.settings import APP_ROOT
from .header import parse_header
from .main_content import parse_main_content
from .parse_section_title import identify_unique_sections, filter_max_level_sections
from bench_convertisseur_xml.html_schemas import HEADER_SCHEMA, MAIN_SCHEMA
from bench_convertisseur_xml.utils.html import make_data_tag

TEMPLATE_PATH = APP_ROOT / 'bench_convertisseur_xml' / 'templates' / 'index.html'
TEMPLATE_HTML = open(TEMPLATE_PATH, 'r', encoding='utf-8').read()


def parse_arrete(lines: List[str]):
    # Define sections that will be parsed and detected in this document
    unique_sections = identify_unique_sections(lines)
    authorized_sections = filter_max_level_sections(unique_sections)

    soup = BeautifulSoup(TEMPLATE_HTML, features="html.parser")
    body = soup.body
    assert body

    header = make_data_tag(soup, HEADER_SCHEMA)
    body.append(header)
    lines = parse_header(soup, header, lines, authorized_sections)

    main_content = make_data_tag(soup, MAIN_SCHEMA)
    body.append(main_content)
    parse_main_content(soup, main_content, lines, authorized_sections)

    return soup