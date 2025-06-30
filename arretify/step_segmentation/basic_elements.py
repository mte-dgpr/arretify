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

from bs4 import BeautifulSoup

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
    Node,
    NodeFlow,
    flat_map_node_flow,
    assert_single_text_segments,
    assert_single_text_segment,
    split_text_segments,
    make_single_line_splitter,
    make_while_splitter,
    map_splitted_text_segments,
    split_before_match,
)
from .document_elements import render_table_of_contents, render_page_footer


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


def parse_list_DEPRECATED(
    soup: BeautifulSoup, lines: TextSegments
) -> Tuple[TextSegments, PageElementOrString]:
    """
    DEPRECATED : kept only for compatibility with old segmentation code.
    Should be removed once migration is complete.
    """
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


def parse_images(
    lines: TextSegments,
) -> NodeFlow:
    return map_splitted_text_segments(
        split_text_segments(
            lines,
            make_single_line_splitter(lambda t: is_image(t.contents)),
        ),
        lambda text_segments: Node(type="image", children=[text_segments]),
    )


# TODO : deal with case :
# - bla
#     hello
#     hellu
# - bli
def parse_lists(
    lines: TextSegments,
) -> NodeFlow:
    return map_splitted_text_segments(
        split_text_segments(
            lines,
            make_while_splitter(lambda t: is_list(t.contents)),
        ),
        lambda text_segments: Node(type="list", children=[text_segments]),
    )


def parse_tables(
    lines: TextSegments,
) -> NodeFlow:
    lines = list(lines)
    while lines:
        pile, lines = split_before_match(lines, lambda t: is_table_line(t.contents))
        if pile:
            yield pile

        pile, lines = split_before_match(lines, lambda t: not is_table_line(t.contents))
        if pile:
            yield Node(type="table", children=[pile])
            pile, lines = split_before_match(
                lines, lambda t: not is_table_description(t.contents, [t.contents for t in pile])
            )
            if pile:
                yield Node(type="table_description", children=[pile])


def parse_blockquotes(
    lines: TextSegments,
) -> NodeFlow:
    lines = list(lines)
    pile: TextSegments = []
    while lines:
        pile, lines = split_before_match(lines, lambda t: is_blockquote_start(t.contents))
        if pile:
            yield pile
            pile = []

        if not lines:
            break

        # At this point, we know that the first line is a blockquote start
        opening_quote_start = lines[0].start

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
            children = flat_map_node_flow([pile], parse_tables)
            children = flat_map_node_flow(children, parse_lists)
            children = flat_map_node_flow(children, parse_images)
            yield Node(
                type="blockquote",
                children=list(children),
            )
            pile = []
        else:
            yield Node(
                type="error",
                children=[[pile[0]]],
                data=dict(error_codes=[ErrorCodes.unbalanced_quote.value]),
            )
            _LOGGER.warning(f"Found unbalanced quote starting {opening_quote_start}")

            # Put back all the lines except the one raising the error into the pile
            while len(pile) > 1:
                lines.append(pile.pop(1))
            pile = []


def render_inline_quotes(soup: BeautifulSoup, string: str) -> Iterable[PageElementOrString]:
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
    node: Node,
) -> Iterable[PageElementOrString]:
    if node.type == "list":
        yield from render_list(soup, node)
    elif node.type == "table":
        yield from render_table(soup, node)
    elif node.type == "table_description":
        yield from render_table_description(soup, node)
    elif node.type == "blockquote":
        yield from render_blockquote(soup, node)
    elif node.type == "table_of_contents":
        yield render_table_of_contents(soup, node)
    elif node.type == "page_footer":
        yield render_page_footer(soup, node)
    elif node.type == "image":
        yield from render_image(soup, node)
    elif node.type == "error":
        yield from render_error(soup, node)
    else:
        raise ValueError(f"Unknown node type '{node.type}' in render_basic_elements.")


def render_table(
    soup: BeautifulSoup,
    node: Node,
) -> Iterable[PageElementOrString]:
    yield parse_markdown_table([t.contents for t in assert_single_text_segments(node)])


def render_table_description(
    soup: BeautifulSoup,
    node: Node,
) -> Iterable[PageElementOrString]:
    text_segments = assert_single_text_segments(node)
    for line in text_segments:
        yield soup.new_tag("br")
        yield line.contents


def render_list(
    soup: BeautifulSoup,
    node: Node,
) -> Iterable[PageElementOrString]:
    lines, ul = _render_list(soup, assert_single_text_segments(node))
    assert len(lines) == 0, "Expected all lines to be consumed in list rendering"
    yield ul


def _render_list(
    soup: BeautifulSoup,
    lines: TextSegments,
) -> Tuple[TextSegments, PageElementOrString]:
    lines = list(lines)
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
    node: Node,
) -> Iterable[PageElementOrString]:
    tag = soup.new_tag("blockquote")
    for node_or_text_segments in node.children:
        if isinstance(node_or_text_segments, Node):
            tag.extend(render_basic_elements(soup, node_or_text_segments))
        else:
            for line in node_or_text_segments:
                # Parse inline quotes in the line
                # and add them as <q> tags
                tag.append(
                    make_new_tag(soup, "p", contents=render_inline_quotes(soup, line.contents))
                )
    yield tag


def render_image(
    soup: BeautifulSoup,
    node: Node,
) -> Iterable[PageElementOrString]:
    yield parse_markdown_image(assert_single_text_segment(node).contents)


# TODO : parametrize the error codes
def render_error(
    soup: BeautifulSoup,
    node: Node,
) -> Iterable[PageElementOrString]:
    text_segment = assert_single_text_segment(node)
    yield make_data_tag(
        soup,
        ERROR_SCHEMA,
        data=dict(error_codes=render_str_list_attribute([ErrorCodes.unbalanced_quote.value])),
        contents=[text_segment.contents],
    )
