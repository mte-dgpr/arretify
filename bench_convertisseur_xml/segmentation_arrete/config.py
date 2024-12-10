"""Define data classes for writing the XML output."""


from enum import Enum


class HeaderSection(Enum):
    ENTITY = "entity"
    IDENTIFICATION = "identification"
    VISA = "visa"
    MOTIFS = "motifs"
    NONE = "none"


class BodySection(Enum):
    TITLE = "title"
    CHAPTER = "chapter"
    ARTICLE = "article"
    SUB_ARTICLE = "sub_article"
    PARAGRAPH = "paragraph"
    TABLE = "table"
    LIST = "list"
    NONE = "none"


def section_from_name(section_name):

    if section_name in {"title", "titre"}:
        section_type = BodySection.TITLE
    elif section_name in {"chapter", "chapitre"}:
        section_type = BodySection.CHAPTER
    elif section_name in {"article"}:
        section_type = BodySection.ARTICLE
    elif section_name in {"sub_article", "sous_article"}:
        section_type = BodySection.SUB_ARTICLE
    elif section_name in {"paragraph", "alinea"}:
        section_type = BodySection.PARAGRAPH
    else:
        section_type = BodySection.NONE

    return section_type
