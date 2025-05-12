from dataclasses import dataclass
from typing import List, Optional

from arretify.types import SectionType


@dataclass(frozen=True)
class TitleInfo:
    section_type: SectionType
    number: Optional[str] = None
    levels: Optional[List[int]] = None
    text: Optional[str] = None
