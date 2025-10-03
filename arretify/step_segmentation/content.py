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
from typing import Dict, Optional, Iterator, Sequence, cast
import logging

from bs4 import (
    Tag,
)

from arretify.types import DocumentContext, SectionType, PageElementOrString, DataElementDataDict
from arretify.utils.html import (
    render_str_list_attribute,
)
from arretify.utils.html_semantic import (
    make_semantic_tag,
)
from arretify.utils.html_create import (
    make_new_tag,
)
from arretify.utils.functional import iter_func_to_list, chain_functions
from arretify.utils.split import split_at_first_verb
from arretify.semantic_tag_schemas import (
    SECTION_SCHEMA,
    SECTION_TITLE_SCHEMAS,
    ALINEA_SCHEMA,
)
from arretify.errors import ErrorCodes
from .basic_elements import (
    render_basic_elements,
    render_inline_quotes,
    render_text_span,
    parse_tables,
    parse_lists,
    parse_images,
    parse_blockquotes,
)
from arretify.utils.split_merge import (
    map_splitted_elements,
    split_elements,
)
from .titles_detection import (
    parse_title_text,
    parse_title_info,
    is_next_title,
    TITLE_NODE,
)
from .core import (
    combine_text_spans,
    is_segmentation_tag,
    make_segmentation_tag,
    read_segmentation_tag_data,
    update_segmentation_tag_data,
    make_recombine_interrupted_lines_splitter,
    make_single_line_splitter_for_text_spans,
    make_probe_from_pattern_proxy,
    get_string,
)
from .document_elements import (
    render_page_footer,
    render_table_of_contents,
    render_page_separator,
)


_LOGGER = logging.getLogger(__name__)


_is_title_string = make_probe_from_pattern_proxy(
    TITLE_NODE.pattern,
)


def is_title(elements: Sequence[PageElementOrString], index: int) -> bool:
    element = elements[index]
    assert is_segmentation_tag(element, tag_name_in=["text_span"])
    # Exclude text_span tags that start with an inline tag.
    # This excludes cases when a line starts with an address
    # or another inline element, which cannot be a title.
    if element.children == 0 or not isinstance(element.contents[0], str):
        return False
    else:
        return _is_title_string(elements, index)


def _get_downstream_sections_types(section_type):
    ordered_sections_types = [section_type for section_type in SectionType]
    section_index = ordered_sections_types.index(section_type)
    return ordered_sections_types[section_index + 1 :]


def parse_content(
    context: DocumentContext,
    elements: Sequence[PageElementOrString],
) -> list[PageElementOrString]:
    elements = parse_blockquotes(context, elements)
    elements = parse_section_titles(context, elements)
    elements = parse_sections(context, elements)
    return elements


def render_content(
    context: DocumentContext,
    elements: Sequence[PageElementOrString],
) -> Tag:
    content = make_new_tag(context.soup, "div")
    for tag in elements:
        if is_segmentation_tag(tag, tag_name_in=["section"]):
            content.append(render_section(context, tag))
        elif is_segmentation_tag(tag, tag_name_in=["table_of_contents"]):
            content.append(render_table_of_contents(context, tag))
        elif is_segmentation_tag(tag):
            raise ValueError(f"Unexpected tag {tag.name} in content")
        else:
            content.append(context.soup.new_tag("div", contents=tag))
    return content


def parse_section_titles(
    context: DocumentContext,
    elements: Sequence[PageElementOrString],
    lite: bool = False,
) -> list[PageElementOrString]:
    # First fix titles containing alinea
    # Do it only if we are not in lite mode as this is computation intensive
    if lite is False:
        elements = _fix_titles_containing_alineas(context, elements)

    # Then collect all section titles in list
    tag_list = _create_section_title_tags(context, elements)
    section_titles: list[Tag] = [
        e for e in tag_list if is_segmentation_tag(e, tag_name_in=["section_title"])
    ]

    # Ancestry order from root to the current section in the parsing context
    sections: int = 1

    # list of integers from previous section title
    current_global_levels: Optional[list[int]] = None

    # Previous list of integers extracted from the lastly seen section title for each section type
    current_titles_levels: Dict[SectionType, Optional[list[int]]] = {}

    # Considering the usual section types hierarchy, this dictionary helps improving the
    # hierarchy within the document, e.g. when finding titles, chapters and articles all having
    # only one number in their numberings, it adds minimal level for selecting the correct schema
    min_titles_levels: Dict[SectionType, int] = {}

    # Used to select the schema level for titles
    current_schema_level = -1

    for section_title in section_titles:
        title_text = get_string(section_title)
        data_extra: Dict = dict()

        # Parse title info
        title_info = parse_title_info(title_text)
        new_section_type = title_info.section_type

        # Add a tag if the titles are not contiguous
        current_title_levels = current_titles_levels.get(new_section_type)
        new_title_levels = list(title_info.levels) if title_info.levels else None

        if not is_next_title(current_global_levels, current_title_levels, new_title_levels):
            _LOGGER.warning(
                f"Detected title of levels {new_title_levels} after current global levels"
                f" {current_global_levels} and current section levels {current_title_levels}"
            )
            data_extra["error_codes"] = [ErrorCodes.non_contiguous_titles.value]

        current_global_levels = new_title_levels
        current_titles_levels[new_section_type] = new_title_levels

        # Process ancestry for new title
        new_schema_level = max(
            min_titles_levels.get(new_section_type, 0),
            len(new_title_levels) - 1 if new_title_levels else -1,
        )

        if new_schema_level - current_schema_level >= 1:
            # Nothing to do we just add the new section below the existing one
            pass
        elif new_schema_level - current_schema_level <= 0:
            # Empty the ancestry tree until we reach the right ancestor
            while new_schema_level - current_schema_level <= 0:
                sections -= 1
                current_schema_level = sections - 2
        else:
            raise RuntimeError(f"unexpected title {title_text}, current level {sections}")

        sections += 1
        current_schema_level = sections - 2

        downstream_sections_types = _get_downstream_sections_types(new_section_type)
        for downstream_section_type in downstream_sections_types:
            min_titles_levels[downstream_section_type] = max(
                min_titles_levels.get(downstream_section_type, 0),
                len(new_title_levels) if new_title_levels else 0,
            )

        update_segmentation_tag_data(
            section_title,
            dict(
                type=new_section_type.value,
                level=new_schema_level,
                number=title_info.number,
                title=title_info.text,
            ),
        )
        update_segmentation_tag_data(section_title, data_extra)

    return tag_list


@iter_func_to_list
def _fix_titles_containing_alineas(
    context: DocumentContext, elements: Sequence[PageElementOrString]
) -> Iterator[PageElementOrString]:
    for element in elements:
        if not is_segmentation_tag(element, tag_name_in=["text_span"]):
            yield element
            continue

        title_string = get_string(element)
        if not TITLE_NODE.pattern.match(title_string):
            yield element
            continue

        section_name, text = parse_title_text(title_string)
        result = split_at_first_verb(text)
        if result is None:
            yield element
            continue

        title_text, alinea_text = result
        # Return two segments: one for the title and one for the alinea
        if not title_text:
            title_text = section_name
        else:
            title_text = section_name + title_text

        # As we don't know exactly the split position in the original text,
        # we use an approximation of original position for source mapping.
        text_span_data = dict(
            start=read_segmentation_tag_data(element)["start"],
            end=read_segmentation_tag_data(element)["end"],
        )
        yield make_segmentation_tag(
            context.soup,
            "text_span",
            contents=[title_text],
            data=text_span_data,
        )
        yield make_segmentation_tag(
            context.soup,
            "text_span",
            contents=[alinea_text],
            data=text_span_data,
        )


def _create_section_title_tags(
    context: DocumentContext,
    elements: Sequence[PageElementOrString],
) -> list[PageElementOrString]:
    return map_splitted_elements(
        split_elements(
            elements,
            make_single_line_splitter_for_text_spans(is_title),
        ),
        lambda children: make_segmentation_tag(
            context.soup,
            "section_title",
            contents=children,
        ),
    )


@iter_func_to_list
def parse_sections(
    context: DocumentContext,
    elements: Sequence[PageElementOrString],
    level: int = 0,
) -> Iterator[PageElementOrString]:
    """
    Takes an input flow with already parsed section titles, and recursively
    creates sections that groups the section titles and their content together.

    For example, given the following input flow:

    <Title 1>
    <Title 1.1>
    <Content 1.1>
    <Title 2>
    <Content 2>

    the output will be:
    <Section 1>
        <Title 1>

        <Section 1.1>
            <Title 1.1>
            <Content 1.1>
        </Section 1.1>
    </Section 1>

    <Section 2>
        <Title 2>
        <Content 2>
    </Section 2>
    """
    elements = list(elements)
    pile: list[PageElementOrString] = []

    # 1. First, parse content encountered before the first sub-section title
    #
    # This is useful in 2 cases :
    # - when we have reached the leaf section level, and we need
    #       to parse alineas
    # - when there is content before the first section title (this is a special
    #       case and rarely happens).
    pile = []
    while elements and not is_segmentation_tag(elements[0], tag_name_in=["section_title"]):
        pile.append(elements.pop(0))
    if pile:
        yield from parse_alineas(context, pile)
    # 2. Second, we parse sections at deeper levels than the current `level`.
    #
    # This is useful in 2 cases :
    # - when there is no title at the current level, and we simply need to
    #       go deeper in the hierarchy
    # - when there is a missing section title at the current level,
    #       e.g. if the flow looks like this (Title 1 is missing) :
    #       <Title 1.1>
    #       <Title 1.2>
    #       <Title 2>
    #       <Title 2.1>
    #       <Title 3>
    pile = []
    while elements:
        if is_segmentation_tag(elements[0], tag_name_in=["section_title"]):
            element_level = cast(int, read_segmentation_tag_data(elements[0])["level"])
            if element_level == level:
                break
            elif element_level > level:
                pile.append(elements.pop(0))
            else:
                raise RuntimeError(
                    f"Unexpected section title level {element_level} " f"at level {level}"
                )
        else:
            pile.append(elements.pop(0))
    if pile:
        yield from parse_sections(context, pile, level=level + 1)
    # 3. Finally parse sections at current level
    pile = []
    while elements:
        # Add section title to the pile
        pile.append(elements.pop(0))

        # Fill-in the pile until we find next section title
        # of the same level
        while elements:
            if is_segmentation_tag(elements[0], tag_name_in=["section_title"]):
                element_level = cast(int, read_segmentation_tag_data(elements[0])["level"])
                if element_level == level:
                    break
                elif element_level < level:
                    raise RuntimeError(f"Unexpected section title level {element_level} ")
            pile.append(elements.pop(0))

        if pile:
            section_title, section_children = pile[0], pile[1:]
            yield make_segmentation_tag(
                context.soup,
                "section",
                contents=[section_title]
                + list(parse_sections(context, section_children, level=level + 1)),
            )
            pile = []


def render_section_title(
    context: DocumentContext,
    tag: Tag,
) -> Tag:
    if not is_segmentation_tag(tag, tag_name_in=["section_title"]):
        raise ValueError("Tag must be a section title")

    data: DataElementDataDict = dict()
    segmentation_tag_data = read_segmentation_tag_data(tag)
    if "error_codes" in segmentation_tag_data:
        data["error_codes"] = render_str_list_attribute(
            cast(list[str], segmentation_tag_data["error_codes"])
        )

    return make_semantic_tag(
        context.soup,
        SECTION_TITLE_SCHEMAS[cast(int, segmentation_tag_data["level"])],
        contents=[get_string(tag)],
        data=cast(DataElementDataDict, segmentation_tag_data),
    )


def render_section(
    context: DocumentContext,
    tag: Tag,
) -> Tag:
    if not is_segmentation_tag(tag, tag_name_in=["section"]):
        raise ValueError("Tag must be a section")

    assert is_segmentation_tag(
        tag.contents[0], tag_name_in=["section_title"]
    ), "First tag must be a section title"
    section_title: Tag = tag.contents[0]

    contents: list[PageElementOrString] = []
    for element in tag.contents:
        if is_segmentation_tag(element, tag_name_in=["section_title"]):
            contents.append(render_section_title(context, element))
        elif is_segmentation_tag(element, tag_name_in=["section"]):
            contents.append(render_section(context, element))
        elif is_segmentation_tag(element, tag_name_in=["alinea"]):
            contents.append(render_alinea(context, element))
        elif is_segmentation_tag(element, tag_name_in=["page_footer"]):
            contents.append(render_page_footer(context, element))
        elif is_segmentation_tag(element, tag_name_in=["table_of_contents"]):
            contents.append(render_table_of_contents(context, element))
        elif is_segmentation_tag(element, tag_name_in=["page_separator"]):
            contents.append(render_page_separator(context, element))
        elif isinstance(element, str):
            contents.append(element)
        elif is_segmentation_tag(element):
            raise ValueError(f"Unexpected tag {element.type} in section contents")

    section_segmentation_tag_data = read_segmentation_tag_data(section_title)
    return make_semantic_tag(
        context.soup,
        SECTION_SCHEMA,
        data=dict(
            type=str(section_segmentation_tag_data["type"]),
            number=str(section_segmentation_tag_data["number"]),
            title=(
                str(section_segmentation_tag_data["title"])
                if section_segmentation_tag_data["title"]
                else None
            ),
        ),
        contents=contents,
    )


# ALINEA : "Constitue un alinéa toute phrase, tout mot, tout ensemble de phrases ou de
# mots commençant à la ligne, précédés ou non d’un tiret, d’un point, d’une
# numérotation ou de guillemets, sans qu’il y ait lieu d’établir des distinctions selon
# la nature du signe placé à la fin de la ligne précédente (point, deux-points ou
# point-virgule). Un tableau constitue un seul alinéa (définition complète dans le
# guide de légistique)."
# REF : https://www.legifrance.gouv.fr/contenu/Media/files/lexique-api-lgf.docx
@iter_func_to_list
def parse_alineas(
    context: DocumentContext, elements: Sequence[PageElementOrString]
) -> Iterator[PageElementOrString]:
    alinea_count = 1
    elements = chain_functions(
        context,
        elements,
        [parse_tables, parse_lists, parse_images],
    )

    # Recombine interrupted lines before processing elements.
    # e.g.
    #   This is an alinea that
    #   <page_separator>
    #   continues on the next page.
    elements = map_splitted_elements(
        split_elements(
            elements,
            make_recombine_interrupted_lines_splitter("text_span"),
        ),
        lambda grouped_elements: combine_text_spans(context, grouped_elements),
    )

    while elements:
        element = elements.pop(0)
        # table_of_contents can appear here if we are in an annexe (then it isn't really an
        # alinea but that's how the detection works for now).
        if is_segmentation_tag(
            element, tag_name_in=["page_footer", "table_of_contents", "page_separator"]
        ):
            yield element
            continue

        alinea_children: list[PageElementOrString] = []
        if is_segmentation_tag(element, tag_name_in=["table"]):
            alinea_children = [element]
            while elements and is_segmentation_tag(elements[0], tag_name_in=["table_description"]):
                alinea_children.append(elements[0])
                elements.pop(0)

        else:
            alinea_children = [element]
        yield make_segmentation_tag(
            context.soup,
            "alinea",
            contents=alinea_children,
            data=dict(
                number=str(alinea_count),
            ),
        )
        alinea_count += 1


def render_alinea(
    context: DocumentContext,
    tag: Tag,
) -> Tag:
    contents: list[PageElementOrString] = []
    for element in tag.contents:
        if is_segmentation_tag(element, tag_name_in=["text_span"]):
            # TODO : move render_inline_quotes inside render_text_span
            text_span_elements = render_text_span(context, element)
            for text_span_element in text_span_elements:
                if isinstance(text_span_element, str):
                    contents.extend(render_inline_quotes(context, text_span_element))
                else:
                    contents.append(text_span_element)
        elif isinstance(element, Tag):
            contents.extend(render_basic_elements(context, element))
        elif isinstance(element, str):
            contents.extend(render_inline_quotes(context, element))
        else:
            raise ValueError(f"Unexpected tag {element} in alinea contents")

    alinea_segmentation_tag_data = read_segmentation_tag_data(tag)
    return make_semantic_tag(
        context.soup,
        ALINEA_SCHEMA,
        data=dict(number=str(alinea_segmentation_tag_data["number"])),
        contents=contents,
    )
