from typing import List
from enum import Enum
from dataclasses import dataclass

from bs4 import Tag, BeautifulSoup

from .sentence_rules import (
    is_arrete, is_entity, is_liste, is_motif, 
    is_table_description, is_visa, is_line_with_semicolumn
)
from bench_convertisseur_xml.utils.html import make_data_tag, PageElementOrString, wrap_in_tag
from bench_convertisseur_xml.utils.markdown import parse_markdown_table, is_table_line
from bench_convertisseur_xml.html_schemas import (
    SECTION_SCHEMA, SECTION_TITLE_SCHEMAS, ALINEA_SCHEMA)
from .config import BodySection
from .parse_section import parse_section
from .parse_list import parse_list


@dataclass
class _SectionParsingContext:
    alinea_count: int


def parse_main_content(soup: BeautifulSoup, main_content: Tag, lines: List[str], authorized_sections):
    pile: List[PageElementOrString] = []
    body_sections: List[Tag] = [main_content]

    # Consume lines until we detect the first section
    while lines:
        section_info = parse_section(lines[0], authorized_sections=authorized_sections)
        if section_info['type'] == BodySection.NONE:
            lines.pop(0)
            continue
        else:
            break

    while lines:
        section_info = parse_section(lines[0], authorized_sections=authorized_sections)
        section_element = make_data_tag(soup, SECTION_SCHEMA, data=dict(
            type=section_info['type'],
            number=section_info["number"],
            title=section_info["text"],
        ))

        new_section_level = section_info["level"]
        if new_section_level - (len(body_sections) - 2) >= 1:
            # Nothing to do we just add the new section below the existing one
            pass
        elif new_section_level - (len(body_sections) - 2) <= 0:
            while new_section_level - (len(body_sections) - 2) <= 0:
                body_sections.pop()
        else:
            raise RuntimeError(f'unexpected title {section_info}, current level {len(body_sections)}')

        section_context = _SectionParsingContext(alinea_count=0)
        def _create_alinea_element(contents: List[PageElementOrString]=[]):
            section_context.alinea_count += 1
            alinea_element = make_data_tag(
                soup, 
                ALINEA_SCHEMA, 
                contents=contents,
                data=dict(number=str(section_context.alinea_count))
            )
            section_element.append(alinea_element)
            return alinea_element

        body_sections[-1].append(section_element)
        body_sections.append(section_element)

        title_element = make_data_tag(soup, SECTION_TITLE_SCHEMAS[new_section_level], contents=[lines.pop(0)])
        section_element.append(title_element)

        while lines:
            section_info = parse_section(lines[0], authorized_sections=authorized_sections)
            if section_info['type'] != BodySection.NONE:
                break

            alinea_element = _create_alinea_element()

            while lines:
                if is_table_line(lines[0]):
                    pile = []

                    while lines and is_table_line(lines[0]):
                        pile.append(lines.pop(0))
                    alinea_element.append(parse_markdown_table(pile))

                    while lines and is_table_description(lines[0], pile):
                        alinea_element.append(soup.new_tag('br'))
                        alinea_element.append(lines.pop(0))
                    break
                    
                elif is_liste(lines[0]):
                    lines, ul_element = parse_list(soup, lines)
                    alinea_element.append(ul_element)
                    break

                # Normal paragraph
                else:
                    line = lines.pop(0)
                    alinea_element.append(line)
                    if not is_line_with_semicolumn(line):
                        break