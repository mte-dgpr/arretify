from arretify.types import ParsingContext
from arretify.html_schemas import (
    HEADER_SCHEMA,
    MAIN_SCHEMA,
    APPENDIX_SCHEMA,
)
from arretify.utils.html import make_data_tag
from .header import parse_header
from .content import parse_content


def parse_arrete(parsing_context: ParsingContext) -> ParsingContext:
    body = parsing_context.soup.body
    assert body

    lines = parsing_context.lines

    if lines:
        header = make_data_tag(parsing_context.soup, HEADER_SCHEMA)
        body.append(header)
        lines = parse_header(parsing_context.soup, header, lines)

    if lines:
        main_content = make_data_tag(parsing_context.soup, MAIN_SCHEMA)
        body.append(main_content)
        lines = parse_content(parsing_context.soup, main_content, lines, exit_on_appendix=True)

    if lines:
        appendix = make_data_tag(parsing_context.soup, APPENDIX_SCHEMA)
        body.append(appendix)
        lines = parse_content(parsing_context.soup, appendix, lines, exit_on_appendix=False)

    return parsing_context
