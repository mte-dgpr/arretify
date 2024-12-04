import re
from pathlib import Path
from enum import Enum
from typing import List, Dict, Optional
from dataclasses import dataclass
from xml.etree.ElementTree import Element, SubElement, tostring
import xml.dom.minidom

from ..settings import TEST_DATA_DIR


@dataclass
class XMLGroup:
    """Classe représentant une section de document avec son niveau hiérarchique"""
    title: str
    content: List[str]
    level: int
    attributes: Dict[str, str] = None

class HeaderSection(Enum):
    ENTITY = "entite"
    IDENTIFICATION = "identification"
    VISA = "visa"
    MOTIFS = "motifs"
    NONE = "none"

class BodySection(Enum):
    TITLE = "titre"
    CHAPTER = "chapitre"
    ARTICLE = "article"
    PARAGRAPH = "alinea"
    TABLE = "table"
    LIST = "list"
    NONE = "none"

class DocumentParser:
    def __init__(self):

        self.root = Element("documents")

        self.current_document = None

        self.header = None
        self.in_header = False
        self.header_sections = []

        self.body = None
        self.in_body = False
        self.max_section_level = 4
        self.body_sections = [[] for _ in range(self.max_section_level)]
        self.paragraphs = []

        self.current_section_level = 0
        self.current_section_type = HeaderSection.NONE

    def parse_document(self, content: List[str]) -> Element:
        """Point d'entrée principal du parsing"""
        self.current_document = SubElement(self.root, "document")

        self.header = SubElement(self.current_document, "header")
        self.body = SubElement(self.current_document, "body")

        k_max = 5000000

        pile = []
        self.in_header = True

        for k, line in enumerate(content):

            line = clean_start(line)

            # While we are in header
            if self.in_header:

                # Discarding all non useful information
                if self._is_not_information(line):
                    log_msg = f"{line} -> no information"
                    print(log_msg)
                    continue

                # Starting subsection entity
                if self._is_entity(line) and self.current_section_type == HeaderSection.NONE:

                    # No process required as we start the document
                    pile.append(line)

                    self.current_section_type = HeaderSection.ENTITY
                    self.header_sections.append(SubElement(self.header, "entity"))

                # Continue feeding subsection entity
                elif self._is_entity(line) and self.current_section_type == HeaderSection.ENTITY:

                    pile.append(line)

                # Starting subsection identification
                elif self._is_arrete(line) and self.current_section_type == HeaderSection.ENTITY:

                    self._process_pile(pile, self.header_sections[-1])
                    pile = [line]

                    self.current_section_type = HeaderSection.IDENTIFICATION
                    self.header_sections.append(SubElement(self.header, "identification"))

                # Discard entity in subsection identification
                elif self._is_entity(line) and self.current_section_type == HeaderSection.IDENTIFICATION:
                    log_msg = f"{line} -> no information"
                    print(log_msg)
                    continue

                # Multi-line identification
                elif self._is_continuing_sentence(line) and self.current_section_type == HeaderSection.IDENTIFICATION:

                    pile[-1] = " ".join([pile[-1], line])

                # Starting subsection visa
                elif self._is_visa(line) and self.current_section_type == HeaderSection.IDENTIFICATION:

                    self._process_pile(pile, self.header_sections[-1])
                    pile = [line]

                    self.current_section_type = HeaderSection.VISA
                    self.header_sections.append(SubElement(self.header, "visa"))

                # Continuing sentence in current visa
                elif self._is_continuing_sentence(line) and self.current_section_type == HeaderSection.VISA:

                    pile[-1] = " ".join([pile[-1], line])

                # Continue feeding subsection visa
                elif self._is_visa(line) and self.current_section_type == HeaderSection.VISA:

                    pile.append(line)

                # Starting subsection motifs
                elif self._is_motif(line) and self.current_section_type == HeaderSection.VISA:

                    self._process_pile(pile, self.header_sections[-1])
                    pile = [line]

                    self.current_section_type = HeaderSection.MOTIFS
                    self.header_sections.append(SubElement(self.header, "motifs"))

                # Continue feeding subsection motifs
                elif self._is_motif(line) and self.current_section_type == HeaderSection.MOTIFS:

                    pile.append(line)

                # Stop header
                elif self._is_arrete(line) and self.current_section_type == HeaderSection.MOTIFS:

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

                log_msg = f"{line} -> {self.current_section_type}"
                print(log_msg)

            # While we are in body
            elif self.in_body:

                # Discarding all non useful information
                if self._is_not_information(line):
                    log_msg = f"{line} -> no information"
                    print(log_msg)
                    continue

                new_section_info = self.identify_section_type(line)
                new_section_type = new_section_info["type"]

                if new_section_type != "none":

                    # if len(self.paragraphs) > 0 and len(pile) > 0:
                    #     self._process_pile(pile, self.paragraphs[-1])
                    #     pile = []

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

                    # # Starting subsection title
                    # if self._is_titre(line):

                    #     if len(self.paragraphs) > 0 and len(pile) > 0:
                    #         self._process_pile(pile, self.paragraphs[-1])
                    #         pile = []

                    #     title_info = self._extract_title_info(line)
                    #     title_element = SubElement(self.body, "title")
                    #     title_element.set("number", title_info['number'])
                    #     title_element.set("text", title_info['text'])
                    #     self.titles.append(title_element)
                    #     self.current_section_type = BodySection.TITLE

                    # # Starting chapitre
                    # elif self._is_chapitre(line):

                    #     if len(self.paragraphs) > 0 and len(pile) > 0:
                    #         self._process_pile(pile, self.paragraphs[-1])
                    #         pile = []

                    #     chapter_info = self._extract_chapter_info(line)
                    #     chapter_element = SubElement(self.titles[-1], "chapter")
                    #     chapter_element.set("number", chapter_info['number'])
                    #     chapter_element.set("text", chapter_info['text'])
                    #     self.chapters.append(chapter_element)
                    #     self.current_section_type = BodySection.CHAPTER

                    # # Starting article
                    # elif self._is_article(line):

                    #     if len(self.paragraphs) > 0 and len(pile) > 0:
                    #         self._process_pile(pile, self.paragraphs[-1])
                    #         pile = []

                    #     article_info = self._extract_article_info(line)
                    #     article_element = SubElement(self.chapters[-1], "article")
                    #     article_element.set("number", article_info['number'])
                    #     article_element.set("text", article_info['text'])
                    #     self.articles.append(article_element)
                    #     self.current_section_type = BodySection.ARTICLE

                # Starting table
                elif self._is_table(line) and self.current_section_type != BodySection.TABLE:

                    if len(self.paragraphs) > 0 and len(pile) > 0:
                        self._process_pile(pile, self.paragraphs[-1])
                        pile = []

                    # Start a new pile
                    pile = []
                    pile.append(line)

                    self.current_section_type = BodySection.TABLE

                # Continue feeding table
                elif self._is_table(line) and self.current_section_type == BodySection.TABLE:

                    pile.append(line)

                # Starting list
                elif self._is_liste(line) and self.current_section_type != BodySection.LIST:

                    if len(self.paragraphs) > 0 and len(pile) > 0:
                        self._process_pile(pile, self.paragraphs[-1])
                        pile = []

                    # Start a new pile
                    pile = []
                    pile.append(line)

                    self.current_section_type = BodySection.LIST

                # Continue feeding list
                elif self._is_liste(line) and self.current_section_type == BodySection.LIST:

                    pile.append(line)

                else:

                    if len(self.paragraphs) > 0 and len(pile) > 0:
                        self._process_pile(pile, self.paragraphs[-1])
                        pile = []

                    new_element = SubElement(self.body_sections[self.current_section_level][-1], "paragraph")
                    new_element.text = line
                    self.paragraphs.append(new_element)

                    # Do not change current section level nor type

                    # paragraph = SubElement(self.articles[-1], "paragraph")
                    # paragraph.text = line
                    # self.paragraphs.append(paragraph)
                    # self.current_section_type = BodySection.PARAGRAPH

                log_msg = f"{line} -> {self.current_section_type}"
                print(log_msg)

                if k > k_max:
                    break

        return self.root

    def _is_not_information(self, line: str) -> bool:
        patterns_to_ignore = [
            r'^\d+/\d+\s*$',           # Format: 3/48
            r'^page\s+\d+/\d+\s*$',    # Format: Page 3/48
            r'^```',                      # Commence par un backtick
            r'^---',                      # Commence par des tirets
            r'^\s*$',                   # Ligne vide ou espaces
            r'^sur\b',                  # Commence par 'sur'
            r'^apr[eè]s\b',           # Commence par 'apres/après'
            r'^!',                   # Commence par un point d'exclamation
        ]
        pattern = '|'.join(f'(?:{pattern})' for pattern in patterns_to_ignore)
        return bool(re.match(pattern, line, re.IGNORECASE))

    def _is_continuing_sentence(self, line: str) -> bool:
        return bool(re.match(r'[a-z]', line))

    def _is_entity(self, line: str) -> bool:
        """Détecte si la ligne commence par un nom d'entité"""
        patterns_to_catch = [
            r"pr[eé]fecture",
            r"direction",
            r"bureau",
            r"le pr[ée]fet",
            r"chevalier",
            r"officier",
        ]
        pattern = f"^({'|'.join(patterns_to_catch)})\\b"
        return bool(re.match(pattern, line, re.IGNORECASE))

    def _is_visa(self, line: str) -> bool:
        """Détecte si la ligne commence par un visa"""
        return bool(re.match(r"^(vu)\b", line, re.IGNORECASE))

    def _is_motif(self, line: str) -> bool:
        """Détecte si la ligne commence par un visa"""
        return bool(re.match(r"^(consid[eé]rant)\b", line, re.IGNORECASE))

    def _is_arrete(self, line: str) -> bool:
        """Détecte si la ligne commence par un visa"""
        return bool(re.match(r"^(arr[eéê]t[eé])\b", line, re.IGNORECASE))

    def identify_section_type(self, line):
        # Patterns for different section types
        patterns = {
            'titre': r'^TITRE\s+([IVX]+)\.?\s*[-–]\s*(.+)$',
            # 'titre': r'^TITRE\s+(?:[IVX]+|\d+)\.?\s*[-–]\s*(.+)$',
            'chapitre': r'^CHAPITRE\s+(\d+[\.\.]\d+)\.?\s+(.+)$',
            'article_3': r'^ARTICLE\s+(\d+[\.\.]\d+[\.\.]\d+)\.?\s+(.+)$',
            'article_4': r'^ARTICLE\s+(\d+[\.\.]\d+[\.\.]\d+[\.\.]\d+)\.?\s+(.+)$',
        }
        patterns_levels = {
            "titre": 0,
            "chapitre": 1,
            "article_3": 2,
            "article_4": 3,
        }

        section_info = {
            "type": "none"
        }

        for section_type, pattern in patterns.items():
            match = re.match(pattern, line, re.IGNORECASE)
            if match:
                section_info = {
                    'type': section_type,
                    "level": patterns_levels[section_type],
                    'number': match.group(1),
                    'text': match.group(2).strip(),
                    'full_text': match.group(0)
                }

        return section_info

    def _is_table(self, line: str) -> bool:
        """Détecte si la ligne commence par un visa"""
        return bool(re.match(r"^\|", line, re.IGNORECASE))

    def _is_liste(self, line: str) -> bool:
        """Détecte si la ligne commence par un visa"""
        return bool(re.match(r"^-\s", line, re.IGNORECASE))

    def _extract_title_info(self, line: str) -> Dict[str, str]:
        """Extrait le numéro et le texte d'un titre"""
        match = re.match(r'^titre\s+([IVX]+)\s*-\s*(.+)', line, re.IGNORECASE)
        # match = re.match(r'^titre\s+(?:[IVX]+|\d+)\.?\s*[-–]\s*(.+)$', line, re.IGNORECASE)
        if match:
            return {
                'number': match.group(1),
                'text': match.group(2).strip()
            }
        return {'number': '', 'text': line}

    def _extract_chapter_info(self, line: str) -> Dict[str, str]:
        """Extrait le numéro et le texte d'un chapitre"""
        match = re.match(r'^chapitre\s+(\d+\.\d+)\s+(.+)', line, re.IGNORECASE)
        if match:
            return {
                'number': match.group(1),
                'text': match.group(2).strip()
            }
        return {'number': '', 'text': line}

    def _extract_article_info(self, line: str) -> Dict[str, str]:
        """Extrait le numéro et le texte d'un article"""
        match = re.match(r'^article\s+(\d+\.\d+\.\d+)\s+(.+)', line, re.IGNORECASE)
        if match:
            return {
                'number': match.group(1),
                'text': match.group(2).strip()
            }
        return {'number': '', 'text': line}

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

def clean_start(text: str) -> str:
    text = re.sub(r'[\n\r]+$', '', text)  # remove newline at the end
    text = re.sub(r"^[#\s]+", "", text)  # remove # and whitespaces
    return text

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
        default=TEST_DATA_DIR / "arretes_ocr" / "2020-04-20_AP-auto_initial_pixtral.txt",
    )
    parser.add_option(
        "-o",
        "--output",
        default='output.xml',
    )
    (options, args) = parser.parse_args()

    main(Path(options.input), Path(options.output))