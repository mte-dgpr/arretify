from typing import Tuple

from .types import SectionId, SectionType


def generate_namespaced_section_id(
    section_type: SectionType, 
    section_id: str
) -> SectionId:
    return f"{section_type.value}:{section_id}"


def parse_namespaced_section_id(
    namespaced_section_id: SectionId
) -> Tuple[SectionType, str]:
    section_type, section_id = namespaced_section_id.split(':')
    return SectionType(section_type), section_id