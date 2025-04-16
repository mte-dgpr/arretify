import re
from typing import List, Tuple, Callable, Iterable

from bs4 import BeautifulSoup, Tag

from arretify.settings import LOGGER
from arretify.utils.html import (
    PageElementOrString,
    make_ul,
    make_li,
    make_new_tag,
    make_data_tag,
)
from arretify.utils.markdown_parsing import (
    is_table_line,
    is_table_description,
    is_list,
    is_image,
    LIST_PATTERN,
    parse_markdown_table,
    parse_markdown_image,
)
from arretify.regex_utils import (
    PatternProxy,
)
from arretify.errors import ErrorCodes
from arretify.html_schemas import ERROR_SCHEMA
from arretify.regex_utils import split_string_with_regex
from arretify.regex_utils import map_matches
from arretify.parsing_utils.source_mapping import (
    TextSegments,
    apply_to_segment,
)


BULLET_LIST_RE = re.compile(r"^\s*-\s*")
"""Detect if a sentence starts with a bullet list."""

BLOCKQUOTE_START_PATTERN = PatternProxy(r"^\s*\"")
"""Detect if a sentence starts with a quote '"'."""

BLOCKQUOTE_END_PATTERN = PatternProxy(r"\"[\s\.]*$")
"""Detect if a sentence ends with a quote '"'."""

INLINE_QUOTE_PATTERN = PatternProxy(r'"(?P<quoted>[^"]+)"')
"""Detect if a sentence has inline quotes."""

DOUBLE_QUOTE_PATTERN = PatternProxy(r'"')
"""Basic double quote '"' pattern."""


def list_indentation(line: str) -> int:
    list_match = LIST_PATTERN.match(line)
    if not list_match:
        raise ValueError("Expected line to be a list element")
    indentation = list_match.group("indentation")
    assert indentation is not None
    return len(indentation)


def _clean_bullet_list(line: str) -> str:
    return BULLET_LIST_RE.sub("", line)


def is_blockquote_start(line: str) -> bool:
    return bool(BLOCKQUOTE_START_PATTERN.search(line))


def is_blockquote_end(line: str) -> bool:
    return bool(BLOCKQUOTE_END_PATTERN.search(line))


def parse_basic_elements(
    soup: BeautifulSoup,
    container: Tag,
    lines: TextSegments,
    render_default: Callable[
        [Iterable[PageElementOrString]], Iterable[PageElementOrString]
    ] = lambda elements: elements,
):
    if is_table_line(lines[0].contents):
        lines, table_elements = parse_table(soup, lines)
        container.extend(table_elements)

    elif is_list(lines[0].contents):
        lines, ul_element = parse_list(soup, lines)
        container.append(ul_element)

    elif is_blockquote_start(lines[0].contents):
        lines, blockquote_or_error_element = parse_blockquote(soup, lines)
        container.append(blockquote_or_error_element)

    elif is_image(lines[0].contents):
        image_element = parse_markdown_image(lines.pop(0).contents)
        container.append(image_element)

    # Normal paragraph
    else:
        children = _parse_all_inline_elements(soup, lines.pop(0).contents)
        container.extend(render_default(children))


# TODO : deal with case :
# - bla
#     hello
#     hellu
# - bli
def parse_list(
    soup: BeautifulSoup, lines: TextSegments
) -> Tuple[TextSegments, PageElementOrString]:
    list_pile: List[PageElementOrString] = []
    ref_indentation = list_indentation(lines[0].contents)

    while lines and is_list(lines[0].contents):
        current_indentation = list_indentation(lines[0].contents)
        if current_indentation == ref_indentation:
            line = apply_to_segment(lines.pop(0), _clean_bullet_list)
            list_pile.append(line.contents)

        elif current_indentation > ref_indentation:
            lines, nested_ul = parse_list(soup, lines)
            li = make_li(soup, [list_pile.pop(), nested_ul])
            list_pile.append(li)

        else:
            break

    return lines, make_ul(soup, list_pile)


def parse_table(
    soup: BeautifulSoup,
    lines: TextSegments,
) -> Tuple[TextSegments, List[PageElementOrString]]:
    pile: List[PageElementOrString] = []
    elements: List[PageElementOrString] = []

    while lines and is_table_line(lines[0].contents):
        pile.append(lines.pop(0).contents)
    elements.append(parse_markdown_table(pile))

    while lines and is_table_description(lines[0].contents, pile):
        elements.append(soup.new_tag("br"))
        elements.append(lines.pop(0).contents)

    return lines, elements


def parse_blockquote(soup: BeautifulSoup, lines: TextSegments) -> Tuple[TextSegments, Tag]:
    if not is_blockquote_start(lines[0].contents):
        raise RuntimeError("Expected block quote start")

    blockquote = soup.new_tag("blockquote")
    opening_quote_start = lines[0].start
    # Remove opening quote
    # TODO-PROCESS-TAG
    lines[0] = apply_to_segment(
        lines[0],
        lambda string: BLOCKQUOTE_START_PATTERN.sub("", string),
    )

    # In order to capture nested quotes, we keep track of the quotes depth.
    # +1 for each opening quote, -1 for each closing quote.
    # When 0 is reached, we have reached the end of the blockquote.
    # Then the whole content gathered is parsed recursively for other basic elements.
    quotes_depth_count = 1
    pile: TextSegments = []
    while lines and quotes_depth_count > 0:
        # Ignore case when the line contains a balanced number of quotes.
        # In that case, no need to increment or decrement as this will
        # be handled recursively.
        double_quotes_matches = list(DOUBLE_QUOTE_PATTERN.finditer(lines[0].contents))
        if len(double_quotes_matches) % 2 == 0:
            pass
        else:
            if is_blockquote_start(lines[0].contents):
                quotes_depth_count += 1
            if is_blockquote_end(lines[0].contents):
                quotes_depth_count -= 1
        pile.append(lines.pop(0))

    # Remove the end quote
    # TODO-PROCESS-TAG
    pile[-1] = apply_to_segment(
        pile[-1],
        lambda string: BLOCKQUOTE_END_PATTERN.sub("", string),
    )

    if quotes_depth_count > 0:
        LOGGER.warn(f"Found unbalanced quote starting {opening_quote_start}")
        error_element = make_data_tag(
            soup,
            ERROR_SCHEMA,
            data=dict(error_code=ErrorCodes.unbalanced_quote.value),
            contents=[pile[0].contents],
        )
        # Put back all the lines except the one raising the error into the pile
        while len(pile) > 1:
            lines.append(pile.pop(1))
        return lines, error_element

    _parse_all_basic_elements(
        soup,
        blockquote,
        pile,
    )

    return lines, blockquote


def _parse_inline_quotes(soup: BeautifulSoup, string: str) -> Iterable[PageElementOrString]:
    return map_matches(
        split_string_with_regex(INLINE_QUOTE_PATTERN, string),
        lambda inline_quote_match: make_new_tag(
            soup,
            "q",
            contents=[str(inline_quote_match.group("quoted"))],
        ),
    )


def _parse_all_inline_elements(soup: BeautifulSoup, string: str) -> List[PageElementOrString]:
    return list(_parse_inline_quotes(soup, string))


def _parse_all_basic_elements(
    soup: BeautifulSoup,
    container: Tag,
    lines: TextSegments,
):
    while lines:
        parse_basic_elements(
            soup,
            container,
            lines,
            lambda children: [make_new_tag(soup, "p", contents=children)],
        )
    return lines
