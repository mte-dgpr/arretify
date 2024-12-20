"""Define data classes for writing the XML output."""


import re
from enum import Enum


SERVICE_PATTERNS = [
    r"pr[eé]fecture",
    r"sous-pr[eé]fecture",
    r"secr[eé]tariat",
    r"sg",
    r"pr[ée]f[eè]te?",
    r"direction",
    r"drire",
    r"dreal",
    r"service",
    r"bureau",
    r"unit[eé]",
    r"installations class[eé]es pour la protection de l'environnement",  # sometimes independent
]
HONORARY_PATTERNS = [
    r"la pr[ée]fecture",
    r"l[ea] pr[ée]f[eè]te?",
    r"chevalier",
    r"officier",
    r"commandeur",
]
REFERENCE_PATTERNS = [
    r"affaires? suivies?",
    r"dossiers? suivis?",
    r"r[eé]f",
    r"n°",
    r"n/ref",
    r"nor",
]


# Convert the patterns to case insensitive
SERVICE_AND_REFERENCE_PATTERN = re.compile(
    f"({'|'.join(SERVICE_PATTERNS + REFERENCE_PATTERNS)})",
    re.IGNORECASE,
)


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
