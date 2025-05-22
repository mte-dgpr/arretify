from dataclasses import dataclass
from types import EllipsisType
from typing import Tuple


PatternString = str
GroupName = str
QuantifierRange = Tuple[int, int | EllipsisType]


@dataclass(frozen=True)
class MatchNamedGroup:
    group_name: str
    text: str


@dataclass(frozen=True)
class Settings:
    ignore_case: bool = True
    ignore_accents: bool = True
    normalize_quotes: bool = True
    normalize_dashes: bool = True
