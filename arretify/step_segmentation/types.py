from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Dict


class SectionType(Enum):
    TITRE = "titre"
    CHAPITRE = "chapitre"
    ARTICLE = "article"
    UNKNOWN = "unknown"
    APPENDIX = "annexe"

    @classmethod
    def from_string(cls, section_name):
        try:
            return cls(section_name.lower())
        except ValueError:
            # For unknown section names return non-section
            return cls.NONE


class SectionsParsingContext:

    sections_levels: Dict[SectionType, Optional[List[int]]] = {}
    last_section_levels: Optional[List[int]] = None

    def get_section_levels(self, section_type: SectionType) -> Optional[List[int]]:
        return self.sections_levels[section_type]

    def update_section_levels(self, section_type: SectionType, section_levels: Optional[List[int]]):
        self.sections_levels[section_type] = section_levels
        self.last_section_levels = section_levels


@dataclass(frozen=True)
class SectionInfo:
    type: SectionType
    number: Optional[str] = None
    levels: Optional[List[int]] = None
    text: Optional[str] = None


@dataclass
class GroupParsingContext:
    alinea_count: int
