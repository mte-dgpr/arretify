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

from arretify.types import SectionType, PageElementOrString, DataElementDataDict, TextSegment
from arretify.utils.html import (
    render_str_list_attribute,
)
from arretify.utils.html_create import make_data_tag
from arretify.utils.functional import iter_func_to_list, chain_functions
from arretify.html_schemas import (
    SECTION_SCHEMA,
    SECTION_TITLE_SCHEMAS,
    ALINEA_SCHEMA,
)
from arretify.errors import ErrorCodes
from arretify.parsing_utils.patterns import is_continuing_sentence
from .basic_elements import (
    render_basic_elements,
    render_inline_quotes,
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
    parse_title_info,
    is_next_title,
    TITLE_NODE,
)
from .core import (
    Node,
    NodeOrText,
    is_node,
    assert_single_text_segment,
    make_single_line_splitter_for_text_segments,
    make_probe_from_pattern,
)
from .document_elements import (
    render_page_footer,
    render_table_of_contents,
    render_page_separator,
)


_LOGGER = logging.getLogger(__name__)


_is_title = make_probe_from_pattern(
    TITLE_NODE.pattern,
)


def _get_downstream_sections_types(section_type):
    ordered_sections_types = [section_type for section_type in SectionType]
    section_index = ordered_sections_types.index(section_type)
    return ordered_sections_types[section_index + 1 :]


def parse_content(
    elements: List[NodeOrText],
) -> List[NodeOrText]:
    elements = parse_blockquotes(elements)
    elements = parse_section_titles(elements)
    elements = parse_sections(elements)
    return elements


def render_content(
    soup: BeautifulSoup,
    elements: List[NodeOrText],
) -> Tag:
    content = soup.new_tag("div")
    for node in elements:
        if is_node(node, type_in=["section"]):
            content.append(render_section(soup, node))
        elif is_node(node, type_in=["table_of_contents"]):
            content.append(render_table_of_contents(soup, node))
        elif is_node(node):
            raise ValueError(f"Unexpected node {node.type} in content")
        else:
            content.append(soup.new_tag("div", contents=node))
    return content


def split_section_titles(lines: TextSegments) -> TextSegments:

    lines = list(lines)

    for i, line in enumerate(lines):

        if is_title(line.contents):

            # Parse title info
            title_info = parse_title_info(line.contents)

            # If the section title contains alinea text, add it to the list
            if title_info.alinea_text:

                # TODO: fix insertion of alinea text
                # Insert alinea text after section title
                lines.insert(
                    i + 1,
                    TextSegment((0, 0), (0, len(title_info.alinea_text)), title_info.alinea_text),
                )

                # Remove alinea text from title contents
                title_contents = line.contents.replace(title_info.alinea_text, "")
                lines[i] = TextSegment(
                    (lines[i].start[0], 0), (lines[i].end[0], len(title_contents)), title_contents
                )

    return lines


def parse_section_titles(
    elements: List[NodeOrText],
) -> List[NodeOrText]:
    # First collect all section titles in output_flow.
    node_list = _create_section_title_nodes(elements)
    section_titles: List[Node] = [e for e in node_list if is_node(e, type_in=["section_title"])]

    # Ancestry order from root to the current section in the parsing context
    sections: int = 1

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
        data_extra: Dict = dict()

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

        section_title.data.update(
            type=new_section_type.value,
            level=new_schema_level,
            number=title_info.number,
            title=title_info.title_text,
        )
        section_title.data.update(data_extra)

    return node_list


def _create_section_title_nodes(
    elements: List[NodeOrText],
) -> List[NodeOrText]:
    return map_splitted_elements(
        split_elements(
            elements,
            make_single_line_splitter_for_text_segments(_is_title),
        ),
        lambda text_segments: Node(
            type="section_title",
            children=text_segments,
        ),
    )


@iter_func_to_list
def parse_sections(
    elements: List[NodeOrText],
    level: int = 0,
) -> Iterator[NodeOrText]:
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
    pile: List[NodeOrText] = []

    # 1. First, parse content encountered before the first sub-section title
    #
    # This is useful in 2 cases :
    # - when we have reached the leaf section level, and we need
    #       to parse alineas
    # - when there is content before the first section title (this is a special
    #       case and rarely happens).
    pile = []
    while elements and not is_node(elements[0], type_in=["section_title"]):
        pile.append(elements.pop(0))
    if pile:
        yield from parse_alineas(pile)

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
        if is_node(elements[0], type_in=["section_title"]):
            if elements[0].data["level"] == level:
                break
            elif elements[0].data["level"] > level:
                pile.append(elements.pop(0))
            else:
                raise RuntimeError(
                    f"Unexpected section title level {elements[0].data['level']} "
                    f"at level {level}"
                )
        else:
            pile.append(elements.pop(0))
    if pile:
        yield from parse_sections(pile, level=level + 1)

    # 3. Finally parse sections at current level
    pile = []
    while elements:
        # Add section title to the pile
        pile.append(elements.pop(0))

        # Fill-in the pile until we find next section title
        # of the same level
        while elements:
            if is_node(elements[0], type_in=["section_title"]):
                if elements[0].data["level"] == level:
                    break
                elif elements[0].data["level"] < level:
                    raise RuntimeError(
                        f"Unexpected section title level {elements[0].data['level']} "
                    )
            pile.append(elements.pop(0))

        if pile:
            section_title, section_children = pile[0], pile[1:]
            yield Node(
                type="section",
                children=[section_title] + list(parse_sections(section_children, level=level + 1)),
            )
            pile = []


def render_section_title(
    soup: BeautifulSoup,
    node: Node,
) -> Tag:
    if not is_node(node, type_in=["section_title"]):
        raise ValueError("Node must be a section title")

    data: DataElementDataDict = dict()
    if "error_codes" in node.data:
        data["error_codes"] = render_str_list_attribute(node.data["error_codes"])

    return make_data_tag(
        soup,
        SECTION_TITLE_SCHEMAS[node.data["level"]],
        contents=[assert_single_text_segment(node).contents],
        data=data,
    )


def render_section(
    soup: BeautifulSoup,
    node: Node,
) -> Tag:
    if not is_node(node, type_in=["section"]):
        raise ValueError("Node must be a section")

    assert is_node(
        node.children[0], type_in=["section_title"]
    ), "First node must be a section title"
    section_title: Node = node.children[0]

    contents: List[PageElementOrString] = []
    for element in node.children:
        if is_node(element, type_in=["section_title"]):
            contents.append(render_section_title(soup, element))
        elif is_node(element, type_in=["section"]):
            contents.append(render_section(soup, element))
        elif is_node(element, type_in=["alinea"]):
            contents.append(render_alinea(soup, element))
        elif is_node(element, type_in=["page_footer"]):
            contents.append(render_page_footer(soup, element))
        elif is_node(element, type_in=["table_of_contents"]):
            contents.append(render_table_of_contents(soup, element))
        elif is_node(element, type_in=["page_separator"]):
            contents.append(render_page_separator(soup, element))
        elif isinstance(element, TextSegment):
            contents.append(element.contents)
        elif is_node(element):
            raise ValueError(f"Unexpected node {element.type} in section contents")

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


# ALINEA : "Constitue un alinéa toute phrase, tout mot, tout ensemble de phrases ou de
# mots commençant à la ligne, précédés ou non d’un tiret, d’un point, d’une
# numérotation ou de guillemets, sans qu’il y ait lieu d’établir des distinctions selon
# la nature du signe placé à la fin de la ligne précédente (point, deux-points ou
# point-virgule). Un tableau constitue un seul alinéa (définition complète dans le
# guide de légistique)."
# REF : https://www.legifrance.gouv.fr/contenu/Media/files/lexique-api-lgf.docx
@iter_func_to_list
def parse_alineas(
    elements: List[NodeOrText],
) -> Iterator[NodeOrText]:
    alinea_count = 1
    elements = chain_functions(
        elements,
        [parse_tables, parse_lists, parse_images],
    )

    while elements:
        element = elements.pop(0)
        # table_of_contents can appear here if we are in an annexe (then it isn't really an
        # alinea but that's how the detection works for now).
        if is_node(element, type_in=["page_footer", "table_of_contents", "page_separator"]):
            yield element
            continue

        alinea_children: List[NodeOrText] = []
        if isinstance(element, Node):
            alinea_children = [element]
            if element.type == "table":
                while (
                    elements
                    and isinstance(elements[0], Node)
                    and elements[0].type == "table_description"
                ):
                    alinea_children.append(elements[0])
                    elements.pop(0)

        else:
            if (
                len(elements) >= 2
                and is_node(elements[0], type_in=["page_separator"])
                and isinstance(elements[1], TextSegment)
                and is_continuing_sentence(
                    element.contents,
                    elements[1].contents,
                )
            ):
                alinea_children = [element, elements[0], elements[1]]
                elements.pop(0)
                elements.pop(0)

            else:
                alinea_children = [element]

        yield Node(
            type="alinea",
            children=alinea_children,
            data=dict(
                number=str(alinea_count),
            ),
        )
        alinea_count += 1


def render_alinea(
    soup: BeautifulSoup,
    node: Node,
) -> Tag:
    contents: List[PageElementOrString] = []
    for element in node.children:
        if isinstance(element, Node):
            contents.extend(render_basic_elements(soup, element))
        else:
            contents.extend(render_inline_quotes(soup, element.contents))

    return make_data_tag(
        soup,
        ALINEA_SCHEMA,
        data=dict(number=str(node.data["number"])),
        contents=contents,
    )
