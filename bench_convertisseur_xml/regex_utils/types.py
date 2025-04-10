from dataclasses import dataclass
import enum
import re
from typing import List, Dict, Union, Optional, List, Union, Iterator, Iterable


PatternString = str
GroupName = str


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