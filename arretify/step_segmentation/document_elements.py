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
from typing import Iterator, Sequence

from bs4 import Tag

from arretify.html_schemas import (
    PAGE_FOOTER_SCHEMA,
    TABLE_OF_CONTENTS_SCHEMA,
    PAGE_SEPARATOR_SCHEMA,
)
from arretify.regex_utils import (
    PatternProxy,
    join_with_or,
)

from arretify.types import DocumentContext, PageElementOrString
from arretify.utils.strings import split_on_newlines
from arretify.utils.html_create import (
    make_data_tag,
    wrap_in_tag,
)
from arretify.utils.functional import iter_func_to_list
from arretify.utils.split_merge import (
    split_elements,
    map_splitted_elements,
)
from .core import (
    is_segmentation_tag,
    make_segmentation_tag,
    read_segmentation_tag_data,
    make_while_splitter_for_text_spans,
    make_probe_from_pattern_proxy,
    get_string,
)


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
_is_page_footer = make_probe_from_pattern_proxy(PAGE_FOOTER_PATTERN)


def parse_tables_of_contents(
    context: DocumentContext,
    elements: Sequence[PageElementOrString],
) -> list[PageElementOrString]:
    return map_splitted_elements(
        split_elements(
            elements,
            make_while_splitter_for_text_spans(
                _is_table_of_contents,
                _table_of_contents_while_condition,
            ),
        ),
        lambda pile: make_segmentation_tag(
            context.soup, "table_of_contents", contents=pile, data=None
        ),
    )


def _table_of_contents_while_condition(elements: Sequence[PageElementOrString], index: int) -> bool:
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
        is_segmentation_tag(next_elements[i], tag_name_in=["text_span"])
        and _is_table_of_contents(next_elements, i)
        for i in range(len(next_elements))
    ):
        return True
    return False


def parse_page_footers(
    context: DocumentContext,
    elements: Sequence[PageElementOrString],
) -> list[PageElementOrString]:
    return map_splitted_elements(
        split_elements(
            elements,
            make_while_splitter_for_text_spans(_is_page_footer, _is_page_footer),
        ),
        lambda children: make_segmentation_tag(
            context.soup, "page_footer", contents=children, data=None
        ),
    )


@iter_func_to_list
def initialize_document_structure(
    context: DocumentContext,
    pages: Sequence[str],
) -> Iterator[PageElementOrString]:
    for page_index, page_text in enumerate(pages):
        yield make_segmentation_tag(
            context.soup, "page_separator", contents=[], data=dict(page_index=page_index)
        )
        page_lines = split_on_newlines(page_text)
        for line_index, line in enumerate(page_lines):
            yield make_segmentation_tag(
                context.soup,
                "text_span",
                contents=[line],
                data=dict(
                    start=[page_index, line_index, 0],
                    end=[page_index, line_index, len(line) - 1],
                ),
            )


def render_table_of_contents(
    context: DocumentContext,
    tag: Tag,
) -> Tag:
    page_elements: list[PageElementOrString] = []
    for element in tag.children:
        if is_segmentation_tag(element, tag_name_in=["text_span"]):
            page_elements.append(get_string(element))
        elif is_segmentation_tag(element, tag_name_in=["page_separator"]):
            page_elements.append(render_page_separator(context, element))
        else:
            raise ValueError(f"Unexpected element in table of contents: {element}")
    return make_data_tag(
        context.soup,
        TABLE_OF_CONTENTS_SCHEMA,
        contents=wrap_in_tag(context.soup, page_elements, "div"),
    )


def render_page_footer(
    context: DocumentContext,
    tag: Tag,
) -> Tag:
    return make_data_tag(
        context.soup,
        PAGE_FOOTER_SCHEMA,
        contents=wrap_in_tag(context.soup, [get_string(tag)], "div"),
    )


def render_page_separator(
    context: DocumentContext,
    tag: Tag,
) -> Tag:
    return make_data_tag(
        context.soup,
        PAGE_SEPARATOR_SCHEMA,
        data=dict(page_index=str(read_segmentation_tag_data(tag)["page_index"])),
    )
