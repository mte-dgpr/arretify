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
from typing import List, Tuple, Iterable, Iterator
import logging

from bs4 import BeautifulSoup, Tag

from arretify.types import TextSegment
from arretify.utils.functional import iter_func_to_list
from arretify.utils.html import (
    PageElementOrString,
    make_new_tag,
    make_data_tag,
    render_str_list_attribute,
)
from arretify.utils.markdown_parsing import (
    is_table_description,
    TABLE_HEADER_SEPARATOR_PATTERN,
    TABLE_LINE_PATTERN,
    IMAGE_PATTERN,
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
    apply_to_segment,
)
from .core import (
    Node,
    NodeOrText,
    Split,
    chain_flat_map_node_list,
    split_text_segments,
    make_single_line_splitter,
    make_while_splitter,
    map_splitted_text_segments,
    flat_map_splitted_text_segments,
    split_before_match,
    is_node,
    assert_single_text_segment,
    make_text_segment_probe_from_pattern,
)
from .document_elements import render_table_of_contents, render_page_footer, render_page_separator

_TableSplitterMatch = Tuple[List[NodeOrText], List[NodeOrText]]
_BlockquoteSplitterMatch = Tuple[List[NodeOrText], ErrorCodes | None]


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


_is_table = make_text_segment_probe_from_pattern(TABLE_LINE_PATTERN)
_is_not_table = make_text_segment_probe_from_pattern(TABLE_LINE_PATTERN, negate=True)
_is_image = make_text_segment_probe_from_pattern(IMAGE_PATTERN)
_is_list = make_text_segment_probe_from_pattern(LIST_PATTERN)
_is_blockquote_start = make_text_segment_probe_from_pattern(BLOCKQUOTE_START_PATTERN)
_is_blockquote_end = make_text_segment_probe_from_pattern(BLOCKQUOTE_END_PATTERN, use_search=True)


def list_indentation(line: str) -> int:
    list_match = LIST_PATTERN.match(line)
    if not list_match:
        raise ValueError("Expected line to be a list element")
    indentation = list_match.group("indentation")
    assert indentation is not None
    return len(indentation)


def _clean_leading_whitespaces(line: str) -> str:
    return LEADING_WHITESPACES_PATTERN.sub("", line)


def parse_images(
    input_list: List[NodeOrText],
) -> List[NodeOrText]:
    return map_splitted_text_segments(
        split_text_segments(
            input_list,
            make_single_line_splitter(_is_image),
        ),
        lambda pile: Node(type="image", children=pile),
    )


# TODO : deal with case :
# - bla
#     hello
#     hellu
# - bli
def parse_lists(
    input_list: List[NodeOrText],
) -> List[NodeOrText]:
    return map_splitted_text_segments(
        split_text_segments(
            input_list,
            make_while_splitter(_is_list),
        ),
        lambda pile: Node(type="list", children=pile),
    )


def parse_tables(
    input_list: List[NodeOrText],
) -> List[NodeOrText]:
    return flat_map_splitted_text_segments(
        split_text_segments(input_list, _table_splitter),
        _make_table_nodes,
    )


@iter_func_to_list
def _make_table_nodes(match: _TableSplitterMatch) -> Iterator[NodeOrText]:
    table_pile, table_description_pile = match
    yield Node(type="table", children=table_pile)
    if table_description_pile:
        yield Node(type="table_description", children=table_description_pile)


def _table_splitter(input_list: List[NodeOrText]) -> Split[NodeOrText, _TableSplitterMatch] | None:
    before, input_list = split_before_match(input_list, _is_table)
    table_pile, input_list = split_before_match(input_list, _is_not_table)
    if table_pile:
        table_lines: List[TextSegment] = []
        for element in table_pile:
            if isinstance(element, TextSegment):
                table_lines.append(element)
        table_description_pile, input_list = split_before_match(
            input_list,
            lambda t: isinstance(t, TextSegment)
            and not is_table_description(t.contents, [t.contents for t in table_lines]),
        )
        return before, (table_pile, table_description_pile), input_list
    else:
        return None


def parse_blockquotes(
    input_list: List[NodeOrText],
) -> List[NodeOrText]:
    return map_splitted_text_segments(
        split_text_segments(
            input_list,
            _blockquote_splitter,
        ),
        _make_blockquote_node,
    )


def _make_blockquote_node(match: _BlockquoteSplitterMatch) -> Node:
    pile, error_code = match
    if error_code is None:
        elements = chain_flat_map_node_list(pile, [parse_tables, parse_lists, parse_images])
        return Node(
            type="blockquote",
            children=list(elements),
        )
    else:
        return Node(
            type="error",
            children=pile,
            data=dict(error_codes=[error_code.value]),
        )


def _blockquote_splitter(
    input_list: List[NodeOrText],
) -> Split[NodeOrText, _BlockquoteSplitterMatch] | None:
    before, input_list = split_before_match(input_list, _is_blockquote_start)

    if not input_list:
        return None

    # At this point, we know that the first element is a blockquote start
    assert isinstance(input_list[0], TextSegment)
    opening_quote_start = input_list[0].start

    # Remove opening quote
    # TODO-PROCESS-TAG
    input_list[0] = apply_to_segment(
        input_list[0],
        lambda string: BLOCKQUOTE_START_PATTERN.sub("", string),
    )
    quotes_depth_count = 1

    for i, element in enumerate(input_list):
        if not isinstance(element, TextSegment):
            continue

        # Ignore case when the line contains a balanced number of quotes.
        # In that case, no need to increment or decrement as this will
        # be handled recursively.
        double_quotes_matches = list(DOUBLE_QUOTE_PATTERN.finditer(element.contents))
        if len(double_quotes_matches) % 2 == 0:
            pass
        else:
            if _is_blockquote_start(element):
                quotes_depth_count += 1
            if _is_blockquote_end(element):
                quotes_depth_count -= 1
            if quotes_depth_count <= 0:
                # Remove the end quote
                # TODO-PROCESS-TAG
                input_list[i] = apply_to_segment(
                    element,
                    lambda string: BLOCKQUOTE_END_PATTERN.sub("", string),
                )
                break

    if quotes_depth_count == 0:
        return before, (input_list[: i + 1], None), input_list[i + 1 :]
    else:
        _LOGGER.warning(f"Found unbalanced quote starting {opening_quote_start}")
        return before, (input_list[0:1], ErrorCodes.unbalanced_quote), input_list[1:]


def render_inline_quotes(soup: BeautifulSoup, string: str) -> Iterable[PageElementOrString]:
    return map_matches(
        split_string_with_regex(INLINE_QUOTE_PATTERN, string),
        lambda inline_quote_match: make_new_tag(
            soup,
            "q",
            contents=[str(inline_quote_match.group("quoted"))],
        ),
    )


def render_basic_elements(
    soup: BeautifulSoup,
    node: Node,
) -> Iterable[PageElementOrString]:
    if node.type == "list":
        yield render_list(soup, node)
    elif node.type == "table":
        yield render_table(soup, node)
    elif node.type == "table_description":
        yield from render_table_description(soup, node)
    elif node.type == "blockquote":
        yield from render_blockquote(soup, node)
    elif node.type == "table_of_contents":
        yield render_table_of_contents(soup, node)
    elif node.type == "page_footer":
        yield render_page_footer(soup, node)
    elif node.type == "image":
        yield render_image(soup, node)
    elif node.type == "error":
        yield render_error(soup, node)
    else:
        raise ValueError(f"Unknown node type '{node.type}' in render_basic_elements.")


def render_table(
    soup: BeautifulSoup,
    node: Node,
) -> Tag:
    pile: List[str] = []
    has_table_header = False
    inline_nodes: List[Tuple[int, Node]] = []
    for element in node.children:
        if isinstance(element, TextSegment):
            pile.append(element.contents)
            if bool(TABLE_HEADER_SEPARATOR_PATTERN.match(element.contents)):
                has_table_header = True
        elif is_node(element, type_in=["page_separator"]):
            table_tag = parse_markdown_table(pile)
            # Get the right table row for inserting the inline node.
            # If the table has a header, the `pile` contains a header
            # separation line (e.g. "|---|---|---|"), which is not
            # counting as a row in the final html table tag.
            row_index = len(pile) - 1 - int(has_table_header)
            inline_nodes.append((row_index, element))
        else:
            raise ValueError(f"Unexpected element type {type(element)} in table rendering.")

    table_tag = parse_markdown_table(pile)
    # Insert inline nodes in their corresponding table rows.
    table_rows = table_tag.find_all("tr")
    for row_index, inline_node in inline_nodes:
        if row_index < len(table_rows) and row_index >= 0:
            table_rows[row_index].select("td, th")[-1].append(
                render_page_separator(soup, inline_node)
            )
        else:
            raise ValueError(f"Invalid index {row_index} in table rendering. ")

    return table_tag


def render_table_description(
    soup: BeautifulSoup,
    node: Node,
) -> Iterable[PageElementOrString]:
    for element in node.children:
        if isinstance(element, TextSegment):
            yield soup.new_tag("br")
            yield element.contents
        elif is_node(element, type_in=["page_separator"]):
            yield render_page_separator(soup, element)
        else:
            raise ValueError(
                f"Unexpected element type {type(element)} in table description rendering."
            )


def render_list(
    soup: BeautifulSoup,
    node: Node,
) -> Tag:
    elements, ul = _render_list(soup, node.children)
    assert len(elements) == 0, "Expected all lines to be consumed in list rendering"
    return ul


def _render_list(
    soup: BeautifulSoup,
    elements: List[NodeOrText],
) -> Tuple[List[NodeOrText], Tag]:
    elements = list(elements)
    list_pile: List[Tag] = []
    assert isinstance(elements[0], TextSegment)
    ref_indentation = list_indentation(elements[0].contents)

    while elements:
        element = elements[0]
        current_indentation = list_indentation(element.contents)
        if current_indentation == ref_indentation:
            line = apply_to_segment(element, _clean_leading_whitespaces)
            elements.pop(0)
            list_pile.append(make_new_tag(soup, "li", contents=line.contents))

        elif current_indentation > ref_indentation:
            elements, nested_ul = _render_list(soup, elements)
            list_pile[-1].append(nested_ul)

        else:
            break

        if elements and is_node(elements[0], type_in=["page_separator"]):
            list_pile[-1].append(render_page_separator(soup, elements[0]))
            elements.pop(0)

    return elements, make_new_tag(soup, "ul", contents=list_pile)


def render_blockquote(
    soup: BeautifulSoup,
    node: Node,
) -> Iterable[PageElementOrString]:
    tag = soup.new_tag("blockquote")
    for element in node.children:
        if isinstance(element, Node):
            tag.extend(render_basic_elements(soup, element))
        else:
            # Parse inline quotes in the line
            # and add them as <q> tags
            tag.append(
                make_new_tag(soup, "p", contents=render_inline_quotes(soup, element.contents))
            )
    yield tag


def render_image(
    soup: BeautifulSoup,
    node: Node,
) -> Tag:
    return parse_markdown_image(assert_single_text_segment(node).contents)


def render_error(
    soup: BeautifulSoup,
    node: Node,
) -> Tag:
    return make_data_tag(
        soup,
        ERROR_SCHEMA,
        data=dict(error_codes=render_str_list_attribute(node.data["error_codes"])),
        contents=[assert_single_text_segment(node).contents],
    )
