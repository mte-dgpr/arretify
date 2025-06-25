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

from arretify.types import SectionType, PageElementOrString, DataElementDataDict
from arretify.utils.html import (
    make_data_tag,
    render_str_list_attribute,
)
from arretify.html_schemas import (
    SECTION_SCHEMA,
    SECTION_TITLE_SCHEMAS,
    ALINEA_SCHEMA,
)
from arretify.parsing_utils.source_mapping import TextSegments
from arretify.errors import ErrorCodes
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
    Node,
    NodeFlow,
    is_node,
    assert_single_text_segment,
    flat_map_node_flow,
)
from .document_elements import (
    parse_parse_page_footer,
    parse_table_of_contents,
    render_page_footer,
    render_table_of_contents,
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

    parsed_content = list(parse_content(pile))
    rendered_content = render_content(soup, parsed_content)
    content.extend(list(rendered_content.children))
    return lines


def _get_downstream_sections_types(section_type):
    ordered_sections_types = [section_type for section_type in SectionType]
    section_index = ordered_sections_types.index(section_type)
    return ordered_sections_types[section_index + 1 :]


def parse_content(
    lines: TextSegments,
) -> NodeFlow:
    node_flow: NodeFlow = [lines]
    # Image strings can be very long, and table of contents pattern look
    # at the end of the sentence.
    # So, we make sure we parse images before table of contents.
    node_flow = flat_map_node_flow(
        node_flow,
        parse_images,
    )
    node_flow = flat_map_node_flow(
        node_flow,
        parse_parse_page_footer,
    )
    node_flow = flat_map_node_flow(
        node_flow,
        parse_table_of_contents,
    )
    node_flow = flat_map_node_flow(
        node_flow,
        parse_blockquotes,
    )
    node_flow = parse_section_titles(node_flow)
    node_flow = parse_sections(node_flow)
    yield from node_flow


def render_content(
    soup: BeautifulSoup,
    node_flow: NodeFlow,
) -> Tag:
    content = soup.new_tag("div")
    for node in node_flow:
        if is_node(node, type_in=["section"]):
            content.append(render_section(soup, node))
        elif is_node(node):
            raise ValueError(f"Unexpected node {node.type} in content")
        else:
            content.append(soup.new_tag("div", contents=node))
    return content


def parse_section_titles(
    node_flow_: NodeFlow,
) -> NodeFlow:
    node_flow = list(node_flow_)

    # First collect all section titles in output_flow.
    output_flow = flat_map_node_flow(node_flow, _create_section_title_nodes)
    section_titles: List[Node] = [e for e in output_flow if is_node(e, type_in=["section_title"])]

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
            title=title_info.text,
        )
        section_title.data.update(data_extra)

    yield from output_flow


def _create_section_title_nodes(
    lines: TextSegments,
) -> NodeFlow:
    lines = list(lines)
    pile: TextSegments = []
    while lines:
        while lines and not is_title(lines[0].contents):
            pile.append(lines.pop(0))
        if pile:
            yield pile
            pile = []

        if lines:
            section_title = Node(type="section_title", children=[[lines.pop(0)]])
            yield section_title


def parse_sections(
    node_flow_: NodeFlow,
    level: int = 0,
) -> NodeFlow:
    node_flow = list(node_flow_)
    pile: List[Node | TextSegments] = []

    # 1. If there is content before the first sub-section title, we parse it as
    # alineas in the current section.
    pile = []
    while node_flow and not is_node(node_flow[0], type_in=["section_title"]):
        pile.append(node_flow.pop(0))
    if pile:
        yield from parse_alineas(pile)

    # 2. If there are sections at deeper levels we parse them first, by calling
    # the function recursively.
    pile = []
    while node_flow:
        if is_node(node_flow[0], type_in=["section_title"]):
            if node_flow[0].data["level"] == level:
                break
            elif node_flow[0].data["level"] > level:
                pile.append(node_flow.pop(0))
            else:
                raise RuntimeError(
                    f"Unexpected section title level {node_flow[0].data['level']} "
                    f"at level {level}"
                )
        else:
            pile.append(node_flow.pop(0))
    if pile:
        yield from parse_sections(pile, level=level + 1)

    # 3. Finally parse sections at current level
    pile = []
    while node_flow:
        # Add section title to the pile
        pile.append(node_flow.pop(0))

        # Fill-in the pile until we find next section title
        # of the same level
        while node_flow:
            if is_node(node_flow[0], type_in=["section_title"]):
                if node_flow[0].data["level"] == level:
                    break
                elif node_flow[0].data["level"] < level:
                    raise RuntimeError(
                        f"Unexpected section title level {node_flow[0].data['level']} "
                    )
            pile.append(node_flow.pop(0))

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
    for node_or_text_segments in node.children:
        if is_node(node_or_text_segments, type_in=["section_title"]):
            contents.append(render_section_title(soup, node_or_text_segments))
        elif is_node(node_or_text_segments, type_in=["section"]):
            contents.append(render_section(soup, node_or_text_segments))
        elif is_node(node_or_text_segments, type_in=["alinea"]):
            contents.append(render_alinea(soup, node_or_text_segments))
        elif is_node(node_or_text_segments, type_in=["page_footer"]):
            contents.append(render_page_footer(soup, node_or_text_segments))
        elif is_node(node_or_text_segments, type_in=["table_of_contents"]):
            contents.append(render_table_of_contents(soup, node_or_text_segments))
        elif is_node(node_or_text_segments):
            raise ValueError(f"Unexpected node {node_or_text_segments.type} in section contents")
        else:
            assert not isinstance(node_or_text_segments, Node)
            contents.extend(t.contents for t in node_or_text_segments)

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
    node_flow_: NodeFlow,
) -> Iterator[Node]:
    node_flow_ = list(node_flow_)
    alinea_count = 1

    node_flow_ = flat_map_node_flow(
        node_flow_,
        parse_tables,
    )
    node_flow_ = flat_map_node_flow(
        node_flow_,
        parse_lists,
    )
    node_flow_ = flat_map_node_flow(
        node_flow_,
        parse_images,
    )
    node_flow = list(node_flow_)

    while node_flow:
        node_or_text_segments = node_flow.pop(0)
        if is_node(node_or_text_segments, type_in=["page_footer", "table_of_contents"]):
            yield node_or_text_segments

        elif isinstance(node_or_text_segments, Node):
            children: List[Node | TextSegments] = [node_or_text_segments]
            if node_or_text_segments.type == "table":
                while (
                    node_flow
                    and isinstance(node_flow[0], Node)
                    and node_flow[0].type == "table_description"
                ):
                    children.append(node_flow.pop(0))

            yield Node(
                type="alinea",
                children=children,
                data=dict(
                    number=str(alinea_count),
                ),
            )
            alinea_count += 1

        else:
            for line in node_or_text_segments:
                yield Node(
                    type="alinea",
                    children=[[line]],
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
    for node_or_text_segments in node.children:
        if isinstance(node_or_text_segments, Node):
            contents.extend(render_basic_elements(soup, node_or_text_segments))
        else:
            assert (
                len(node_or_text_segments) == 1
            ), "Alinea node should contain exactly one TextSegments"
            contents.extend(_parse_inline_quotes(soup, node_or_text_segments[0].contents))

    return make_data_tag(
        soup,
        ALINEA_SCHEMA,
        data=dict(number=str(node.data["number"])),
        contents=contents,
    )
