"""Define data classes for writing the XML output."""


import re
from enum import Enum

from bench_convertisseur_xml.regex_utils import PatternProxy


SERVICE_PATTERNS = [
    r"préfecture",
    r"sous-préfecture",
    r"secrétariat",
    r"sg",
    r"préfète?",
    r"direction",
    r"drire",
    r"dreal",
    r"service",
    r"section",
    r"pôle",
    r"bureau",
    r"unité",
    r"installations classées pour la protection de l'environnement",  # sometimes independent
]
HONORARY_PATTERNS = [
    r"la préfecture",
    r"l[ea] préfète?",
    r"chevalier",
    r"officier",
    r"commandeur",
]
REFERENCE_PATTERNS = [
    r"affaires? suivies?",
    r"dossiers? suivis?",
    r"réf",
    r"n°",
    r"n/ref",
    r"nor",
]


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
    else:
        section_type = BodySection.NONE

    return section_type
