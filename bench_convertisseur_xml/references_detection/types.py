import enum


SectionId = str
ArticleId = str


class SectionType(enum.Enum):
    ALINEA = 'alinea'
    SUB_SECTION = 'sub_section'