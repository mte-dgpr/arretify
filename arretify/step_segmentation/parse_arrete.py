from arretify.types import ParsingContext
from arretify.html_schemas import (
    HEADER_SCHEMA,
    MAIN_SCHEMA,
    APPENDIX_SCHEMA,
)
from arretify.utils.html import make_data_tag
from .header import parse_header
from .main_content import parse_main_content
from .appendix import is_appendix_title, parse_appendix


def parse_arrete(parsing_context: ParsingContext) -> ParsingContext:
    body = parsing_context.soup.body
    assert body

    header = make_data_tag(parsing_context.soup, HEADER_SCHEMA)
    body.append(header)
    lines = parse_header(parsing_context.soup, header, parsing_context.lines)

    main_content = make_data_tag(parsing_context.soup, MAIN_SCHEMA)
    body.append(main_content)
    lines = parse_main_content(parsing_context.soup, main_content, lines)

    if lines and is_appendix_title(lines[0].contents):
        appendix = make_data_tag(parsing_context.soup, APPENDIX_SCHEMA)
        body.append(appendix)
        parse_appendix(parsing_context.soup, appendix, lines)

    return parsing_context
