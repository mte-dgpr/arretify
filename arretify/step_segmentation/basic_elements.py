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
import logging
from typing import Iterator, Sequence, Tuple

from arretify.errors import ErrorCodes
from arretify.law_data.french_addresses import (
    ALL_STREET_NAMES,
    NUMBER_SUFFIXES,
    STREET_NAMES_NORMALIZATION_SETTINGS,
    WAY_TYPES,
)
from arretify.parsing_utils.patterns import is_continuing_sentence
from arretify.regex_utils import (
    PatternProxy,
    join_with_or,
    named_group,
    normalize_string,
    safe_group,
)
from arretify.semantic_tag_specs import AddressSpec, ErrorSpec, PageFooterSpec, TableOfContentsSpec
from arretify.step_segmentation.semantic_tag_specs import (
    BlockquoteSegmentationSpec,
    ListSegmentationSpec,
    TableDescriptionSegmentationSpec,
    TableSegmentationSpec,
    TextSpanSegmentationSpec,
)
from arretify.types import DocumentContext, ProtectedTag, ProtectedTagOrStr
from arretify.utils.functional import chain_functions, iter_func_to_list
from arretify.utils.html_create import (
    InvalidContentsError,
    make_semantic_tag,
    replace_contents,
    validate_semantic_tag_contents,
    wrap_in_tag,
)
from arretify.utils.html_semantic import SemanticTagSpec, get_semantic_tag_data, is_semantic_tag
from arretify.utils.markdown_parsing import (
    IMAGE_PATTERN,
    LIST_PATTERN,
    TABLE_LINE_PATTERN,
    is_table_description,
    parse_markdown_image,
)
from arretify.utils.split_merge import (
    Probe,
    RawSplit,
    Splitter,
    flat_map_splitted_elements,
    negate,
    split_and_map_elements,
    split_before_match,
    split_elements,
)

from .core import (
    combine_text_spans,
    get_string,
    get_strings,
    make_pattern_splitter,
    make_probe_from_pattern_proxy,
    make_single_line_splitter_for_text_spans,
    make_while_splitter_for_text_spans,
    pick_if_transparent_tag_followed_by_match,
    pick_text_spans,
)

_LOGGER = logging.getLogger(__name__)


# -------------------- Tables -------------------- #
_TableSplitterMatch = Tuple[list[ProtectedTagOrStr], list[ProtectedTagOrStr]]
"""
A match for the table splitter, in the form `(<table_elements>, <table_description_elements>)`.
"""

_is_table = make_probe_from_pattern_proxy(TABLE_LINE_PATTERN)
_is_table_start = pick_text_spans(_is_table)
_is_table_end = negate(pick_if_transparent_tag_followed_by_match(pick_text_spans(_is_table)))


def _make_table_description_end_probe(table_lines: Sequence[str]) -> Probe[ProtectedTagOrStr]:
    def _is_table_description(elements: Sequence[ProtectedTagOrStr], index: int) -> bool:
        if is_table_description(get_string(elements[index]), table_lines):
            return True
        return False

    return negate(pick_text_spans(_is_table_description))


def parse_tables(
    context: DocumentContext,
    elements: Sequence[ProtectedTagOrStr],
) -> list[ProtectedTagOrStr]:
    return flat_map_splitted_elements(
        split_elements(elements, _table_splitter),
        lambda match: _make_table_tags(context, match),
    )


@iter_func_to_list
def _make_table_tags(
    context: DocumentContext, match: _TableSplitterMatch
) -> Iterator[ProtectedTagOrStr]:
    table_pile, table_description_pile = match
    yield make_semantic_tag(context.protected_soup, TableSegmentationSpec, contents=table_pile)
    if table_description_pile:
        yield make_semantic_tag(
            context.protected_soup,
            TableDescriptionSegmentationSpec,
            contents=table_description_pile,
        )


def _table_splitter(
    elements: Sequence[ProtectedTagOrStr],
) -> RawSplit[ProtectedTagOrStr, _TableSplitterMatch] | None:
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


# -------------------- Lists -------------------- #
_is_list_element = make_probe_from_pattern_proxy(LIST_PATTERN)
_is_list_start = pick_text_spans(_is_list_element)
_is_list_continuation = pick_if_transparent_tag_followed_by_match(pick_text_spans(_is_list_element))


def _make_list_splitter(
    context: DocumentContext,
) -> Splitter[ProtectedTagOrStr, list[ProtectedTagOrStr]]:
    def _splitter(
        elements: Sequence[ProtectedTagOrStr],
    ) -> RawSplit[ProtectedTagOrStr, list[ProtectedTagOrStr]] | None:
        """
        Split the input list into piles of list elements.
        Each pile is a list of elements that are part of the same list.
        """
        before, elements = split_before_match(elements, _is_list_start)

        if not elements:
            return None

        pile: list[ProtectedTagOrStr] = []
        while elements:
            element = elements[0]

            # This will pick either a list element, or an transparent tag (e.g. page separator)
            # that is followed by a list element.
            if _is_list_continuation(elements, 0):
                pile.append(elements.pop(0))

            # If we get a line that does not match the list pattern,
            # we check if it continues the previous sentence.
            elif is_semantic_tag(element, spec_in=[TextSpanSegmentationSpec]):
                # First get the previous list element in the pile.
                j = len(pile) - 1
                while j >= 0 and not is_semantic_tag(pile[j], spec_in=[TextSpanSegmentationSpec]):
                    j -= 1
                if j < 0:
                    raise RuntimeError("Expected to find a list element in the pile.")
                previous_list_element = pile[j]

                if is_continuing_sentence(
                    get_string(previous_list_element),
                    get_string(element),
                ):
                    element = replace_contents(element, [" "] + element.contents)
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
    elements: Sequence[ProtectedTagOrStr],
) -> list[ProtectedTagOrStr]:
    return split_and_map_elements(
        elements,
        _make_list_splitter(context),
        lambda pile: make_semantic_tag(context.protected_soup, ListSegmentationSpec, contents=pile),
    )


# -------------------- Blockquotes -------------------- #
_BlockquoteSplitterMatch = Tuple[list[ProtectedTagOrStr], ErrorCodes | None]
"""
A match for the blockquote splitter, in the form `(<blockquote_elements>, <error_codes>)`.
"""

BLOCKQUOTE_START_PATTERN = PatternProxy(r"^\s*\"")
"""Detect if a sentence starts with a quote '"'."""

BLOCKQUOTE_END_PATTERN = PatternProxy(r"\"[\s\.]*$")
"""Detect if a sentence ends with a quote '"'."""

DOUBLE_QUOTE_PATTERN = PatternProxy(r'"')
"""Basic double quote '"' pattern."""


_is_blockquote_start = pick_text_spans(make_probe_from_pattern_proxy(BLOCKQUOTE_START_PATTERN))
_is_blockquote_end = pick_text_spans(
    make_probe_from_pattern_proxy(BLOCKQUOTE_END_PATTERN, use_search=True)
)


def parse_blockquotes(
    context: DocumentContext,
    elements: Sequence[ProtectedTagOrStr],
) -> list[ProtectedTagOrStr]:
    return split_and_map_elements(
        elements,
        _blockquote_splitter,
        lambda match: _make_blockquote_tag(context, match),
    )


def _make_blockquote_tag(context: DocumentContext, match: _BlockquoteSplitterMatch) -> ProtectedTag:
    pile, error_code = match
    if error_code is None:
        contents = chain_functions(context, pile, [parse_tables, parse_lists, parse_images])
        return make_semantic_tag(
            context.protected_soup, BlockquoteSegmentationSpec, contents=contents
        )
    else:
        return make_semantic_tag(
            context.protected_soup,
            ErrorSpec,
            contents=get_strings(pile),
            data=ErrorSpec.data_model(error_codes=[error_code]),
        )


def _blockquote_splitter(
    elements: Sequence[ProtectedTagOrStr],
) -> RawSplit[ProtectedTagOrStr, _BlockquoteSplitterMatch] | None:
    before, elements = split_before_match(elements, _is_blockquote_start)

    if not elements:
        return None

    # At this point, we know that the first element is a blockquote start
    element = elements[0]
    assert is_semantic_tag(element, spec_in=[TextSpanSegmentationSpec])
    first_str_index, first_str = _get_first_str(element)
    blockquote_start = get_semantic_tag_data(TextSpanSegmentationSpec, element).start
    # Remove opening quote
    elements[0] = replace_contents(
        element,
        element.contents[:first_str_index]
        + [BLOCKQUOTE_START_PATTERN.sub("", first_str)]
        + element.contents[first_str_index + 1 :],
    )
    quotes_depth_count = 1

    for i, element in enumerate(elements):
        if not is_semantic_tag(element, spec_in=[TextSpanSegmentationSpec]):
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
                elements[i] = replace_contents(
                    element,
                    element.contents[:last_str_index]
                    + [BLOCKQUOTE_END_PATTERN.sub("", last_str)]
                    + element.contents[last_str_index + 1 :],
                )
                break

    if quotes_depth_count == 0:
        # Last line should be included, so we take `i + 1`
        return before, (elements[: i + 1], None), elements[i + 1 :]
    else:
        _LOGGER.warning(f"Found unbalanced quote starting {blockquote_start}")
        return before, (elements[0:1], ErrorCodes.unbalanced_quote), elements[1:]


def _get_first_str(
    text_span_tag: ProtectedTag,
) -> Tuple[int, str]:
    for i, element in enumerate(text_span_tag.contents):
        if isinstance(element, str):
            return i, element
    raise ValueError("No str found.")


def _get_last_str(
    text_span_tag: ProtectedTag,
) -> Tuple[int, str]:
    for i, element in enumerate(reversed(text_span_tag.contents)):
        if isinstance(element, str):
            return len(text_span_tag.contents) - 1 - i, element
    raise ValueError("No str found.")


# -------------------- Images -------------------- #
_is_image = make_probe_from_pattern_proxy(IMAGE_PATTERN)


def parse_images(
    context: DocumentContext,
    elements: Sequence[ProtectedTagOrStr],
) -> list[ProtectedTagOrStr]:
    return split_and_map_elements(
        elements,
        make_single_line_splitter_for_text_spans(_is_image),
        lambda contents: parse_markdown_image(get_string(contents[0])),
    )


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
    elements: Sequence[ProtectedTagOrStr],
) -> list[ProtectedTagOrStr]:
    """
    Parse French addresses.

    Right now we detect only the street number and street name.
    e.g. : in "12bis rue Jean Moulin, 75000 Paris", we detect only "12bis rue Jean Moulin".
    """
    return split_and_map_elements(
        elements,
        _address_splitter,
        lambda address: make_semantic_tag(context.protected_soup, AddressSpec, contents=[address]),
    )


def _address_splitter(
    elements: Sequence[ProtectedTagOrStr],
) -> RawSplit[ProtectedTagOrStr, str] | None:
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


# -------------------- Table of contents and page footers -------------------- #
PAGE_FOOTERS_LIST = [
    # "X/Y"
    r"\d+/\d+\s*",
    # "Page X/Y"
    r"page\s+\d+/\d+\s*",
    # "Page X sur Y"
    r"page\s+\d+\s+sur\s+\d+\s*",
    # "Page X"
    r"page\s+\d+",
]

PAGE_FOOTER_PATTERN = PatternProxy(rf"^{join_with_or(PAGE_FOOTERS_LIST)}")
"""Detect page footer."""

_is_page_footer = make_probe_from_pattern_proxy(PAGE_FOOTER_PATTERN)


def parse_page_footers(
    context: DocumentContext,
    elements: Sequence[ProtectedTagOrStr],
) -> list[ProtectedTagOrStr]:
    return split_and_map_elements(
        elements,
        make_while_splitter_for_text_spans(_is_page_footer, _is_page_footer),
        lambda contents: make_semantic_tag(
            context.protected_soup,
            PageFooterSpec,
            contents=wrap_in_tag(
                context.protected_soup,
                "div",
                [get_string(e) for e in contents],
            ),
        ),
    )


# -------------------- Table of contents -------------------- #
TABLE_OF_CONTENTS_PAGING_PATTERN_S = r"\.{5}\s+(page\s+)?\d+"
"""Detect table of contents paging, e.g. "..... page 1" or "..... 1"."""

TABLE_OF_CONTENTS_LIST = [
    r"sommaire",
    r"table des matieres",
    r"liste des (chapitres|articles)",
    rf".*?\s+{TABLE_OF_CONTENTS_PAGING_PATTERN_S}$",
]

TABLE_OF_CONTENTS_PATTERN = PatternProxy(rf"^{join_with_or(TABLE_OF_CONTENTS_LIST)}")
"""Detect all table of contents starting sentences."""


_is_table_of_contents = make_probe_from_pattern_proxy(TABLE_OF_CONTENTS_PATTERN)


def parse_tables_of_contents(
    context: DocumentContext,
    elements: Sequence[ProtectedTagOrStr],
) -> list[ProtectedTagOrStr]:
    return split_and_map_elements(
        elements,
        make_while_splitter_for_text_spans(
            _is_table_of_contents,
            _table_of_contents_while_condition,
        ),
        lambda contents: _render_table_of_contents(context, contents),
    )


def _table_of_contents_while_condition(elements: Sequence[ProtectedTagOrStr], index: int) -> bool:
    # Instead of checking just the first line, we check the next few lines.
    # This allows to deal with case when TOC contains lines that are not
    # easily recognizable as TOC, e.g.:
    #
    #   Title 1
    #       article 1.1 ..... page 1
    #       article 1.2 ..... page 2
    #   Title 2
    #       article 2.1 ..... page 3
    #
    # Aditionnally, this takes in tags such as `page_separator` that might appear
    # between text segments.
    next_elements = elements[index : index + 3]
    if any(
        is_semantic_tag(next_elements[i], spec_in=[TextSpanSegmentationSpec])
        and _is_table_of_contents(next_elements, i)
        for i in range(len(next_elements))
    ):
        return True
    return False


def _render_table_of_contents(
    context: DocumentContext,
    contents: Sequence[ProtectedTagOrStr],
) -> ProtectedTag:
    rendered_contents: list[ProtectedTagOrStr] = []
    for element in contents:
        if is_semantic_tag(element, spec_in=[TextSpanSegmentationSpec]):
            rendered_contents.append(get_string(element))
        else:
            rendered_contents.append(element)
    return make_semantic_tag(
        context.protected_soup,
        TableOfContentsSpec,
        contents=wrap_in_tag(context.protected_soup, "div", rendered_contents),
    )


# -------------------- Unknown elements -------------------- #
@iter_func_to_list
def parse_unknown_elements(
    context: DocumentContext,
    spec: SemanticTagSpec,
    contents: Sequence[ProtectedTagOrStr],
) -> Iterator[ProtectedTagOrStr]:
    invalid_contents_indices = set()
    try:
        validate_semantic_tag_contents(spec, contents)
    except InvalidContentsError as invalid_contents_error:
        for index, _ in invalid_contents_error.errors:
            invalid_contents_indices.add(index)

    for i, element in enumerate(contents):
        if i in invalid_contents_indices:
            yield make_semantic_tag(
                context.protected_soup,
                ErrorSpec,
                contents=[element],
                data=ErrorSpec.data_model(error_codes=[ErrorCodes.unknown_content]),
            )

        else:
            yield element
