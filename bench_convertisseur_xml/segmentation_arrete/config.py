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
    PARAGRAPH = "alinea"
    TABLE = "table"
    LIST = "list"
    NONE = "none"
