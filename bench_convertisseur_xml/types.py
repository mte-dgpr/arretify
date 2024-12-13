from typing import List

from dataclasses import dataclass

@dataclass(frozen=True)
class ElementSchema:
    name: str
    tag_name: str
    classes: List[str]
    data_keys: List[str]