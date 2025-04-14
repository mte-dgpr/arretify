from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


class BodySection(Enum):
    TITRE = "titre"
    CHAPITRE = "chapitre"
    ARTICLE = "article"
    NONE = "none"

    @classmethod
    def from_string(cls, section_name):
        try:
            return cls(section_name.lower())
        except ValueError:
            # For unknown section names return non-section
            return cls.NONE


@dataclass(frozen=True)
class SectionInfo:
    type: BodySection
    number: Optional[str] = None
    levels: Optional[List[int]] = None
    text: Optional[str] = None


@dataclass
class SectionParsingContext:
    alinea_count: int
