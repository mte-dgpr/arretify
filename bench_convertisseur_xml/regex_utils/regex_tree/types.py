from dataclasses import dataclass
from typing import List, Dict, Union, Optional, List, Union, Iterator, Iterable

from ..core import PatternProxy
from ..types import GroupName, Settings


Node = Union['ContainerNode', 'LeafNode', 'GroupNode', 'QuantifierNode']
NodeMap = Dict[GroupName, Node]
MatchDict = Dict[str, str]


@dataclass(frozen=True)
class ContainerNode:
    id: GroupName
    pattern: PatternProxy
    children: NodeMap
    settings: Settings

    def __repr__(self):
        return f'ContainerNode(id={self.id}, pattern={self.pattern.pattern})'


@dataclass(frozen=True)
class LeafNode:
    id: GroupName
    pattern: PatternProxy
    settings: Settings

    def __repr__(self):
        return f'LeafNode(id={self.id}, pattern={self.pattern.pattern})'


@dataclass(frozen=True)
class GroupNode:
    id: GroupName
    group_name: GroupName
    pattern: PatternProxy
    child: Node
    settings: Settings

    def __repr__(self):
        return f'GroupNode(name={self.group_name})'


@dataclass(frozen=True)
class QuantifierNode:
    id: GroupName
    quantifier: str
    pattern: PatternProxy
    child: Node
    settings: Settings

    def __repr__(self):
        return f'QuantifierNode(quantifier={self.quantifier})'


@dataclass(frozen=True)
class RegexTreeMatch:
    children: List[Union[str, 'RegexTreeMatch']]
    group_name: Union[GroupName, None]
    match_dict: MatchDict


RegexTreeMatchFlow = Iterable[RegexTreeMatch | str]