from typing import List

from dataclasses import dataclass

@dataclass(frozen=True)
class DataElementSchema:
    name: str
    tag_name: str
    data_keys: List[str]


@dataclass(frozen=True)
class PresentationElementSchema:
    tag_name: str

