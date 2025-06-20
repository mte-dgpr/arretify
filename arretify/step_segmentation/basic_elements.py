#
# Copyright (c) 2025 Direction générale de la prévention des risques (DGPR).
#
# This file is part of Arrêtify.
# See https://github.com/mte-dgpr/arretify for further info.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from typing import List, Tuple, Iterable
import logging

from bs4 import BeautifulSoup, Tag

from arretify.utils.html import (
    PageElementOrString,
    make_ul,
    make_li,
    make_new_tag,
    make_data_tag,
    render_str_list_attribute,
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
from .core import (
    Element,
    ElementFlow,
    flat_map_element_flow,
    assert_single_text_segments,
    assert_single_text_segment,
)


LEADING_WHITESPACES_PATTERN = PatternProxy(r"^\s+")
"""Detect leading whitespaces."""

BLOCKQUOTE_START_PATTERN = PatternProxy(r"^\s*\"")
"""Detect if a sentence starts with a quote '"'."""

BLOCKQUOTE_END_PATTERN = PatternProxy(r"\"[\s\.]*$")
"""Detect if a sentence ends with a quote '"'."""

INLINE_QUOTE_PATTERN = PatternProxy(r'"(?P<quoted>[^"]+)"')
"""Detect if a sentence has inline quotes."""

DOUBLE_QUOTE_PATTERN = PatternProxy(r'"')
"""Basic double quote '"' pattern."""


_LOGGER = logging.getLogger(__name__)


def list_indentation(line: str) -> int:
    list_match = LIST_PATTERN.match(line)
    if not list_match:
        raise ValueError("Expected line to be a list element")
    indentation = list_match.group("indentation")
    assert indentation is not None
    return len(indentation)


def _clean_leading_whitespaces(line: str) -> str:
    return LEADING_WHITESPACES_PATTERN.sub("", line)


def is_blockquote_start(line: str) -> bool:
    return bool(BLOCKQUOTE_START_PATTERN.search(line))


def is_blockquote_end(line: str) -> bool:
    return bool(BLOCKQUOTE_END_PATTERN.search(line))


def parse_basic_elements_DEPRECATED(
    soup: BeautifulSoup,
    lines: TextSegments,
) -> Iterable[PageElementOrString]:
    for element_or_text_segments in parse_basic_elements(lines):
        if isinstance(element_or_text_segments, Element):
            yield from render_basic_elements(soup, element_or_text_segments)
        else:
            for line in element_or_text_segments:
                yield from _parse_inline_quotes(soup, lines.pop(0).contents)


def parse_list_DEPRECATED(
    soup: BeautifulSoup, lines: TextSegments
) -> Tuple[TextSegments, PageElementOrString]:
    list_pile: List[PageElementOrString] = []
    ref_indentation = list_indentation(lines[0].contents)

    while lines and is_list(lines[0].contents):
        current_indentation = list_indentation(lines[0].contents)
        if current_indentation == ref_indentation:
            line = apply_to_segment(lines.pop(0), _clean_leading_whitespaces)
            list_pile.append(line.contents)

        elif current_indentation > ref_indentation:
            lines, nested_ul = parse_list_DEPRECATED(soup, lines)
            li = make_li(soup, [list_pile.pop(), nested_ul])
            list_pile.append(li)

        else:
            break

    return lines, make_ul(soup, list_pile)


def parse_basic_elements(
    lines: TextSegments,
    should_parse_blockquotes: bool = True,
) -> ElementFlow:
    element_flow: ElementFlow = [lines]
    if should_parse_blockquotes:
        element_flow = flat_map_element_flow(element_flow, parse_blockquotes)
    element_flow = flat_map_element_flow(element_flow, parse_tables)
    element_flow = flat_map_element_flow(element_flow, parse_lists)
    element_flow = flat_map_element_flow(element_flow, parse_images)
    yield from element_flow


def parse_images(
    lines: TextSegments,
) -> ElementFlow:
    pile: TextSegments = []
    while lines:
        while lines and not is_image(lines[0].contents):
            pile.append(lines.pop(0))
        if pile:
            yield pile
            pile = []

        if lines:
            yield Element(name="image", contents=[[lines.pop(0)]])


# TODO : deal with case :
# - bla
#     hello
#     hellu
# - bli
def parse_lists(
    lines: TextSegments,
) -> ElementFlow:
    pile: TextSegments = []

    while lines:
        while lines and not is_list(lines[0].contents):
            pile.append(lines.pop(0))
        if pile:
            yield pile
            pile = []

        while lines and is_list(lines[0].contents):
            pile.append(lines.pop(0))
        if pile:
            yield Element(name="list", contents=[pile])
            pile = []


def parse_tables(
    lines: TextSegments,
) -> ElementFlow:
    pile: TextSegments = []
    table_pile: TextSegments = []

    while lines:
        pile = []
        while lines and not is_table_line(lines[0].contents):
            pile.append(lines.pop(0))
        if pile:
            yield pile

        pile = []
        while lines and is_table_line(lines[0].contents):
            pile.append(lines.pop(0))
        if pile:
            yield Element(name="table", contents=[pile])

        table_pile = pile
        pile = []
        while lines and is_table_description(lines[0].contents, [t.contents for t in table_pile]):
            pile.append(lines.pop(0))
        if pile:
            yield Element(name="table_description", contents=[pile])


def parse_blockquotes(
    lines: TextSegments,
) -> ElementFlow:
    pile: TextSegments = []
    while lines:
        while lines and not is_blockquote_start(lines[0].contents):
            pile.append(lines.pop(0))
        if pile:
            yield pile
            pile = []

        if not lines:
            break

        # At this point, we know that the first line is a blockquote start
        lines[0].start
        # Remove opening quote
        # TODO-PROCESS-TAG
        lines[0] = apply_to_segment(
            lines[0],
            lambda string: BLOCKQUOTE_START_PATTERN.sub("", string),
        )
        quotes_depth_count = 1

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

        if quotes_depth_count == 0:
            yield Element(
                name="blockquote",
                contents=list(parse_basic_elements(pile, should_parse_blockquotes=False)),
            )
        else:
            yield Element(
                name="error",
                contents=[[pile[0]]],
            )
            yield pile[1:]


def _parse_inline_quotes(soup: BeautifulSoup, string: str) -> Iterable[PageElementOrString]:
    return map_matches(
        split_string_with_regex(INLINE_QUOTE_PATTERN, string),
        lambda inline_quote_match: make_new_tag(
            soup,
            "q",
            contents=[str(inline_quote_match.group("quoted"))],
        ),
    )


def parse_list(
    soup: BeautifulSoup, lines: TextSegments
) -> Tuple[TextSegments, PageElementOrString]:
    return (lines, "bla")


def render_basic_elements(
    soup: BeautifulSoup,
    element: Element,
) -> Iterable[PageElementOrString]:
    if element.name == "list":
        yield from render_list(soup, element)
    elif element.name == "table":
        yield from render_table(soup, element)
    elif element.name == "table_description":
        yield from render_table_description(soup, element)
    elif element.name == "blockquote":
        yield from render_blockquote(soup, element)
    elif element.name == "image":
        yield from render_image(soup, element)
    elif element.name == "error":
        yield from render_error(soup, element)
    else:
        raise ValueError(
            f"Unknown element name '{element.name}' in render_basic_elements. "
            f"Expected one of: 'list', 'table', 'table_description', 'blockquote', 'image', 'error'."
        )


def render_table(
    soup: BeautifulSoup,
    element: Element,
) -> Iterable[PageElementOrString]:
    yield parse_markdown_table([t.contents for t in assert_single_text_segments(element)])


def render_table_description(
    soup: BeautifulSoup,
    element: Element,
) -> Iterable[PageElementOrString]:
    text_segments = assert_single_text_segments(element)
    for line in text_segments:
        yield soup.new_tag("br")
        yield line.contents


def render_list(
    soup: BeautifulSoup,
    element: Element,
) -> Iterable[PageElementOrString]:
    lines, ul = _render_list(soup, assert_single_text_segments(element))
    assert len(lines) == 0, "Expected all lines to be consumed in list rendering"
    yield ul


def _render_list(
    soup: BeautifulSoup,
    lines: TextSegments,
) -> Tuple[TextSegments, PageElementOrString]:
    list_pile: List[PageElementOrString] = []
    ref_indentation = list_indentation(lines[0].contents)

    while lines and is_list(lines[0].contents):
        current_indentation = list_indentation(lines[0].contents)
        if current_indentation == ref_indentation:
            line = apply_to_segment(lines.pop(0), _clean_leading_whitespaces)
            list_pile.append(line.contents)

        elif current_indentation > ref_indentation:
            lines, nested_ul = _render_list(soup, lines)
            li = make_li(soup, [list_pile.pop(), nested_ul])
            list_pile.append(li)

        else:
            break

    return lines, make_ul(soup, list_pile)


def render_blockquote(
    soup: BeautifulSoup,
    element: Element,
) -> Iterable[PageElementOrString]:
    tag = soup.new_tag("blockquote")
    for element_or_text_segments in element.contents:
        if isinstance(element_or_text_segments, Element):
            tag.extend(render_basic_elements(soup, element_or_text_segments))
        else:
            for line in element_or_text_segments:
                # Parse inline quotes in the line
                # and add them as <q> tags
                tag.append(
                    make_new_tag(soup, "p", contents=_parse_inline_quotes(soup, line.contents))
                )
            # children = _parse_all_inline_elements(soup, lines.pop(0).contents)
            # container.extend(render_default(children))
            # yield lines.pop(0)
    yield tag


def render_image(
    soup: BeautifulSoup,
    element: Element,
) -> Iterable[PageElementOrString]:
    yield parse_markdown_image(assert_single_text_segment(element).contents)


# TODO : parametrize the error codes
def render_error(
    soup: BeautifulSoup,
    element: Element,
) -> Iterable[PageElementOrString]:
    text_segment = assert_single_text_segment(element)
    yield make_data_tag(
        soup,
        ERROR_SCHEMA,
        data=dict(error_codes=render_str_list_attribute([ErrorCodes.unbalanced_quote.value])),
        contents=[text_segment.contents],
    )
