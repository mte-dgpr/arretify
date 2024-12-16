from typing import List
from enum import Enum

from bs4 import Tag, BeautifulSoup

from .sentence_rules import (
    is_arrete, is_continuing_sentence, is_entity, is_liste, is_motif, is_not_information, 
    is_table, is_table_description, is_visa
)
from bench_convertisseur_xml.utils.html import make_element, PageElementOrString, wrap_in_paragraphs
from bench_convertisseur_xml.utils.markdown import parse_markdown_table, clean_markdown
from bench_convertisseur_xml.html_schemas import (
    DIV_SCHEMA, PARAGRAPH_SCHEMA, SECTION_SCHEMA, TABLE_SCHEMA, LIST_SCHEMA, SECTION_TITLE_SCHEMA)
from .config import BodySection
from .parse_section import parse_section


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
        section_element = make_element(soup, SECTION_SCHEMA, dict(
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

        body_sections[-1].append(section_element)
        body_sections.append(section_element)

        title_element = make_element(soup, SECTION_TITLE_SCHEMA, contents=[lines.pop(0)])
        section_element.append(title_element)

        while lines and is_continuing_sentence(lines[0]):
            section_element.append(lines.pop(0))

        while lines:
            section_info = parse_section(lines[0], authorized_sections=authorized_sections)
            if section_info['type'] != BodySection.NONE:
                break

            if is_table(lines[0]):
                pile = []
                while lines and is_table(lines[0]) or is_table_description(lines[0], pile):
                    pile.append(lines.pop(0))
                table_element = parse_markdown_table(pile)
                body_sections[-1].append(table_element)
                
            elif is_liste(lines[0]):
                pile = []
                while lines and is_liste(lines[0]):
                    pile.append(lines.pop(0))
                list_element = make_element(soup, LIST_SCHEMA, contents=wrap_in_paragraphs(soup, pile))
                body_sections[-1].append(list_element)

            # Normal paragraph
            else:
                paragraph_element = make_element(soup, PARAGRAPH_SCHEMA)
                paragraph_element.append(lines.pop(0))
                section_element.append(paragraph_element)
                # If line starts with lowercase, we might have changed page
                while lines and is_continuing_sentence(lines[0]):
                    paragraph_element.append(lines.pop(0))
        