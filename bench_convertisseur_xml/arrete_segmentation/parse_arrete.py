from bs4 import BeautifulSoup

from bench_convertisseur_xml.settings import APP_ROOT
from bench_convertisseur_xml.html_schemas import HEADER_SCHEMA, MAIN_SCHEMA
from bench_convertisseur_xml.utils.html import make_data_tag
from bench_convertisseur_xml.parsing_utils.source_mapping import TextSegments
from .header import parse_header
from .main_content import parse_main_content


TEMPLATE_PATH = APP_ROOT / 'bench_convertisseur_xml' / 'templates' / 'arrete.html'
TEMPLATE_HTML = open(TEMPLATE_PATH, 'r', encoding='utf-8').read()


def parse_arrete(lines: TextSegments) -> BeautifulSoup:
    # Define sections that will be parsed and detected in this document
    soup = BeautifulSoup(TEMPLATE_HTML, features="html.parser")
    body = soup.body
    assert body

    header = make_data_tag(soup, HEADER_SCHEMA)
    body.append(header)
    lines = parse_header(soup, header, lines)

    main_content = make_data_tag(soup, MAIN_SCHEMA)
    body.append(main_content)
    parse_main_content(soup, main_content, lines)

    return soup
