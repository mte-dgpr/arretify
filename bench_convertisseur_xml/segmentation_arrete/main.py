"""Main file to convert TXT files to XML output."""


import re
from pathlib import Path

from typing import List, Dict
from dataclasses import dataclass
from xml.etree.ElementTree import Element, SubElement, tostring
import xml.dom.minidom

from .config import BodySection, HeaderSection
from .section_rules import preprocess_section_types
from .sentence_rules import (
    is_arrete, is_continuing_sentence, is_entity, is_liste, is_motif, is_not_information, is_table,
    is_visa
)
from .utils import clean_markdown
from ..settings import TEST_DATA_DIR


@dataclass
class XMLGroup:
    """Classe représentant une section de document avec son niveau hiérarchique"""
    title: str
    content: List[str]
    level: int
    attributes: Dict[str, str] = None


class DocumentParser:
    def __init__(self):

        self.root = Element("documents")

        self.current_document = None

        self.header = None
        self.in_header = False
        self.header_sections = []

        self.patterns = {}
        self.patterns_levels = {}

        self.body = None
        self.in_body = False
        self.body_sections = []
        self.paragraphs = []

        self.current_section_level = -1
        self.current_section_type = HeaderSection.NONE

    def parse_document(self, content: List[str]) -> Element:
        """Point d'entrée principal du parsing"""
        self.current_document = SubElement(self.root, "document")

        self.header = SubElement(self.current_document, "header")
        self.body = SubElement(self.current_document, "body")

        k_max = 50000000

        pile = []
        self.in_header = True

        patterns, patterns_levels = preprocess_section_types(content)
        self.patterns = patterns
        self.patterns_levels = patterns_levels
        self.body_sections = [[] for _ in range(len(self.patterns))]

        for k, line in enumerate(content):

            line = clean_markdown(line)

            # While we are in header
            if self.in_header:

                # Discarding all non useful information
                if is_not_information(line):
                    continue

                # Starting subsection entity
                if is_entity(line) and self.current_section_type == HeaderSection.NONE:

                    # No process required as we start the document
                    pile.append(line)

                    self.current_section_type = HeaderSection.ENTITY
                    self.header_sections.append(SubElement(self.header, "entity"))

                # Continue feeding subsection entity
                elif is_entity(line) and self.current_section_type == HeaderSection.ENTITY:

                    pile.append(line)

                # Starting subsection identification
                elif is_arrete(line) and self.current_section_type == HeaderSection.ENTITY:

                    self._process_pile(pile, self.header_sections[-1])
                    pile = [line]

                    self.current_section_type = HeaderSection.IDENTIFICATION
                    self.header_sections.append(SubElement(self.header, "identification"))

                # Discard entity in subsection identification
                elif is_entity(line) and self.current_section_type == HeaderSection.IDENTIFICATION:
                    continue

                # Multi-line identification
                elif is_continuing_sentence(line) and self.current_section_type == HeaderSection.IDENTIFICATION:

                    pile[-1] = " ".join([pile[-1], line])

                # Starting subsection visa
                elif is_visa(line) and self.current_section_type == HeaderSection.IDENTIFICATION:

                    self._process_pile(pile, self.header_sections[-1])
                    pile = [line]

                    self.current_section_type = HeaderSection.VISA
                    self.header_sections.append(SubElement(self.header, "visa"))

                # Continuing sentence in current visa
                elif is_continuing_sentence(line) and self.current_section_type == HeaderSection.VISA:

                    pile[-1] = " ".join([pile[-1], line])

                # Continue feeding subsection visa
                elif is_visa(line) and self.current_section_type == HeaderSection.VISA:

                    pile.append(line)

                # Multi-line motifs
                elif is_continuing_sentence(line) or is_liste(line) and self.current_section_type == HeaderSection.VISA:

                    if len(pile) > 0:
                        pile[-1] = "\n".join([pile[-1], line])

                # Starting subsection motifs
                elif is_motif(line) and self.current_section_type == HeaderSection.VISA:

                    self._process_pile(pile, self.header_sections[-1])
                    pile = [line]

                    self.current_section_type = HeaderSection.MOTIFS
                    self.header_sections.append(SubElement(self.header, "motifs"))

                # Continue feeding subsection motifs
                elif is_motif(line) and self.current_section_type == HeaderSection.MOTIFS:

                    pile.append(line)

                # Multi-line motifs
                elif is_continuing_sentence(line) or is_liste(line) and self.current_section_type == HeaderSection.MOTIFS:

                    if len(pile) > 0:
                        pile[-1] = "\n".join([pile[-1], line])

                # Stop header
                elif is_arrete(line) and self.current_section_type == HeaderSection.MOTIFS:

                    self._process_pile(pile, self.header_sections[-1])
                    pile = []

                    # New header
                    self.in_header = False
                    self.in_body = True

                    # Updating type
                    self.current_section_type = BodySection.NONE

                # Continue feeding subsection
                else:

                    log_msg = f"{line} -> ERROR: uncatched element"
                    print(log_msg)
                    break

            # While we are in body
            elif self.in_body:

                # Discarding all non useful information
                if is_not_information(line):
                    continue

                new_section_info = self.identify_section_type(line)
                new_section_type = new_section_info["type"]

                if new_section_type != "none":

                    if len(self.paragraphs) > 0 and len(pile) > 0:
                        self._process_pile(pile, self.paragraphs[-1])
                        pile = []

                    new_section_level = new_section_info["level"]
                    if new_section_level == 0:
                        new_element = SubElement(self.body, new_section_type)
                    else:
                        new_element = SubElement(self.body_sections[new_section_level-1][-1], new_section_type)
                    new_element.set("number", new_section_info["number"])
                    new_element.set("text", new_section_info["text"])
                    self.body_sections[new_section_level].append(new_element)

                    self.current_section_level = new_section_level
                    self.current_section_type = new_section_type

                # Starting table
                elif is_table(line, pile, self.current_section_type) and self.current_section_type != BodySection.TABLE:

                    if len(self.paragraphs) > 0 and len(pile) > 0:
                        self._process_pile(pile, self.paragraphs[-1])
                        pile = []

                    new_element = SubElement(self.body_sections[self.current_section_level][-1], "table")
                    self.paragraphs.append(new_element)

                    # Start a new pile
                    pile = []
                    pile.append(line)

                    self.current_section_type = BodySection.TABLE

                # Continue feeding table
                elif is_table(line, pile, self.current_section_type) and self.current_section_type == BodySection.TABLE:

                    pile.append(line)

                # Starting list
                elif is_liste(line) and self.current_section_type != BodySection.LIST:

                    if len(self.paragraphs) > 0 and len(pile) > 0:
                        self._process_pile(pile, self.paragraphs[-1])
                        pile = []

                    new_element = SubElement(self.body_sections[self.current_section_level][-1], "list")
                    self.paragraphs.append(new_element)

                    # Start a new pile
                    pile = []
                    pile.append(line)

                    self.current_section_type = BodySection.LIST

                # Continue feeding list
                elif is_liste(line) and self.current_section_type == BodySection.LIST:

                    pile.append(line)

                # Normal paragraph
                else:

                    if len(self.paragraphs) > 0 and len(pile) > 0:
                        self._process_pile(pile, self.paragraphs[-1])
                        pile = []

                    # If line starts with lowercase, we might have changed page
                    if is_continuing_sentence(line) and self.current_section_type == BodySection.PARAGRAPH:
                        self.paragraphs[-1].text = " ".join([self.paragraphs[-1].text, line])

                    # If this is a paragraph before the first section
                    elif self.current_section_level < 0:
                        continue

                    # Otherwise new element
                    else:
                        new_element = SubElement(self.body_sections[self.current_section_level][-1], "paragraph")
                        new_element.text = line
                        self.paragraphs.append(new_element)

                        # Change section type
                        self.current_section_type = BodySection.PARAGRAPH

            log_msg = f"{line} -> {self.current_section_type} ({self.current_section_level})"
            print(log_msg)

            if k > k_max:
                break

        if len(self.paragraphs) > 0 and len(pile) > 0:
            self._process_pile(pile, self.paragraphs[-1])
            pile = []

        return self.root

    def identify_section_type(self, line):
        # Patterns for different section types
        # patterns = {
        #     'titre': r'^TITRE\s+([IVX]+|[1-9])(?:\.?\s+(.+))?$',
        #     'chapitre': r'^CHAPITRE\s+(\d+[\.]\d+)(?:\.?\s+(.+))?$',
        #     'article_3': r'^ARTICLE\s+(\d+[\.]\d+[\.]\d+)(?:\.?\s+(.+))?$',
        #     'article_4': r'^ARTICLE\s+(\d+[\.]\d+[\.]\d+[\.]\d+)(?:\.?\s+(.+))?$',
        # }
        # patterns_levels = {
        #     "titre": 0,
        #     "chapitre": 1,
        #     "article_3": 2,
        #     "article_4": 3,
        # }

        section_info = {
            "type": "none"
        }

        for section_type, pattern in self.patterns.items():

            match = re.match(pattern, line, re.IGNORECASE)

            if match:

                level = self.patterns_levels[section_type]
                text = match.group(2)

                section_info = {
                    'type': section_type,
                    "level": level,
                    'number': match.group(1),
                    'text': text.strip() if text else "",
                    'full_text': match.group(0),
                }

        return section_info



    def _process_pile(self, pile: List[str], section_element: Element):
        """Traite la pile de lignes et les ajoute à la section XML"""
        for line in pile:
            if line.strip():  # Si la ligne n'est pas vide
                line_element = SubElement(section_element, "line")
                line_element.text = line

    def _create_xml_element(self, tag: str, text: str = None,
                          attributes: Dict[str, str] = None) -> Element:
        """Utilitaire pour créer des éléments XML"""
        element = Element(tag)
        if text:
            element.text = text
        if attributes:
            for key, value in attributes.items():
                element.set(key, value)
        return element


def format_xml(element: Element) -> str:
    """Formate le XML de manière lisible"""
    raw_xml = tostring(element, 'utf-8')
    dom = xml.dom.minidom.parseString(raw_xml)
    return dom.toprettyxml(indent="  ")


def main(input_file_path: Path, output_file_path: Path):
    with open(input_file_path, 'r', encoding='utf-8') as f:
        content = f.readlines()

    parser = DocumentParser()
    xml_root = parser.parse_document(content)

    formatted_xml = format_xml(xml_root)

    with open(output_file_path, 'w', encoding='utf-8') as f:
        f.write(formatted_xml)


if __name__ == "__main__":
    import sys
    from optparse import OptionParser

    parser = OptionParser()
    parser.add_option(
        "-i",
        "--input",
        # default=TEST_DATA_DIR / "arretes_ocr" / "2020-04-20_AP-auto_initial_pixtral.txt",
        # default=TEST_DATA_DIR / "arretes_ocr" / "2021-09-24_AP-auto_refonte_pixtral.txt",
        # default=TEST_DATA_DIR / "arretes_ocr" / "2023-02-23_APC-auto_pixtral.txt",
        default=TEST_DATA_DIR / "arretes_ocr" / "2011-02-24_AP-auto_pixtral.txt",
    )
    parser.add_option(
        "-o",
        "--output",
        default='output.xml',
    )
    (options, args) = parser.parse_args()

    main(Path(options.input), Path(options.output))
