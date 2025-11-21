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
from typing import Iterator, List, Sequence, Tuple

from arretify.regex_utils.core import PatternProxy
from arretify.regex_utils.functional import map_matches
from arretify.regex_utils.split import split_string_with_regex
from arretify.semantic_tag_specs import (
    AlineaSpec,
    AppendixSpec,
    HeaderSpec,
    MainSpec,
    PageSeparatorSpec,
    SectionData,
    SectionSpec,
    SectionTitleData,
    SectionTitleSpec,
)
from arretify.step_segmentation.core import TRANSPARENT_TAG_SPECS, get_string
from arretify.step_segmentation.header import VISA_MOTIFS_RENDER_SPECS
from arretify.step_segmentation.semantic_tag_specs import (
    AlineaSegmentationSpec,
    AppendixSegmentationSpec,
    BlockquoteSegmentationSpec,
    HeaderSegmentationSpec,
    ListSegmentationSpec,
    MainSegmentationSpec,
    MotifSegmentationSpec,
    SectionSegmentationSpec,
    SectionTitleSegmentationSpec,
    TableDescriptionSegmentationSpec,
    TableSegmentationSpec,
    TextSpanSegmentationSpec,
    VisaSegmentationSpec,
)
from arretify.types import DocumentContext, ProtectedTag, ProtectedTagOrStr
from arretify.utils.functional import iter_func_to_list
from arretify.utils.html_create import make_semantic_tag, make_tag, replace_contents
from arretify.utils.html_semantic import (
    get_semantic_tag_data,
    get_semantic_tag_spec,
    is_semantic_tag,
)
from arretify.utils.markdown_parsing import (
    LIST_PATTERN,
    TABLE_HEADER_SEPARATOR_PATTERN,
    parse_markdown_table,
)

_LOGGER = logging.getLogger(__name__)


@iter_func_to_list
def render_contents(
    context: DocumentContext,
    contents: Sequence[ProtectedTagOrStr],
) -> Iterator[ProtectedTagOrStr]:
    """
    Recursively renders the segmentation tags into their final HTML representation.
    """
    for element in contents:
        if is_semantic_tag(element, spec_in=[HeaderSegmentationSpec]):
            yield render_header(context, element)

        elif is_semantic_tag(element, spec_in=[MainSegmentationSpec]):
            yield render_main(
                context,
                element,
            )

        elif is_semantic_tag(element, spec_in=[AppendixSegmentationSpec]):
            yield render_appendix(
                context,
                element,
            )

        elif is_semantic_tag(element, spec_in=[SectionSegmentationSpec]):
            yield render_section(context, element)

        elif is_semantic_tag(element, spec_in=[SectionTitleSegmentationSpec]):
            yield render_section_title(context, element)

        elif is_semantic_tag(element, spec_in=[AlineaSegmentationSpec]):
            yield render_alinea(context, element)

        elif is_semantic_tag(element, spec_in=[VisaSegmentationSpec, MotifSegmentationSpec]):
            yield render_visa_motif(context, element)

        elif is_semantic_tag(element, spec_in=[ListSegmentationSpec]):
            yield render_list(context, element)

        elif is_semantic_tag(element, spec_in=[BlockquoteSegmentationSpec]):
            yield render_blockquote(context, element)

        elif is_semantic_tag(element, spec_in=[TableSegmentationSpec]):
            yield render_table(context, element)

        elif is_semantic_tag(element, spec_in=[TableDescriptionSegmentationSpec]):
            yield from render_table_description(context, element)

        else:
            yield element


# -------------------- Arrete segmentation -------------------- #


def render_section_title(
    context: DocumentContext,
    tag: ProtectedTag,
) -> ProtectedTag:
    if not is_semantic_tag(tag, spec_in=[SectionTitleSegmentationSpec]):
        raise ValueError("Tag must be a section title")

    segmentation_section_data = get_semantic_tag_data(SectionTitleSegmentationSpec, tag)
    assert segmentation_section_data.level is not None, "Section level must be defined"
    section_title_data = SectionTitleData(
        level=segmentation_section_data.level, error_codes=segmentation_section_data.error_codes
    )

    return make_semantic_tag(
        context.protected_soup,
        SectionTitleSpec,
        contents=[get_string(tag)],
        data=section_title_data,
    )


def render_section(
    context: DocumentContext,
    tag: ProtectedTag,
) -> ProtectedTag:
    assert is_semantic_tag(
        tag.contents[0], spec_in=[SectionTitleSegmentationSpec]
    ), "First tag must be a section title"
    section_title: ProtectedTag = tag.contents[0]
    section_data = get_semantic_tag_data(SectionTitleSegmentationSpec, section_title)
    return make_semantic_tag(
        context.protected_soup,
        SectionSpec,
        data=SectionData(
            type=section_data.type,
            number=section_data.number,
            title=section_data.title,
        ),
        contents=render_contents(context, tag.contents),
    )


def render_alinea(
    context: DocumentContext,
    tag: ProtectedTag,
) -> ProtectedTag:
    contents: list[ProtectedTagOrStr] = []
    for element in render_contents(context, tag.contents):
        if is_semantic_tag(element, spec_in=[TextSpanSegmentationSpec]):
            # TODO : move render_inline_quotes inside render_text_span
            text_span_elements = render_text_span(context, element)
            for text_span_element in text_span_elements:
                if isinstance(text_span_element, str):
                    contents.extend(render_inline_quotes(context, text_span_element))
                else:
                    contents.append(text_span_element)
        else:
            contents.append(element)

    return make_semantic_tag(
        context.protected_soup,
        AlineaSpec,
        data=get_semantic_tag_data(AlineaSegmentationSpec, tag),
        contents=contents,
    )


# -------------------- Header / Main -------------------- #


def render_header(
    context: DocumentContext,
    tag: ProtectedTag,
) -> ProtectedTag:
    contents: list[ProtectedTagOrStr] = []
    for element in render_contents(context, tag.contents):
        if is_semantic_tag(element, spec_in=[TextSpanSegmentationSpec]):
            contents.append(
                make_tag(
                    context.protected_soup,
                    "div",
                    contents=render_text_span(context, element),
                )
            )
        else:
            contents.append(element)

    return make_semantic_tag(
        context.protected_soup,
        HeaderSpec,
        contents=contents,
    )


def render_visa_motif(
    context: DocumentContext,
    tag: ProtectedTag,
) -> ProtectedTag:
    assert is_semantic_tag(tag, spec_in=[VisaSegmentationSpec, MotifSegmentationSpec])
    contents: list[ProtectedTagOrStr] = []
    spec = get_semantic_tag_spec(tag)

    for element in render_contents(context, tag.contents):
        if is_semantic_tag(element, spec_in=[TextSpanSegmentationSpec]):
            contents.append(get_string(element))
        else:
            contents.append(element)

    return make_semantic_tag(
        context.protected_soup,
        VISA_MOTIFS_RENDER_SPECS[spec],
        contents=contents,
    )


def render_main(
    context: DocumentContext,
    tag: ProtectedTag,
) -> ProtectedTag:
    return make_semantic_tag(
        context.protected_soup,
        MainSpec,
        contents=render_contents(context, tag.contents),
    )


def render_appendix(
    context: DocumentContext,
    tag: ProtectedTag,
) -> ProtectedTag:
    return make_semantic_tag(
        context.protected_soup,
        AppendixSpec,
        contents=render_contents(context, tag.contents),
    )


# -------------------- List -------------------- #


LEADING_WHITESPACES_PATTERN = PatternProxy(r"^\s+")
"""Detect leading whitespaces."""


def _list_indentation(line: str) -> int:
    list_match = LIST_PATTERN.match(line)
    if not list_match:
        raise ValueError("Expected line to be a list element")
    indentation = list_match.group("indentation")
    assert indentation is not None
    return len(indentation)


def _clean_leading_whitespaces(line: str) -> str:
    return LEADING_WHITESPACES_PATTERN.sub("", line)


def render_list(
    context: DocumentContext,
    tag: ProtectedTag,
) -> ProtectedTag:
    elements = list(tag.contents)
    iteration_counter = 0
    ul = None
    # With a well-formed list, the following loop should iterate only once.
    # However, we handle here the case of malformed lists,
    # where indentation is not perfectly consistent, e.g. :
    #  - Item 1
    # - Item 2
    while elements:
        elements, new_ul = _render_list(context, elements)
        if ul is None:
            ul = new_ul
        else:
            ul = replace_contents(ul, ul.contents + new_ul.contents)
        iteration_counter += 1

    if iteration_counter > 1:
        _LOGGER.warning("List could be malformed due to inconsistent indentation.")

    assert ul is not None, "Expected to have a list for rendering but found none"
    return ul


def _render_list(
    context: DocumentContext,
    elements_: Sequence[ProtectedTagOrStr],
) -> Tuple[list[ProtectedTagOrStr], ProtectedTag]:
    elements = list(elements_)
    list_pile: list[ProtectedTag] = []
    element = elements[0]
    ref_indentation = _list_indentation(get_string(element))

    while elements:
        element = elements[0]

        if is_semantic_tag(element, spec_in=[PageSeparatorSpec]):
            list_pile[-1] = replace_contents(list_pile[-1], list_pile[-1].contents + [element])
            elements.pop(0)

        elif is_semantic_tag(element, spec_in=[TextSpanSegmentationSpec]):
            current_indentation = _list_indentation(get_string(element))

            if current_indentation == ref_indentation:
                li_contents = list(render_text_span(context, element))
                if isinstance(li_contents[0], str):
                    li_contents[0] = _clean_leading_whitespaces(li_contents[0])
                list_pile.append(make_tag(context.protected_soup, "li", contents=li_contents))
                elements.pop(0)

            elif current_indentation > ref_indentation:
                elements, nested_ul = _render_list(context, elements)
                list_pile[-1] = replace_contents(
                    list_pile[-1], list_pile[-1].contents + [nested_ul]
                )

            # If the indentation is less than the reference indentation,
            # we exit the function and go up one level.
            else:
                break

        else:
            raise ValueError(f"Unexpected element {element} in list rendering.")

    return elements, make_tag(context.protected_soup, "ul", contents=list_pile)


# -------------------- Table -------------------- #


def render_table(
    _: DocumentContext,
    tag: ProtectedTag,
) -> ProtectedTag:
    pile: list[str] = []
    has_table_header = False
    transparent_tags: list[Tuple[int, ProtectedTag]] = []
    for element in tag.contents:
        if is_semantic_tag(element, spec_in=[TextSpanSegmentationSpec]):
            element_str = get_string(element)
            pile.append(element_str)
            if bool(TABLE_HEADER_SEPARATOR_PATTERN.match(element_str)):
                has_table_header = True
        elif is_semantic_tag(element, spec_in=TRANSPARENT_TAG_SPECS):
            table_tag = parse_markdown_table(pile)
            # Get the right table row for inserting the transparent tag.
            # If the table has a header, the `pile` contains a header
            # separation line (e.g. "|---|---|---|"), which is not
            # counting as a row in the final html table tag.
            row_index = len(pile) - 1 - int(has_table_header)
            transparent_tags.append((row_index, element))
        else:
            raise ValueError(f"Unexpected element {element} in table rendering.")

    table_tag = parse_markdown_table(pile)

    # Insert transparent tags in their corresponding table rows.
    table_rows = table_tag.select("tr")
    for row_index, transparent_tag in transparent_tags:
        if row_index < len(table_rows) and row_index >= 0:
            last_cell_tag = table_rows[row_index].select("td, th")[-1]
            replace_contents(last_cell_tag, last_cell_tag.contents + [transparent_tag])
        else:
            raise ValueError(f"Invalid index {row_index} in table rendering. ")

    return table_tag


def render_table_description(
    context: DocumentContext,
    tag: ProtectedTag,
) -> Iterator[ProtectedTagOrStr]:
    for element in tag.contents:
        if is_semantic_tag(element, spec_in=[TextSpanSegmentationSpec]):
            yield make_tag(context.protected_soup, "br")
            yield get_string(element)
        else:
            yield element


# -------------------- Blockquote -------------------- #


def render_blockquote(
    context: DocumentContext,
    tag: ProtectedTag,
) -> ProtectedTag:
    contents: List[ProtectedTagOrStr] = []
    for element in render_contents(context, tag.contents):
        if is_semantic_tag(element, spec_in=[TextSpanSegmentationSpec]):
            contents.append(
                make_tag(
                    context.protected_soup,
                    "p",
                    # TODO : should be parsed like other tags, instead of being
                    # rendered here on the fly. This would also make parsing blockquote easier.
                    contents=render_inline_quotes(context, get_string(element)),
                )
            )
        else:
            contents.append(element)

    return make_tag(context.protected_soup, "blockquote", contents=contents)


# -------------------- Misc -------------------- #
INLINE_QUOTE_PATTERN = PatternProxy(r'"(?P<quoted>[^"]+)"')
"""Detect if a sentence has inline quotes."""


def render_inline_quotes(context: DocumentContext, string: str) -> Iterator[ProtectedTagOrStr]:
    return map_matches(
        split_string_with_regex(INLINE_QUOTE_PATTERN, string),
        lambda inline_quote_match: make_tag(
            context.protected_soup,
            "q",
            contents=[str(inline_quote_match.group("quoted"))],
        ),
    )


@iter_func_to_list
def render_text_span(
    _: DocumentContext,
    tag: ProtectedTag,
) -> Iterator[ProtectedTagOrStr]:
    for i, element in enumerate(tag.contents):
        if isinstance(element, str):
            # If this is not the last element, we add a space as separator.
            yield element + " " * int(i < len(tag.contents) - 1)
        elif is_semantic_tag(element):
            yield element
        else:
            raise ValueError(f"Unexpected element type {type(element)} in text span rendering.")
