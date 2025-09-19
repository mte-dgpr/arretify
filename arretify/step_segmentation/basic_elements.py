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
from typing import List, Sequence, Tuple, Iterator, cast
import logging

from bs4 import Tag

from arretify.parsing_utils.patterns import is_continuing_sentence
from arretify.types import DocumentContext, PageElementOrString
from arretify.utils.functional import iter_func_to_list, chain_functions
from arretify.utils.html import (
    render_str_list_attribute,
)
from arretify.utils.html_create import (
    make_data_tag,
    make_new_tag,
    make_segmentation_tag,
    read_segmentation_tag_data,
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
    join_with_or,
    named_group,
    safe_group,
    normalize_string,
)
from arretify.errors import ErrorCodes
from arretify.html_schemas import ERROR_SCHEMA
from arretify.regex_utils import split_string_with_regex
from arretify.regex_utils import map_matches
from arretify.utils.split_merge import (
    Probe,
    RawSplit,
    Splitter,
    split_elements,
    map_splitted_elements,
    flat_map_splitted_elements,
    split_before_match,
    negate,
)
from arretify.law_data.french_addresses import (
    WAY_TYPES,
    NUMBER_SUFFIXES,
    ALL_STREET_NAMES,
    STREET_NAMES_NORMALIZATION_SETTINGS,
)

from .core import (
    is_tag,
    make_single_line_splitter_for_text_span_nodes,
    get_string,
    get_strings,
    combine_text_spans,
    make_probe_from_pattern_proxy,
    pick_text_span_node,
    pick_if_transparent_tag_followed_by_match,
    make_pattern_splitter,
)
from .document_elements import render_table_of_contents, render_page_footer, render_page_separator


_LOGGER = logging.getLogger(__name__)


# -------------------- Tables -------------------- #
_TableSplitterMatch = Tuple[List[PageElementOrString], List[PageElementOrString]]
"""
A match for the table splitter, in the form `(<table_elements>, <table_description_elements>)`.
"""

_is_table = make_probe_from_pattern_proxy(TABLE_LINE_PATTERN)
_is_table_start = pick_text_span_node(_is_table)
_is_table_end = negate(pick_if_transparent_tag_followed_by_match(pick_text_span_node(_is_table)))


def _make_table_description_end_probe(table_lines: Sequence[str]) -> Probe[PageElementOrString]:
    def _is_table_description(elements: Sequence[PageElementOrString], index: int) -> bool:
        if is_table_description(get_string(elements[index]), table_lines):
            return True
        return False

    return negate(pick_text_span_node(_is_table_description))


def parse_tables(
    context: DocumentContext,
    elements: Sequence[PageElementOrString],
) -> List[PageElementOrString]:
    return flat_map_splitted_elements(
        split_elements(elements, _table_splitter),
        lambda match: _make_table_tags(context, match),
    )


@iter_func_to_list
def _make_table_tags(
    context: DocumentContext, match: _TableSplitterMatch
) -> Iterator[PageElementOrString]:
    table_pile, table_description_pile = match
    yield make_segmentation_tag(context.soup, "table", contents=table_pile)
    if table_description_pile:
        yield make_segmentation_tag(
            context.soup, "table_description", contents=table_description_pile
        )


def _table_splitter(
    elements: Sequence[PageElementOrString],
) -> RawSplit[PageElementOrString, _TableSplitterMatch] | None:
    before, elements = split_before_match(elements, _is_table_start)
    table_pile, elements = split_before_match(elements, _is_table_end)

    if table_pile:
        # Directly after table end, look for table description.
        table_description_pile, elements = split_before_match(
            elements,
            _make_table_description_end_probe(get_strings(table_pile)),
        )

        return (
            before,
            (
                table_pile,
                table_description_pile,
            ),
            elements,
        )
    else:
        return None


def render_table(
    context: DocumentContext,
    tag: Tag,
) -> Tag:
    pile: List[str] = []
    has_table_header = False
    transparent_tags: List[Tuple[int, Tag]] = []
    for element in tag.children:
        if is_tag(element, tag_name_in=["text_span"]):
            element_str = get_string(element)
            pile.append(element_str)
            if bool(TABLE_HEADER_SEPARATOR_PATTERN.match(element_str)):
                has_table_header = True
        elif is_tag(element, tag_name_in=["page_separator"]):
            table_tag = parse_markdown_table(pile)
            # Get the right table row for inserting the transparent tag.
            # If the table has a header, the `pile` contains a header
            # separation line (e.g. "|---|---|---|"), which is not
            # counting as a row in the final html table tag.
            row_index = len(pile) - 1 - int(has_table_header)
            transparent_tags.append((row_index, element))
        else:
            raise ValueError(f"Unexpected element type {type(element)} in table rendering.")

    table_tag = parse_markdown_table(pile)

    # Insert transparent nodes in their corresponding table rows.
    table_rows = table_tag.find_all("tr")
    for row_index, transparent_tag in transparent_tags:
        if row_index < len(table_rows) and row_index >= 0:
            table_rows[row_index].select("td, th")[-1].append(
                render_page_separator(context, transparent_tag)
            )
        else:
            raise ValueError(f"Invalid index {row_index} in table rendering. ")

    return table_tag


def render_table_description(
    context: DocumentContext,
    tag: Tag,
) -> Iterator[PageElementOrString]:
    for element in tag.children:
        if is_tag(element, tag_name_in=["text_span"]):
            yield context.soup.new_tag("br")
            yield get_string(element)
        elif is_tag(element, tag_name_in=["page_separator"]):
            yield render_page_separator(context, element)
        else:
            raise ValueError(
                f"Unexpected element type {type(element)} in table description rendering."
            )


# -------------------- Lists -------------------- #
LEADING_WHITESPACES_PATTERN = PatternProxy(r"^\s+")
"""Detect leading whitespaces."""

_is_list_element = make_probe_from_pattern_proxy(LIST_PATTERN)
_is_list_start = pick_text_span_node(_is_list_element)
_is_list_continuation = pick_if_transparent_tag_followed_by_match(
    pick_text_span_node(_is_list_element)
)


def _list_indentation(line: str) -> int:
    list_match = LIST_PATTERN.match(line)
    if not list_match:
        raise ValueError("Expected line to be a list element")
    indentation = list_match.group("indentation")
    assert indentation is not None
    return len(indentation)


def _clean_leading_whitespaces(line: str) -> str:
    return LEADING_WHITESPACES_PATTERN.sub("", line)


def _make_list_splitter(
    context: DocumentContext,
) -> Splitter[PageElementOrString, List[PageElementOrString]]:
    def _splitter(
        elements: Sequence[PageElementOrString],
    ) -> RawSplit[PageElementOrString, List[PageElementOrString]] | None:
        """
        Split the input list into piles of list elements.
        Each pile is a list of elements that are part of the same list.
        """
        before, elements = split_before_match(elements, _is_list_start)

        if not elements:
            return None

        pile: List[PageElementOrString] = []
        while elements:
            element = elements[0]

            # This will pick either a list element, or an transparent tag (e.g. page separator)
            # that is followed by a list element.
            if _is_list_continuation(elements, 0):
                pile.append(elements.pop(0))

            # If we get a line that does not match the list pattern,
            # we check if it continues the previous sentence.
            elif is_tag(element, tag_name_in=["text_span"]):
                # First get the previous list element in the pile.
                j = len(pile) - 1
                while j >= 0 and not is_tag(pile[j], tag_name_in=["text_span"]):
                    j -= 1
                if j < 0:
                    raise RuntimeError("Expected to find a list element in the pile.")
                previous_list_element = pile[j]

                if is_continuing_sentence(
                    get_string(previous_list_element),
                    get_string(element),
                ):
                    element.insert(0, " ")
                    pile[j] = combine_text_spans(context, [*pile[j:], element])
                    elements.pop(0)
                else:
                    break

            else:
                break

        return before, pile, elements

    return _splitter


# Does not deal with case (no bullets, but indented lines) :
# - bla
#     hello
#     hellu
# - bli
def parse_lists(
    context: DocumentContext,
    elements: Sequence[PageElementOrString],
) -> List[PageElementOrString]:
    return map_splitted_elements(
        split_elements(
            elements,
            _make_list_splitter(context),
        ),
        lambda pile: make_segmentation_tag(context.soup, "list", contents=pile),
    )


def render_list(
    context: DocumentContext,
    tag: Tag,
) -> Tag:
    elements, ul = _render_list(context, tag.contents)
    assert len(elements) == 0, "Expected all lines to be consumed in list rendering"
    return ul


def _render_list(
    context: DocumentContext,
    elements_: Sequence[PageElementOrString],
) -> Tuple[List[PageElementOrString], Tag]:
    elements = list(elements_)
    list_pile: List[Tag] = []
    element = elements[0]
    ref_indentation = _list_indentation(get_string(element))

    while elements:
        element = elements[0]

        if is_tag(element, tag_name_in=["page_separator"]):
            list_pile[-1].append(render_page_separator(context, element))
            elements.pop(0)

        elif is_tag(element, tag_name_in=["text_span"]):
            current_indentation = _list_indentation(get_string(element))

            if current_indentation == ref_indentation:
                li_contents = list(render_text_span(context, element))
                if isinstance(li_contents[0], str):
                    li_contents[0] = _clean_leading_whitespaces(li_contents[0])
                list_pile.append(make_new_tag(context.soup, "li", contents=li_contents))
                elements.pop(0)

            elif current_indentation > ref_indentation:
                elements, nested_ul = _render_list(context, elements)
                list_pile[-1].append(nested_ul)

            # If the indentation is less than the reference indentation,
            # we exit the function and go up one level.
            else:
                break

        else:
            raise ValueError(f"Unexpected element {element} in list rendering.")

    return elements, make_new_tag(context.soup, "ul", contents=list_pile)


# -------------------- Blockquotes -------------------- #
_BlockquoteSplitterMatch = Tuple[List[PageElementOrString], ErrorCodes | None]
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
    context: DocumentContext,
    elements: Sequence[PageElementOrString],
) -> List[PageElementOrString]:
    return map_splitted_elements(
        split_elements(
            elements,
            _blockquote_splitter,
        ),
        lambda match: _make_blockquote_tag(context, match),
    )


def _make_blockquote_tag(context: DocumentContext, match: _BlockquoteSplitterMatch) -> Tag:
    pile, error_code = match
    if error_code is None:
        contents = chain_functions(context, pile, [parse_tables, parse_lists, parse_images])
        return make_segmentation_tag(context.soup, "blockquote", contents=contents)
    else:
        return make_segmentation_tag(
            context.soup, "error", contents=pile, data=dict(error_codes=[error_code.value])
        )


def _blockquote_splitter(
    elements: Sequence[PageElementOrString],
) -> RawSplit[PageElementOrString, _BlockquoteSplitterMatch] | None:
    before, elements = split_before_match(elements, _is_blockquote_start)

    if not elements:
        return None

    # At this point, we know that the first element is a blockquote start
    element = elements[0]
    assert is_tag(element, tag_name_in=["text_span"])
    first_str_index, first_str = _get_first_str(element)
    blockquote_start = read_segmentation_tag_data(element)["start"]
    # Remove opening quote
    element.contents[first_str_index].replace_with(BLOCKQUOTE_START_PATTERN.sub("", first_str))
    quotes_depth_count = 1

    for i, element in enumerate(elements):
        if not is_tag(element, tag_name_in=["text_span"]):
            continue

        # Ignore case when the line contains a balanced number of quotes.
        # In that case, no need to increment or decrement as this will
        # be handled recursively.
        double_quotes_matches = list(DOUBLE_QUOTE_PATTERN.finditer(get_string(element)))
        if len(double_quotes_matches) % 2 == 0:
            pass
        else:
            if _is_blockquote_start(elements, i):
                quotes_depth_count += 1
            if _is_blockquote_end(elements, i):
                quotes_depth_count -= 1
            if quotes_depth_count <= 0:
                last_str_index, last_str = _get_last_str(element)
                # Remove the end quote
                element.contents[last_str_index].replace_with(
                    BLOCKQUOTE_END_PATTERN.sub("", last_str)
                )
                break

    if quotes_depth_count == 0:
        # Last line should be included, so we take `i + 1`
        return before, (elements[: i + 1], None), elements[i + 1 :]
    else:
        _LOGGER.warning(f"Found unbalanced quote starting {blockquote_start}")
        return before, (elements[0:1], ErrorCodes.unbalanced_quote), elements[1:]


def _get_first_str(
    text_span_tag: Tag,
) -> Tuple[int, str]:
    for i, element in enumerate(text_span_tag.contents):
        if isinstance(element, str):
            return i, element
    raise ValueError("No str found.")


def _get_last_str(
    text_span_tag: Tag,
) -> Tuple[int, str]:
    for i, element in enumerate(reversed(text_span_tag.contents)):
        if isinstance(element, str):
            return len(text_span_tag.contents) - 1 - i, element
    raise ValueError("No str found.")


def render_blockquote(
    context: DocumentContext,
    tag: Tag,
) -> Tag:
    blockquote_tag = context.soup.new_tag("blockquote")
    for element in tag.contents:
        if is_tag(element, tag_name_in=["text_span"]):
            blockquote_tag.append(
                make_new_tag(
                    context.soup,
                    "p",
                    # TODO : should be parsed like other nodes, instead of being
                    # rendered here on the fly. This would also make parsing blockquote easier.
                    contents=render_inline_quotes(context, get_string(element)),
                )
            )
        elif is_tag(element):
            blockquote_tag.extend(render_basic_elements(context, element))

    return blockquote_tag


# -------------------- Images -------------------- #
_is_image = make_probe_from_pattern_proxy(IMAGE_PATTERN)


def parse_images(
    context: DocumentContext,
    elements: Sequence[PageElementOrString],
) -> List[PageElementOrString]:
    return map_splitted_elements(
        split_elements(
            elements,
            make_single_line_splitter_for_text_span_nodes(_is_image),
        ),
        lambda children: make_segmentation_tag(context.soup, "image", contents=children),
    )


def render_image(
    context: DocumentContext,
    tag: Tag,
) -> Tag:
    return parse_markdown_image(get_string(tag))


# -------------------- Addresses -------------------- #
ADDRESS_DETECT_PATTERN = PatternProxy(
    # Detects a street number at the start of the string.
    # Examples :
    # 123
    # 42bis
    named_group(
        rf"\d+(\s*({join_with_or(list(NUMBER_SUFFIXES))}))?\s+",
        group_name="street_number",
    )
    # Detects a string that starts with a way type, then
    # all characters until the end of the string.
    # Example :
    # rue Jean Moulin, 12345 Ville-sur-Fleuve, blabla.
    + named_group(rf"({join_with_or(list(WAY_TYPES))}).*$", group_name="street_name_and_remainder")
)


_address_detect_splitter = make_pattern_splitter(ADDRESS_DETECT_PATTERN)


def parse_addresses(
    context: DocumentContext,
    elements: Sequence[PageElementOrString],
) -> List[PageElementOrString]:
    """
    Parse French addresses.

    Right now we detect only the street number and street name.
    e.g. : in "12bis rue Jean Moulin, 75000 Paris", we detect only "12bis rue Jean Moulin".
    """
    return map_splitted_elements(
        split_elements(
            elements,
            _address_splitter,
        ),
        lambda address: make_segmentation_tag(context.soup, "address", contents=[address]),
    )


def _address_splitter(
    elements: Sequence[PageElementOrString],
) -> RawSplit[PageElementOrString, str] | None:
    split = _address_detect_splitter(elements)
    if not split:
        return None

    before_elements, match, after_elements = split
    street_number = safe_group(match, "street_number")
    street_name_and_remainder: str = safe_group(match, "street_name_and_remainder")
    normalized_street_name_and_remainder = normalize_string(
        street_name_and_remainder, STREET_NAMES_NORMALIZATION_SETTINGS
    )

    # Find the longest street name that matches, so we can separate
    # the street name from the remainder.
    i = len(normalized_street_name_and_remainder)
    candidate = normalized_street_name_and_remainder[0:i]
    while i > 0:
        if candidate in ALL_STREET_NAMES:
            break
        i -= 1
        candidate = normalized_street_name_and_remainder[0:i]

    remainder_string = street_name_and_remainder[len(candidate) :]
    if remainder_string:
        after_elements.insert(
            0,
            remainder_string,
        )

    return (
        before_elements,
        # Recompose address by re-adding street number
        street_number + street_name_and_remainder[0 : len(candidate)],
        after_elements,
    )


def render_address(
    context: DocumentContext,
    tag: Tag,
) -> Tag:
    return make_new_tag(
        context.soup,
        "address",
        contents=[
            get_string(tag),
        ],
    )


# -------------------- Misc -------------------- #
INLINE_QUOTE_PATTERN = PatternProxy(r'"(?P<quoted>[^"]+)"')
"""Detect if a sentence has inline quotes."""


def render_inline_quotes(context: DocumentContext, string: str) -> Iterator[PageElementOrString]:
    return map_matches(
        split_string_with_regex(INLINE_QUOTE_PATTERN, string),
        lambda inline_quote_match: make_new_tag(
            context.soup,
            "q",
            contents=[str(inline_quote_match.group("quoted"))],
        ),
    )


@iter_func_to_list
def render_text_span(
    context: DocumentContext,
    tag: Tag,
) -> Iterator[PageElementOrString]:
    for i, element in enumerate(tag.contents):
        if isinstance(element, str):
            # If this is not the last element, we add a space as separator.
            yield element + " " * int(i < len(tag.contents) - 1)
        elif is_tag(element, tag_name_in=["page_separator"]):
            yield render_page_separator(context, element)
        elif is_tag(element, tag_name_in=["address"]):
            yield render_address(context, element)
        else:
            raise ValueError(f"Unexpected element type {type(element)} in text span rendering.")


def render_basic_elements(
    context: DocumentContext,
    tag: Tag,
) -> Iterator[PageElementOrString]:
    tag_name = tag.name
    if tag_name == "list":
        yield render_list(context, tag)
    elif tag_name == "table":
        yield render_table(context, tag)
    elif tag_name == "table_description":
        yield from render_table_description(context, tag)
    elif tag_name == "blockquote":
        yield render_blockquote(context, tag)
    elif tag_name == "table_of_contents":
        yield render_table_of_contents(context, tag)
    elif tag_name == "page_footer":
        yield render_page_footer(context, tag)
    elif tag_name == "page_separator":
        yield render_page_separator(context, tag)
    elif tag_name == "image":
        yield render_image(context, tag)
    elif tag_name == "error":
        yield render_error(context, tag)
    elif tag_name == "text_span":
        yield from render_text_span(context, tag)
    else:
        raise ValueError(f"Unknown tag type '{tag_name}' in render_basic_elements.")


def render_error(
    context: DocumentContext,
    tag: Tag,
) -> Tag:
    return make_data_tag(
        context.soup,
        ERROR_SCHEMA,
        data=dict(
            error_codes=render_str_list_attribute(
                cast(List[str], read_segmentation_tag_data(tag)["error_codes"])
            )
        ),
        contents=[get_string(n) for n in tag.contents],
    )
