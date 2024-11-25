import re
from enum import Enum
from typing import List, Dict, Optional
from dataclasses import dataclass
from xml.etree.ElementTree import Element, SubElement, tostring
import xml.dom.minidom

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
        self.titles = []
        self.chapters = []
        self.articles = []
        self.paragraphs = []

        self.current_section_type = HeaderSection.NONE

    def parse_document(self, content: List[str]) -> Element:
        """Point d'entrée principal du parsing"""
        self.current_document = SubElement(self.root, "document")

        self.header = SubElement(self.current_document, "header")
        self.body = SubElement(self.current_document, "body")

        k_max = 50000000

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

                    self.current_section_type = HeaderSection.ENTITY
                    self.header_sections.append(SubElement(self.header, "entity"))
                    pile.append(line)

                # Continue feeding subsection entity
                elif self._is_entity(line) and self.current_section_type == HeaderSection.ENTITY:

                    pile.append(line)

                # Starting subsection identification
                elif self._is_arrete(line) and self.current_section_type == HeaderSection.ENTITY:

                    self._process_pile(pile, self.header_sections[-1])
                    pile = []

                    self.current_section_type = HeaderSection.IDENTIFICATION
                    self.header_sections.append(SubElement(self.header, "identification"))
                    pile.append(line)

                # Discard entity in subsection identification
                elif self._is_entity(line) and self.current_section_type == HeaderSection.IDENTIFICATION:
                    log_msg = f"{line} -> no information"
                    print(log_msg)
                    continue

                # Starting subsection visa
                elif self._is_visa(line) and self.current_section_type == HeaderSection.IDENTIFICATION:

                    self._process_pile(pile, self.header_sections[-1])
                    pile = []

                    self.current_section_type = HeaderSection.VISA
                    self.header_sections.append(SubElement(self.header, "visa"))
                    pile.append(line)

                # Continue feeding subsection visa
                elif self._is_visa(line) and self.current_section_type == HeaderSection.VISA:

                    pile.append(line)

                # Starting subsection motifs
                elif self._is_motif(line) and self.current_section_type == HeaderSection.VISA:

                    self._process_pile(pile, self.header_sections[-1])
                    pile = []

                    self.current_section_type = HeaderSection.MOTIFS
                    self.header_sections.append(SubElement(self.header, "motifs"))
                    pile.append(line)

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

                # Starting subsection title
                if self._is_titre(line):

                    title_info = self._extract_title_info(line)
                    title_element = SubElement(self.body, "title")
                    title_element.set("number", title_info['number'])
                    title_element.set("text", title_info['text'])
                    self.titles.append(title_element)                    
                    self.current_section_type = BodySection.TITLE

                # Starting chapitre
                elif self._is_chapitre(line):

                    chapter_info = self._extract_chapter_info(line)
                    chapter_element = SubElement(self.titles[-1], "chapter")
                    chapter_element.set("number", chapter_info['number'])
                    chapter_element.set("text", chapter_info['text'])
                    self.chapters.append(chapter_element)
                    self.current_section_type = BodySection.CHAPTER

                # Starting article
                elif self._is_article(line):

                    article_info = self._extract_article_info(line)
                    article_element = SubElement(self.chapters[-1], "article")
                    article_element.set("number", article_info['number'])
                    article_element.set("text", article_info['text'])
                    self.articles.append(article_element)
                    self.current_section_type = BodySection.ARTICLE

                # Starting table
                elif self._is_table(line) and self.current_section_type != BodySection.TABLE:

                    # Start a new pile
                    pile = []

                    self.current_section_type = BodySection.TABLE
                    pile.append(line)

                # Continue feeding table
                elif self._is_table(line) and self.current_section_type == BodySection.TABLE:

                    pile.append(line)

                # Starting list
                elif self._is_liste(line) and self.current_section_type != BodySection.LIST:

                    # Start a new pile
                    pile = []

                    self.current_section_type = BodySection.LIST
                    pile.append(line)

                # Continue feeding list
                elif self._is_liste(line) and self.current_section_type == BodySection.LIST:

                    pile.append(line)

                else:

                    paragraph = SubElement(self.articles[-1], "paragraph")
                    paragraph.text = line
                    self.paragraphs.append(paragraph)
                    self.current_section_type = BodySection.PARAGRAPH

                log_msg = f"{line} -> {self.current_section_type}"
                print(log_msg)

                if k > k_max:
                    break

        return self.root

    def _is_not_information(self, line: str) -> bool:
        patterns_to_ignore = [
            r'^\d+/\d+\s*$',           # Format: 3/48
            r'^page\s+\d+/\d+\s*$',    # Format: Page 3/48
            r'^`',                      # Commence par un backtick
            r'^\s*$',                   # Ligne vide ou espaces
            r'^sur\b',                  # Commence par 'sur'
            r'^apr[eè]s\b',           # Commence par 'apres/après'
            r'^!',                   # Commence par un point d'exclamation
        ]
        pattern = '|'.join(f'(?:{pattern})' for pattern in patterns_to_ignore)
        return bool(re.match(pattern, line, re.IGNORECASE))

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

    def _is_titre(self, line: str) -> bool:
        """Détecte si la ligne commence par un visa"""
        return bool(re.match(r"^(titre)\b", line, re.IGNORECASE))

    def _is_chapitre(self, line: str) -> bool:
        """Détecte si la ligne commence par un visa"""
        return bool(re.match(r"^(chapitre)\b", line, re.IGNORECASE))

    def _is_article(self, line: str) -> bool:
        """Détecte si la ligne commence par un visa"""
        return bool(re.match(r"^(article)\b", line, re.IGNORECASE))

    def _is_table(self, line: str) -> bool:
        """Détecte si la ligne commence par un visa"""
        return bool(re.match(r"^\|", line, re.IGNORECASE))

    def _is_liste(self, line: str) -> bool:
        """Détecte si la ligne commence par un visa"""
        return bool(re.match(r"^-\s", line, re.IGNORECASE))

    def _extract_title_info(self, line: str) -> Dict[str, str]:
        """Extrait le numéro et le texte d'un titre"""
        match = re.match(r'^titre\s+([IVX]+)\s*-\s*(.+)', line, re.IGNORECASE)
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
                line_element = SubElement(section_element, "ligne")
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

def main():
    # Exemple d'utilisation
    input_txt = "données de test/3013459/2020-04-20_AP-auto_initial_pixtral.txt"
    with open(input_txt, 'r', encoding='utf-8') as f:
        content = f.readlines()

    parser = DocumentParser()
    xml_root = parser.parse_document(content)

    formatted_xml = format_xml(xml_root)

    with open('output.xml', 'w', encoding='utf-8') as f:
        f.write(formatted_xml)

if __name__ == "__main__":
    main()