"""Main file to convert TXT files to XML output."""


from optparse import OptionParser
from pathlib import Path

from typing import List, Dict
from xml.etree.ElementTree import Element, SubElement, tostring
import xml.dom.minidom

from .config import BodySection, HeaderSection, section_from_name
from .parse_section import (
    identify_unique_sections, filter_max_level_sections, parse_section
)
from .sentence_rules import (
    is_arrete, is_continuing_sentence, is_entity, is_liste, is_motif, is_not_information, is_table,
    is_visa
)
from .utils import clean_markdown
from ..settings import TEST_DATA_DIR


# TODO-HTML : REMOVE
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
        self.max_section_level = -1
        self.current_section_type = HeaderSection.NONE

    def parse_document(self, content: List[str]) -> Element:
        """Point d'entrée principal du parsing"""
        self.current_document = SubElement(self.root, "document")

        self.header = SubElement(self.current_document, "header")
        self.body = SubElement(self.current_document, "body")

        k_max = 1000000

        pile = []
        self.in_header = True

        # Define sections that will be parsed and detected in this document
        unique_sections = identify_unique_sections(content)
        authorized_sections = filter_max_level_sections(unique_sections)

        self.max_section_level = len(authorized_sections)
        self.body_sections = [[] for _ in range(self.max_section_level)]

        for k, line in enumerate(content):

            line = clean_markdown(line)

            # While we are in header
            if self.in_header:

                new_section_info = parse_section(line, authorized_sections=authorized_sections)
                new_section_name = new_section_info["section_name"]
                new_section_type = section_from_name(new_section_name)

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
                elif not is_arrete(line) and self.current_section_type == HeaderSection.ENTITY:

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

                # Continue feeding subsection identification
                elif not (is_visa(line) or is_motif(line)) and self.current_section_type == HeaderSection.IDENTIFICATION:

                    pile.append(line)

                # Starting subsection visa
                elif is_visa(line) and self.current_section_type == HeaderSection.IDENTIFICATION:

                    self._process_pile(pile, self.header_sections[-1])
                    pile = [line]

                    self.current_section_type = HeaderSection.VISA
                    self.header_sections.append(SubElement(self.header, "visa"))

                # Continue feeding subsection visa
                elif not (is_motif(line) or is_arrete(line)) and new_section_type not in {BodySection.TITLE, BodySection.CHAPTER, BodySection.ARTICLE, BodySection.SUB_ARTICLE} and self.current_section_type == HeaderSection.VISA:

                    pile.append(line)

                # Starting subsection motifs
                elif is_motif(line) and self.current_section_type == HeaderSection.VISA:

                    self._process_pile(pile, self.header_sections[-1])
                    pile = [line]

                    self.current_section_type = HeaderSection.MOTIFS
                    self.header_sections.append(SubElement(self.header, "motifs"))

                # Continue feeding subsection motifs
                elif not is_arrete(line) and new_section_type not in {BodySection.TITLE, BodySection.CHAPTER, BodySection.ARTICLE, BodySection.SUB_ARTICLE} and self.current_section_type == HeaderSection.MOTIFS:

                    pile.append(line)

                # Stop header
                elif (is_arrete(line) and self.current_section_type in {HeaderSection.MOTIFS, HeaderSection.VISA}) or new_section_type in {BodySection.TITLE, BodySection.CHAPTER, BodySection.ARTICLE, BodySection.SUB_ARTICLE}:

                    self._process_pile(pile, self.header_sections[-1])
                    pile = []

                    # New header
                    self.in_header = False
                    self.in_body = True

                    # Updating type
                    self.current_section_type = BodySection.NONE

                # Continue feeding subsection
                else:

                    print(line)
                    raise ValueError("Uncatched element")

            # While we are in body
            if self.in_body:

                # Discarding all non useful information
                if is_not_information(line):
                    continue

                new_section_info = parse_section(line, authorized_sections=authorized_sections)
                new_section_name = new_section_info["section_name"]
                new_section_type = section_from_name(new_section_name)

                if new_section_type != BodySection.NONE:
                    # Process current pile and empty it
                    if len(self.paragraphs) > 0 and len(pile) > 0:
                        self._process_pile(pile, self.paragraphs[-1])
                        pile = []

                    # Find the upper section in body
                    new_section_level = new_section_info["level"]
                    upper_level = new_section_level - 1
                    while upper_level >= 0 and len(self.body_sections[upper_level]) == 0:
                        upper_level -= 1

                    if upper_level < 0 or len(self.body_sections[upper_level]) == 0:
                        new_element = SubElement(self.body, new_section_name)
                    else:
                        new_element = SubElement(self.body_sections[upper_level][-1], new_section_name)

                    # Add attributes
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


# TODO-HTML : REMOVE
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

    PARSER = OptionParser()
    PARSER.add_option(
        "-i",
        "--input",
        # default=TEST_DATA_DIR / "arretes_ocr" / "2020-04-20_AP-auto_initial_pixtral.txt",
        # default=TEST_DATA_DIR / "arretes_ocr" / "2021-09-24_AP-auto_refonte_pixtral.txt",
        # default=TEST_DATA_DIR / "arretes_ocr" / "2023-02-23_APC-auto_pixtral.txt",
        # default=TEST_DATA_DIR / "arretes_ocr" / "2011-02-24_AP-auto_pixtral.txt",
        # default=TEST_DATA_DIR / "arretes_ocr" / "2002-03-04_AP-auto_refonte_pixtral.txt",
        # default=TEST_DATA_DIR / "arretes_ocr" / "1978-05-24_AP-auto_pixtral.txt",
        default=TEST_DATA_DIR / "arretes_ocr" / "2017-01-26_APC-garanties-financières_pixtral.txt",
    )
    PARSER.add_option(
        "-o",
        "--output",
        default='output.xml',
    )
    (options, args) = PARSER.parse_args()

    main(Path(options.input), Path(options.output))
