from bs4 import BeautifulSoup

from arretify.settings import APP_ROOT
from arretify.html_schemas import (
    HEADER_SCHEMA,
    MAIN_SCHEMA,
    APPENDIX_SCHEMA,
)
from arretify.utils.html import make_data_tag
from arretify.parsing_utils.source_mapping import (
    TextSegments,
)
from .header import parse_header
from .main_content import parse_main_content
from .appendix import is_appendix_title, parse_appendix


TEMPLATE_PATH = APP_ROOT / "arretify" / "templates" / "arrete.html"
TEMPLATE_HTML = open(TEMPLATE_PATH, "r", encoding="utf-8").read()


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
    lines = parse_main_content(soup, main_content, lines)

    if lines and is_appendix_title(lines[0].contents):
        appendix = make_data_tag(soup, APPENDIX_SCHEMA)
        body.append(appendix)
        parse_appendix(soup, appendix, lines)

    return soup
