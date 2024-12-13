from typing import List
from enum import Enum

from bs4 import Tag, BeautifulSoup

from .sentence_rules import (
    is_arrete, is_continuing_sentence, is_entity, is_liste, is_motif, is_not_information, 
    is_table, is_table_description, is_visa
)
from .utils import clean_markdown
from bench_convertisseur_xml.utils.html import make_element, PageElementOrString
from bench_convertisseur_xml.types import ElementSchema
from .config import BodySection, section_from_name
from .utils import clean_markdown
from .parse_section import parse_section

TABLE_SCHEMA = ElementSchema(
    name="table",
    tag_name="div",
    classes=["dsr-table"],
    data_keys=[],
)

DIV_SCHEMA = ElementSchema(
    name="div",
    tag_name="div",
    classes=[],
    data_keys=[],
)

SECTION_SCHEMA = ElementSchema(
    name="section",
    tag_name="div",
    classes=['dsr-section'],
    data_keys=['text', 'number', 'type'],
)

TITLE_SCHEMA = ElementSchema(
    name="title",
    tag_name="div",
    classes=['dsr-title'],
    data_keys=[],
)

PARAGRAPH_SCHEMA = ElementSchema(
    name="paragraph",
    tag_name="p",
    classes=[],
    data_keys=[],
)

LIST_SCHEMA = ElementSchema(
    name="list",
    tag_name="div",
    classes=[],
    data_keys=[],
)

def _get_body_section(line: str, authorized_sections):
    new_section_info = parse_section(line, authorized_sections=authorized_sections)
    new_section_name = new_section_info["section_name"]
    return section_from_name(new_section_name)


def _process_pile(soup: BeautifulSoup, pile: List[str]):
    """Traite la pile de lignes et les ajoute à la section XML"""
    # Si la ligne n'est pas vide
    return [
        make_element(soup, DIV_SCHEMA, contents=[line]) if isinstance(line, str) else line
        for line in pile if (not isinstance(line, str) or line.strip())
    ]


def _ensure_ul_element(soup: BeautifulSoup, container: Tag | str, string: str):
    if not isinstance(container, Tag):
        ul = soup.new_tag('ul')
        li = soup.new_tag('li')
        li.append(container)
        ul.append(li)
    else:
        ul = container
    li = soup.new_tag('li')
    li.append(string)
    ul.append(li)
    return ul    


def parse_main_content(soup: BeautifulSoup, lines: List[str], authorized_sections):
    pile: List[PageElementOrString] = []
    max_section_level = len(authorized_sections)
    body_sections: List[Tag] = [soup.body]
    current_section_type = BodySection.NONE
    current_element: Tag | None = None

    while lines:
        new_section_info = parse_section(lines[0], authorized_sections=authorized_sections)
        new_section_name = new_section_info["section_name"]
        new_section_type = section_from_name(new_section_name)

        if new_section_type != BodySection.NONE:
            new_element = make_element(soup, SECTION_SCHEMA, dict(
                type=new_section_name,
                number=new_section_info["number"],
                text=new_section_info["text"],
            ))

            new_section_level = new_section_info["level"]
            if new_section_level - (len(body_sections) - 2) == 1:
                # Nothing to do we just add the new section below the existing one
                pass
            elif new_section_level - (len(body_sections) - 2) <= 0:
                while new_section_level - (len(body_sections) - 2) <= 0:
                    body_sections.pop()
            else:
                raise RuntimeError(f'unexpected title {new_section_info}, current level {len(body_sections)}')

            body_sections[-1].append(new_element)
            body_sections.append(new_element)

            current_section_type = new_section_type

            title_element = make_element(soup, TITLE_SCHEMA, contents=[lines.pop(0)])
            new_element.append(title_element)

        if is_table(lines[0]):
            pile = []
            while is_table(lines[0]) or is_table_description(lines[0], pile):
                pile.append(lines.pop(0))            
            table_element = make_element(soup, TABLE_SCHEMA, contents=_process_pile(soup, pile))
            body_sections[-1].append(
                table_element
            )
            current_element = table_element
            
        elif is_liste(lines[0]):
            pile = []
            while is_liste(lines[0]):
                pile.append(lines.pop(0))
            list_element = make_element(soup, LIST_SCHEMA, contents=_process_pile(soup, pile))
            body_sections[-1].append(list_element)
            current_element = list_element

        # Normal paragraph
        else:
            # If line starts with lowercase, we might have changed page
            if is_continuing_sentence(lines[0]) and current_section_type == BodySection.PARAGRAPH:
                assert current_element
                current_element.append(lines.pop(0))

            # If this is a paragraph before the first section
            elif len(body_sections) == 1:
                lines.pop(0)
                continue

            # Otherwise new element
            else:
                new_element = make_element(soup, PARAGRAPH_SCHEMA)
                body_sections[-1].append(new_element)
                new_element.append(lines.pop(0))
                current_element = new_element

                # Change section type
                current_section_type = BodySection.PARAGRAPH
        