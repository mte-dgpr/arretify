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
from typing import Callable, Iterator, Sequence

from arretify.semantic_tag_specs import PageSeparatorData, PageSeparatorSpec
from arretify.types import DocumentContext, ProtectedTagOrStr, SectionType
from arretify.utils.functional import chain_functions, iter_func_to_list
from arretify.utils.html_create import is_semantic_tag, make_semantic_tag, replace_contents
from arretify.utils.split_merge import split_before_match
from arretify.utils.strings import split_on_newlines

from .basic_elements import (
    parse_addresses,
    parse_images,
    parse_page_footers,
    parse_tables_of_contents,
)
from .core import get_string, pick_text_spans
from .header import parse_header
from .main_or_appendix import is_title, parse_content
from .semantic_tag_specs import (
    AppendixSegmentationSpec,
    HeaderSegmentationSpec,
    MainSegmentationSpec,
    TextSpanSegmentationData,
    TextSpanSegmentationSpec,
)
from .titles_detection import parse_title_info

_is_title_line = pick_text_spans(is_title)


def _is_appendix_text_span_tag(elements: Sequence[ProtectedTagOrStr], index: int) -> bool:
    element = elements[index]
    assert is_semantic_tag(element)
    if _is_title_line(elements, index):
        # Parse title info
        title_info = parse_title_info(get_string(element))
        new_section_type = title_info.section_type

        # Appendix is considered as a different part of the document
        if new_section_type == SectionType.ANNEXE:
            return True
    return False


_is_appendix = pick_text_spans(_is_appendix_text_span_tag)


@iter_func_to_list
def parse_arrete(context: DocumentContext, pages: Sequence[str]) -> Iterator[ProtectedTagOrStr]:
    elements: list[ProtectedTagOrStr] = initialize_document_structure(context, pages)

    # Add basic document elements
    elements = chain_functions(
        context,
        elements,
        [
            _make_text_span_parser(parse_addresses),
            # Image strings can be very long, and table of contents pattern look
            # at the end of the sentence.
            # So, we make sure we parse images before table of contents.
            parse_images,
            parse_page_footers,
            parse_tables_of_contents,
        ],
    )

    # Header
    pile, elements = split_before_match(elements, _is_title_line)
    yield make_semantic_tag(
        context.protected_soup, HeaderSegmentationSpec, contents=parse_header(context, pile)
    )

    # Main content
    pile, elements = split_before_match(elements, _is_appendix)
    yield make_semantic_tag(
        context.protected_soup, MainSegmentationSpec, contents=parse_content(context, pile)
    )

    # Appendix
    if elements:
        yield make_semantic_tag(
            context.protected_soup,
            AppendixSegmentationSpec,
            contents=parse_content(context, elements),
        )


@iter_func_to_list
def initialize_document_structure(
    context: DocumentContext,
    pages: Sequence[str],
) -> Iterator[ProtectedTagOrStr]:
    for page_index, page_text in enumerate(pages):
        yield make_semantic_tag(
            context.protected_soup,
            PageSeparatorSpec,
            contents=[],
            data=PageSeparatorData(page_index=page_index),
        )
        page_lines = split_on_newlines(page_text)
        for line_index, line in enumerate(page_lines):
            yield make_semantic_tag(
                context.protected_soup,
                TextSpanSegmentationSpec,
                contents=[line],
                data=TextSpanSegmentationData(
                    start=[page_index, line_index, 0],
                    end=[page_index, line_index, len(line) - 1],
                ),
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
