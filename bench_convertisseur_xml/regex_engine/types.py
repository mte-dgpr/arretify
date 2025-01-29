import enum
import re
from typing import List, Dict, Union, Optional, List, Union, Iterator, Iterable
from dataclasses import dataclass

from bench_convertisseur_xml.types import PatternString, GroupName

MatchDict = Dict[str, str]
Node = Union['ContainerNode', 'LeafNode', 'GroupNode', 'QuantifierNode']
NodeMap = Dict[GroupName, Node]


@dataclass(frozen=True)
class Settings:
    ignore_case: bool = True


@dataclass(frozen=True)
class ContainerNode:
    id: GroupName
    pattern: re.Pattern
    children: NodeMap
    settings: Settings

    def __repr__(self):
        return f'ContainerNode(id={self.id}, pattern={self.pattern.pattern})'


@dataclass(frozen=True)
class LeafNode:
    id: GroupName
    pattern: re.Pattern
    settings: Settings

    def __repr__(self):
        return f'LeafNode(id={self.id}, pattern={self.pattern.pattern})'


@dataclass(frozen=True)
class GroupNode:
    id: GroupName
    group_name: GroupName
    pattern: re.Pattern
    child: Node
    settings: Settings

    def __repr__(self):
        return f'GroupNode(name={self.group_name})'


@dataclass(frozen=True)
class QuantifierNode:
    id: GroupName
    quantifier: str
    pattern: re.Pattern
    child: Node
    settings: Settings

    def __repr__(self):
        return f'QuantifierNode(quantifier={self.quantifier})'



@dataclass(frozen=True)
class MatchGroup:
    children: List[Union[str, 'MatchGroup']]
    group_name: Union[GroupName, None]
    match_dict: MatchDict

    @property
    def string_children(self) -> List[str]:
        string_children: List[str] = []
        for string in self.children:
            if not isinstance(string, str):
                raise ValueError(f"expected string, got {string}")
            string_children.append(string)
        return string_children

MatchGroupFlow = Iterable[MatchGroup | str]