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
from typing import Dict, List, Optional, Iterator
import logging

from bs4 import (
    BeautifulSoup,
    Tag,
)

from arretify.types import SectionType, PageElementOrString
from arretify.utils.html import (
    make_data_tag,
)
from arretify.html_schemas import (
    SECTION_SCHEMA,
    SECTION_TITLE_SCHEMAS,
    ALINEA_SCHEMA,
)
from arretify.parsing_utils.source_mapping import TextSegments
from .basic_elements import (
    render_basic_elements,
    _parse_inline_quotes,
    parse_tables,
    parse_lists,
    parse_images,
    parse_blockquotes,
)
from .titles_detection import (
    is_title,
    parse_title_info,
    is_next_title,
)
from .core import (
    Element,
    ElementFlow,
    is_element,
    assert_single_text_segment,
    flat_map_element_flow,
)


_LOGGER = logging.getLogger(__name__)


def parse_content_DEPRECATED(
    soup: BeautifulSoup,
    content: Tag,
    lines: TextSegments,
    exit_on_appendix: bool = True,
) -> TextSegments:
    pile: TextSegments = []

    if exit_on_appendix:
        while lines:
            if is_title(lines[0].contents):
                # Parse title info
                title_info = parse_title_info(lines[0].contents)
                new_section_type = title_info.section_type

                # Appendix is considered as a different part of the document
                if new_section_type == SectionType.ANNEXE:
                    break

            pile.append(lines.pop(0))
    else:
        pile = lines

    rendered_content = render_content(soup, parse_content(pile))
    content.extend(list(rendered_content.children))
    return lines


def _get_downstream_sections_types(section_type):
    ordered_sections_types = [section_type for section_type in SectionType]
    section_index = ordered_sections_types.index(section_type)
    return ordered_sections_types[section_index + 1 :]


def parse_content(
    lines: TextSegments,
) -> ElementFlow:
    element_flow: ElementFlow = [lines]
    # element_flow = flat_map_element_flow(
    #     element_flow,
    #     parse_document_elements,
    # )
    element_flow = flat_map_element_flow(
        element_flow,
        parse_blockquotes,
    )
    element_flow = flat_map_element_flow(
        element_flow,
        parse_section_titles,
    )
    element_flow = parse_sections(element_flow)
    yield from element_flow


def render_content(
    soup: BeautifulSoup,
    element_flow: ElementFlow,
) -> Tag:
    content = soup.new_tag("div")
    for element in element_flow:
        if is_element(element, name="section"):
            content.append(render_section(soup, element))
        elif is_element(element):
            raise ValueError(f"Unexpected element {element.name} in content")
        else:
            content.append(soup.new_tag("div", contents=element))
    return content


def parse_section_titles(
    lines: TextSegments,
) -> ElementFlow:
    lines = lines[:]
    pile: TextSegments = []
    section_titles: List[Element] = []
    output_flow: List[Element | TextSegments] = []

    while lines:
        while lines and not is_title(lines[0].contents):
            pile.append(lines.pop(0))
        if pile:
            output_flow.append(pile)
            pile = []

        if lines:
            section_title = Element(name="section_title", contents=[[lines.pop(0)]])
            section_titles.append(section_title)
            output_flow.append(section_title)

    # Ancestry order from root to the current section in the parsing context
    sections: int = 1  # [content]

    # List of integers from previous section title
    current_global_levels: Optional[List[int]] = None

    # Previous list of integers extracted from the lastly seen section title for each section type
    current_titles_levels: Dict[SectionType, Optional[List[int]]] = {}

    # Considering the usual section types hierarchy, this dictionary helps improving the
    # hierarchy within the document, e.g. when finding titles, chapters and articles all having
    # only one number in their numberings, it adds minimal level for selecting the correct schema
    min_titles_levels: Dict[SectionType, int] = {}

    # Used to select the schema level for titles
    current_schema_level = -1

    for section_title in section_titles:
        title_text = assert_single_text_segment(section_title).contents

        # Parse title info
        title_info = parse_title_info(title_text)
        new_section_type = title_info.section_type

        # Add a tag if the titles are not contiguous
        current_title_levels = current_titles_levels.get(new_section_type)
        new_title_levels = title_info.levels

        if not is_next_title(current_global_levels, current_title_levels, new_title_levels):

            _LOGGER.warning(
                f"Detected title of levels {new_title_levels} after current global levels"
                f" {current_global_levels} and current section levels {current_title_levels}"
            )

            # title_element_data["error_codes"] = render_str_list_attribute(
            #     [ErrorCodes.non_contiguous_titles.value]
            # )

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
                sections -= 1  # sections.pop()
                current_schema_level = sections - 2  # len(sections) - 2
        else:
            raise RuntimeError(f"unexpected title {title_text}, current level {sections}")

        sections += 1  # sections.append(section_element)
        current_schema_level = sections - 2  # len(sections) - 2

        downstream_sections_types = _get_downstream_sections_types(new_section_type)
        for downstream_section_type in downstream_sections_types:
            min_titles_levels[downstream_section_type] = max(
                min_titles_levels.get(downstream_section_type, 0),
                len(new_title_levels) if new_title_levels else 0,
            )

        section_title.data.update(
            type=new_section_type.value,
            level=new_schema_level,
            number=title_info.number,
            title=title_info.text,
        )

    yield from output_flow


def parse_sections(
    element_flow_: ElementFlow,
    level: int = 0,
) -> ElementFlow:
    element_flow = list(element_flow_)
    pile: List[Element | TextSegments] = []

    # We start by finding the first sub-section title at the
    # current level.
    pile = []
    has_sub_sections = False
    while element_flow:
        if is_element(element_flow[0], name="section_title"):
            if element_flow[0].data["level"] == level:
                break
            elif element_flow[0].data["level"] > level:
                has_sub_sections = True
            else:
                raise RuntimeError(
                    f"Unexpected section title level {element_flow[0].data['level']} "
                    f"at level {level}"
                )
        pile.append(element_flow.pop(0))

    # Special case : we have no section title at the current level (*),
    # but we do have sections at deeper level (**).
    if not element_flow and has_sub_sections:  # (*)  # (**)
        yield from parse_sections(pile, level=level + 1)
        return

    # If there is content before the first sub-section title, we parse it as
    # alineas in the current section.
    elif pile:
        yield from parse_alineas(pile)

    pile = []
    while element_flow:
        # Add section title to the pile
        pile.append(element_flow.pop(0))

        # Fill-in the pile until we find next section title
        # of the same level
        while element_flow:
            if is_element(element_flow[0], name="section_title"):
                if element_flow[0].data["level"] == level:
                    break
                elif element_flow[0].data["level"] < level:
                    raise RuntimeError(
                        f"Unexpected section title level {element_flow[0].data['level']} "
                    )
            pile.append(element_flow.pop(0))

        if pile:
            section_title, section_content = pile[0], pile[1:]
            yield Element(
                name="section",
                contents=[section_title] + list(parse_sections(section_content, level + 1)),
            )
            pile = []


def render_section_title(
    soup: BeautifulSoup,
    element: Element,
) -> Tag:
    if not is_element(element, name="section_title"):
        raise ValueError("Element must be a section title")

    return make_data_tag(
        soup,
        SECTION_TITLE_SCHEMAS[element.data["level"]],
        # TODO : data error codes
        contents=[assert_single_text_segment(element).contents],
    )


def render_section(
    soup: BeautifulSoup,
    element: Element,
) -> Tag:
    if not is_element(element, name="section"):
        raise ValueError("Element must be a section")

    assert is_element(
        element.contents[0], name="section_title"
    ), "First element must be a section title"
    section_title: Element = element.contents[0]

    contents: List[PageElementOrString] = []
    for element_or_text_segments in element.contents:
        if is_element(element_or_text_segments, name="section_title"):
            contents.append(render_section_title(soup, element_or_text_segments))
        elif is_element(element_or_text_segments, name="section"):
            contents.append(render_section(soup, element_or_text_segments))
        elif is_element(element_or_text_segments, name="alinea"):
            contents.append(render_alinea(soup, element_or_text_segments))
        elif is_element(element_or_text_segments):
            raise ValueError(
                f"Unexpected element {element_or_text_segments.name} in section contents"
            )
        else:
            assert not isinstance(element_or_text_segments, Element)
            contents.extend(t.contents for t in element_or_text_segments)

    return make_data_tag(
        soup,
        SECTION_SCHEMA,
        data=dict(
            type=section_title.data["type"],
            number=section_title.data["number"],
            title=section_title.data["title"],
        ),
        contents=contents,
    )


# Parse alineas until a new section is detected
# ALINEA : "Constitue un alinéa toute phrase, tout mot, tout ensemble de phrases ou de
# mots commençant à la ligne, précédés ou non d’un tiret, d’un point, d’une
# numérotation ou de guillemets, sans qu’il y ait lieu d’établir des distinctions selon
# la nature du signe placé à la fin de la ligne précédente (point, deux-points ou
# point-virgule). Un tableau constitue un seul alinéa (définition complète dans le
# guide de légistique)."
# REF : https://www.legifrance.gouv.fr/contenu/Media/files/lexique-api-lgf.docx
def parse_alineas(
    element_flow_: ElementFlow,
) -> Iterator[Element]:
    element_flow_ = list(element_flow_)
    alinea_count = 1

    element_flow_ = flat_map_element_flow(
        element_flow_,
        parse_tables,
    )
    element_flow_ = flat_map_element_flow(
        element_flow_,
        parse_lists,
    )
    element_flow_ = flat_map_element_flow(
        element_flow_,
        parse_images,
    )
    element_flow = list(element_flow_)

    while element_flow:
        element_or_text_segments = element_flow.pop(0)
        if isinstance(element_or_text_segments, Element):
            contents: List[Element | TextSegments] = [element_or_text_segments]
            if element_or_text_segments.name == "table":
                while (
                    element_flow
                    and isinstance(element_flow[0], Element)
                    and element_flow[0].name == "table_description"
                ):
                    contents.append(element_flow.pop(0))

            yield Element(
                name="alinea",
                contents=contents,
                data=dict(
                    number=str(alinea_count),
                ),
            )
            alinea_count += 1
        else:
            for line in element_or_text_segments:
                yield Element(
                    name="alinea",
                    contents=[[line]],
                    data=dict(
                        number=str(alinea_count),
                    ),
                )
                alinea_count += 1


def render_alinea(
    soup: BeautifulSoup,
    element: Element,
) -> Tag:
    contents: List[PageElementOrString] = []
    for element_or_text_segments in element.contents:
        if isinstance(element_or_text_segments, Element):
            contents.extend(render_basic_elements(soup, element_or_text_segments))
        else:
            assert (
                len(element_or_text_segments) == 1
            ), "Alinea element should contain exactly one TextSegments"
            contents.extend(_parse_inline_quotes(soup, element_or_text_segments[0].contents))

    return make_data_tag(
        soup,
        ALINEA_SCHEMA,
        data=dict(number=str(element.data["number"])),
        contents=contents,
    )
