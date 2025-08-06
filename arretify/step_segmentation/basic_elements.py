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
from arretify.parsing_utils.patterns import is_continuing_sentence
from arretify.utils.functional import iter_func_to_list, chain_functions
from arretify.utils.html import (
    PageElementOrString,
    render_str_list_attribute,
)
from arretify.utils.html_create import make_data_tag, make_new_tag
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
from arretify.utils.split_merge import (
    Probe,
    RawSplit,
    split_elements,
    map_splitted_elements,
    flat_map_splitted_elements,
    split_before_match,
    negate,
)

from .core import (
    Node,
    NodeOrText,
    is_node,
    make_single_line_splitter_for_text_span_nodes,
    get_string,
    get_strings,
    combine_text_spans,
    make_probe_from_pattern_proxy,
    pick_text_span_node,
    pick_if_inline_node_followed_by_match,
)
from .document_elements import render_table_of_contents, render_page_footer, render_page_separator


_LOGGER = logging.getLogger(__name__)


# -------------------- Tables -------------------- #
_TableSplitterMatch = Tuple[List[NodeOrText], List[NodeOrText]]
"""
A match for the table splitter, in the form `(<table_elements>, <table_description_elements>)`.
"""

_is_table = make_probe_from_pattern_proxy(TABLE_LINE_PATTERN)
_is_table_start = pick_text_span_node(_is_table)
_is_table_end = negate(pick_if_inline_node_followed_by_match(pick_text_span_node(_is_table)))


def _make_table_description_end_probe(table_lines: List[str]) -> Probe[NodeOrText]:
    def _is_table_description(elements: List[NodeOrText], index: int) -> bool:
        if is_table_description(get_string(elements[index]), table_lines):
            return True
        return False

    return negate(pick_text_span_node(_is_table_description))


def parse_tables(
    input_list: List[NodeOrText],
) -> List[NodeOrText]:
    return flat_map_splitted_elements(
        split_elements(input_list, _table_splitter),
        _make_table_nodes,
    )


@iter_func_to_list
def _make_table_nodes(match: _TableSplitterMatch) -> Iterator[NodeOrText]:
    table_pile, table_description_pile = match
    yield Node(type="table", children=table_pile)
    if table_description_pile:
        yield Node(type="table_description", children=table_description_pile)


def _table_splitter(
    input_list: List[NodeOrText],
) -> RawSplit[NodeOrText, _TableSplitterMatch] | None:
    before, input_list = split_before_match(input_list, _is_table_start)
    table_pile, input_list = split_before_match(input_list, _is_table_end)

    if table_pile:
        # Directly after table end, look for table description.
        table_description_pile, input_list = split_before_match(
            input_list,
            _make_table_description_end_probe(get_strings(table_pile)),
        )

        return (
            before,
            (
                table_pile,
                table_description_pile,
            ),
            input_list,
        )
    else:
        return None


def render_table(
    soup: BeautifulSoup,
    node: Node,
) -> Tag:
    pile: List[str] = []
    has_table_header = False
    inline_nodes: List[Tuple[int, Node]] = []
    for element in node.children:
        if is_node(element, type_in=["text_span"]):
            element_str = get_string(element)
            pile.append(element_str)
            if bool(TABLE_HEADER_SEPARATOR_PATTERN.match(element_str)):
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
        if is_node(element, type_in=["text_span"]):
            yield soup.new_tag("br")
            yield get_string(element)
        elif is_node(element, type_in=["page_separator"]):
            yield render_page_separator(soup, element)
        else:
            raise ValueError(
                f"Unexpected element type {type(element)} in table description rendering."
            )


# -------------------- Lists -------------------- #
LEADING_WHITESPACES_PATTERN = PatternProxy(r"^\s+")
"""Detect leading whitespaces."""

_is_list_element = make_probe_from_pattern_proxy(LIST_PATTERN)
_is_list_start = pick_text_span_node(_is_list_element)
_is_list_continuation = pick_if_inline_node_followed_by_match(pick_text_span_node(_is_list_element))


def _list_indentation(line: str) -> int:
    list_match = LIST_PATTERN.match(line)
    if not list_match:
        raise ValueError("Expected line to be a list element")
    indentation = list_match.group("indentation")
    assert indentation is not None
    return len(indentation)


def _clean_leading_whitespaces(line: str) -> str:
    return LEADING_WHITESPACES_PATTERN.sub("", line)


def _list_splitter(
    elements: List[NodeOrText],
) -> RawSplit[NodeOrText, List[NodeOrText]] | None:
    """
    Split the input list into piles of list elements.
    Each pile is a list of elements that are part of the same list.
    """
    before, elements = split_before_match(elements, _is_list_start)

    if not elements:
        return None

    pile: List[NodeOrText] = []
    while elements:
        element = elements[0]

        # This will pick either a list element, or an inline tag (e.g. page separator)
        # that is followed by a list element.
        if _is_list_continuation(elements, 0):
            pile.append(elements.pop(0))

        # If we get a line that does not match the list pattern,
        # we check if it continues the previous sentence.
        elif is_node(element, type_in=["text_span"]):
            # First get the previous list element in the pile.
            j = len(pile) - 1
            while j >= 0 and not is_node(pile[j], type_in=["text_span"]):
                j -= 1
            if j < 0:
                raise RuntimeError("Expected to find a list element in the pile.")
            previous_list_element = pile[j]

            if is_continuing_sentence(
                get_string(previous_list_element),
                get_string(element),
            ):
                pile[j] = combine_text_spans([*pile[j:], elements.pop(0)])
            else:
                break

        else:
            break

    return before, pile, elements


# TODO : deal with case :
# - bla
#     hello
#     hellu
# - bli
def parse_lists(
    input_list: List[NodeOrText],
) -> List[NodeOrText]:
    return map_splitted_elements(
        split_elements(
            input_list,
            _list_splitter,
        ),
        lambda pile: Node(type="list", children=pile),
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
    element = elements[0]
    ref_indentation = _list_indentation(get_string(element))

    while elements:
        element = elements[0]

        if is_node(element, type_in=["page_separator"]):
            list_pile[-1].append(render_page_separator(soup, element))
            elements.pop(0)

        elif is_node(element, type_in=["text_span", "text_span"]):
            current_indentation = _list_indentation(get_string(element))

            if current_indentation == ref_indentation:
                li_contents = list(render_text_span(soup, element))
                if isinstance(li_contents[0], str):
                    li_contents[0] = _clean_leading_whitespaces(li_contents[0])
                list_pile.append(make_new_tag(soup, "li", contents=li_contents))
                elements.pop(0)

            elif current_indentation > ref_indentation:
                elements, nested_ul = _render_list(soup, elements)
                list_pile[-1].append(nested_ul)

            # If the indentation is less than the reference indentation,
            # we exit the function and go up one level.
            else:
                break

        else:
            raise ValueError(f"Unexpected element {element} in list rendering.")

    return elements, make_new_tag(soup, "ul", contents=list_pile)


# -------------------- Blockquotes -------------------- #
_BlockquoteSplitterMatch = Tuple[List[NodeOrText], ErrorCodes | None]
"""
A match for the blockquote splitter, in the form `(<blockquote_elements>, <error_codes>)`.
"""

BLOCKQUOTE_START_PATTERN = PatternProxy(r"^\s*\"")
"""Detect if a sentence starts with a quote '"'."""

BLOCKQUOTE_END_PATTERN = PatternProxy(r"\"[\s\.]*$")
"""Detect if a sentence ends with a quote '"'."""

DOUBLE_QUOTE_PATTERN = PatternProxy(r'"')
"""Basic double quote '"' pattern."""


_is_blockquote_start = pick_text_span_node(make_probe_from_pattern_proxy(BLOCKQUOTE_START_PATTERN))
_is_blockquote_end = pick_text_span_node(
    make_probe_from_pattern_proxy(BLOCKQUOTE_END_PATTERN, use_search=True)
)


def parse_blockquotes(
    input_list: List[NodeOrText],
) -> List[NodeOrText]:
    return map_splitted_elements(
        split_elements(
            input_list,
            _blockquote_splitter,
        ),
        _make_blockquote_node,
    )


def _make_blockquote_node(match: _BlockquoteSplitterMatch) -> Node:
    pile, error_code = match
    if error_code is None:
        children = chain_functions(pile, [parse_tables, parse_lists, parse_images])
        return Node(
            type="blockquote",
            children=children,
        )
    else:
        return Node(
            type="error",
            children=pile,
            data=dict(error_codes=[error_code.value]),
        )


def _blockquote_splitter(
    input_list: List[NodeOrText],
) -> RawSplit[NodeOrText, _BlockquoteSplitterMatch] | None:
    before, input_list = split_before_match(input_list, _is_blockquote_start)

    if not input_list:
        return None

    # At this point, we know that the first element is a blockquote start
    element = input_list[0]
    assert is_node(element, type_in=["text_span"])
    first_text_segment_index, first_text_segment = _get_first_text_segment(element)
    # Remove opening quote
    # TODO-PROCESS-TAG
    element.children[first_text_segment_index] = apply_to_segment(
        first_text_segment,
        lambda string: BLOCKQUOTE_START_PATTERN.sub("", string),
    )
    quotes_depth_count = 1

    for i, element in enumerate(input_list):
        if not is_node(element, type_in=["text_span"]):
            continue

        # Ignore case when the line contains a balanced number of quotes.
        # In that case, no need to increment or decrement as this will
        # be handled recursively.
        double_quotes_matches = list(DOUBLE_QUOTE_PATTERN.finditer(get_string(element)))
        if len(double_quotes_matches) % 2 == 0:
            pass
        else:
            if _is_blockquote_start(input_list, i):
                quotes_depth_count += 1
            if _is_blockquote_end(input_list, i):
                quotes_depth_count -= 1
            if quotes_depth_count <= 0:
                last_text_segment_index, last_text_segment = _get_last_text_segment(element)
                # Remove the end quote
                # TODO-PROCESS-TAG
                element.children[last_text_segment_index] = apply_to_segment(
                    last_text_segment,
                    lambda string: BLOCKQUOTE_END_PATTERN.sub("", string),
                )
                break

    if quotes_depth_count == 0:
        # Last line should be included, so we take `i + 1`
        return before, (input_list[: i + 1], None), input_list[i + 1 :]
    else:
        _LOGGER.warning(f"Found unbalanced quote starting {first_text_segment.start}")
        return before, (input_list[0:1], ErrorCodes.unbalanced_quote), input_list[1:]


def _get_first_text_segment(
    text_span_node: Node,
) -> Tuple[int, TextSegment]:
    for i, element in enumerate(text_span_node.children):
        if isinstance(element, TextSegment):
            return i, element
    raise ValueError("No text segment found.")


def _get_last_text_segment(
    text_span_node: Node,
) -> Tuple[int, TextSegment]:
    for i, element in enumerate(reversed(text_span_node.children)):
        if isinstance(element, TextSegment):
            return len(text_span_node.children) - 1 - i, element
    raise ValueError("No text segment found.")


def render_blockquote(
    soup: BeautifulSoup,
    node: Node,
) -> Iterable[PageElementOrString]:
    tag = soup.new_tag("blockquote")
    for element in node.children:
        if is_node(element, type_in=["text_span"]):
            tag.append(
                make_new_tag(
                    soup,
                    "p",
                    # TODO : should be parsed like other nodes, instead of being
                    # rendered here on the fly. This would also make parsing blockquote easier.
                    contents=render_inline_quotes(soup, get_string(element)),
                )
            )
        elif is_node(element):
            tag.extend(render_basic_elements(soup, element))

    yield tag


# -------------------- Images -------------------- #
_is_image = make_probe_from_pattern_proxy(IMAGE_PATTERN)


def parse_images(
    input_list: List[NodeOrText],
) -> List[NodeOrText]:
    return map_splitted_elements(
        split_elements(
            input_list,
            make_single_line_splitter_for_text_span_nodes(_is_image),
        ),
        lambda children: Node(type="image", children=children),
    )


def render_image(
    soup: BeautifulSoup,
    node: Node,
) -> Tag:
    return parse_markdown_image(get_string(node))


# -------------------- Misc -------------------- #
INLINE_QUOTE_PATTERN = PatternProxy(r'"(?P<quoted>[^"]+)"')
"""Detect if a sentence has inline quotes."""


def render_inline_quotes(soup: BeautifulSoup, string: str) -> Iterable[PageElementOrString]:
    return map_matches(
        split_string_with_regex(INLINE_QUOTE_PATTERN, string),
        lambda inline_quote_match: make_new_tag(
            soup,
            "q",
            contents=[str(inline_quote_match.group("quoted"))],
        ),
    )


def render_text_span(
    soup: BeautifulSoup,
    node: Node,
) -> Iterator[PageElementOrString]:
    for i, element in enumerate(node.children):
        if isinstance(element, TextSegment):
            # If this is not the last element, we add a space as separator.
            yield element.contents + " " * int(i < len(node.children) - 1)
        elif is_node(element, type_in=["page_separator"]):
            yield render_page_separator(soup, element)
        else:
            raise ValueError(f"Unexpected element type {type(element)} in text span rendering.")


def render_basic_elements(
    soup: BeautifulSoup,
    node: Node,
) -> Iterator[PageElementOrString]:
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
    elif node.type == "page_separator":
        yield render_page_separator(soup, node)
    elif node.type == "image":
        yield render_image(soup, node)
    elif node.type == "error":
        yield render_error(soup, node)
    elif node.type == "text_span":
        yield from render_text_span(soup, node)
    else:
        raise ValueError(f"Unknown node type '{node.type}' in render_basic_elements.")


def render_error(
    soup: BeautifulSoup,
    node: Node,
) -> Tag:
    return make_data_tag(
        soup,
        ERROR_SCHEMA,
        data=dict(error_codes=render_str_list_attribute(node.data["error_codes"])),
        contents=[get_string(n) for n in node.children],
    )
