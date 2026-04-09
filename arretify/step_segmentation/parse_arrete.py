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
from typing import Callable, Iterator, Sequence, Tuple

from arretify.types import DocumentContext, ProtectedTagOrStr, SectionType
from arretify.utils.functional import chain_functions, iter_func_to_list
from arretify.utils.html_create import is_semantic_tag, make_semantic_tag, replace_contents
from arretify.utils.split_merge import split_before_match

from .basic_elements import parse_addresses, parse_page_footers, parse_tables_of_contents
from .core import get_string, pick_text_spans
from .header import is_arrete_keyword, parse_arrete_keyword, parse_header
from .main_or_appendix import is_title, parse_content
from .semantic_tag_specs import (
    AppendixSegmentationSpec,
    HeaderSegmentationSpec,
    MainSegmentationSpec,
    TextSpanSegmentationSpec,
)
from .titles_detection import parse_title_info

_is_title_line = pick_text_spans(is_title)


def _split_before_main(
    elements: Sequence[ProtectedTagOrStr],
) -> Tuple[Sequence[ProtectedTagOrStr], Sequence[ProtectedTagOrStr]]:
    """
    Helper to find the beginning of the main content.
    For that we look for the keyword "arrête" followed by a title.
    """
    arrete_keyword_index: int = -1
    counter: int = -1
    while counter < len(elements) - 1:
        counter += 1
        if is_arrete_keyword(elements, counter):
            arrete_keyword_index = counter
        elif arrete_keyword_index != -1 and _is_title_line(elements, counter):
            break

    if arrete_keyword_index != -1 and counter >= len(elements) - 1:
        raise ValueError("Could not find the first title after the 'arrête' keyword.")

    if arrete_keyword_index != -1:
        return elements[: arrete_keyword_index + 1], elements[arrete_keyword_index + 1 :]

    # If the "arrête" keyword is not found, we implement a fallback by looking
    # for the first title in the document.
    return split_before_match(elements, _is_title_line)


def _is_appendix_text_span_tag(elements: Sequence[ProtectedTagOrStr], index: int) -> bool:
    """
    Probe help find the beginning of the appendix by looking for a title with section type "Annexe".
    """
    element = elements[index]
    assert is_semantic_tag(element)
    if is_title(elements, index):
        # Parse title info
        title_info = parse_title_info(get_string(element))
        new_section_type = title_info.section_type

        # Appendix is considered as a different part of the document
        if new_section_type == SectionType.ANNEXE:
            return True
    return False


_is_appendix = pick_text_spans(_is_appendix_text_span_tag)


@iter_func_to_list
def parse_arrete(
    context: DocumentContext, elements: Sequence[ProtectedTagOrStr]
) -> Iterator[ProtectedTagOrStr]:
    # Add basic document elements
    remainder = chain_functions(
        context,
        elements,
        [
            _make_text_span_parser(parse_addresses),
            parse_page_footers,
            parse_tables_of_contents,
        ],
    )

    # Header
    header_elements, remainder = _split_before_main(remainder)
    header_elements = parse_arrete_keyword(context, header_elements)
    header_elements = parse_header(context, header_elements)
    yield make_semantic_tag(
        context.protected_soup, HeaderSegmentationSpec, contents=header_elements
    )

    # Main content
    main_elements, remainder = split_before_match(remainder, _is_appendix)
    main_elements = parse_content(context, main_elements)
    yield make_semantic_tag(context.protected_soup, MainSegmentationSpec, contents=main_elements)

    # Appendix
    if remainder:
        yield make_semantic_tag(
            context.protected_soup,
            AppendixSegmentationSpec,
            contents=parse_content(context, remainder),
        )


def _make_text_span_parser(
    func: Callable[[DocumentContext, Sequence[ProtectedTagOrStr]], list[ProtectedTagOrStr]],
) -> Callable[[DocumentContext, Sequence[ProtectedTagOrStr]], list[ProtectedTagOrStr]]:
    """
    Makes a function that uses `func` to parse the children of text_span tags.
    """

    @iter_func_to_list
    def _parse(
        context: DocumentContext, elements: Sequence[ProtectedTagOrStr]
    ) -> Iterator[ProtectedTagOrStr]:
        for element in elements:
            if is_semantic_tag(element, spec_in=[TextSpanSegmentationSpec]):
                yield replace_contents(element, func(context, element.contents))
            else:
                yield element

    return _parse
