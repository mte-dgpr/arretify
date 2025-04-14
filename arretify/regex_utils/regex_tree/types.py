from dataclasses import dataclass
from typing import (
    List,
    Dict,
    Union,
    Iterable,
)

from ..core import PatternProxy
from ..types import GroupName, Settings


NodeMap = Dict[GroupName, "Node"]
Node = Union[
    "SequenceNode",
    "BranchingNode",
    "LiteralNode",
    "GroupNode",
    "QuantifierNode",
]
MatchDict = Dict[str, str]


@dataclass(frozen=True)
class BaseNode:
    id: GroupName
    settings: Settings
    pattern: PatternProxy

    def __repr__(self):
        pattern_repr = (
            self.pattern.pattern[:10] + "..."
            if len(self.pattern.pattern) > 10
            else self.pattern.pattern
        )
        return f'<{self.id}, {self.__class__.__name__}, "{pattern_repr}">'


@dataclass(frozen=True, repr=False)
class SequenceNode(BaseNode):
    children: NodeMap


@dataclass(frozen=True, repr=False)
class BranchingNode(BaseNode):
    children: NodeMap


@dataclass(frozen=True, repr=False)
class LiteralNode(BaseNode):
    pass


@dataclass(frozen=True, repr=False)
class GroupNode(BaseNode):
    group_name: GroupName
    child: Node


@dataclass(frozen=True, repr=False)
class QuantifierNode(BaseNode):
    quantifier: str
    child: Node


@dataclass(frozen=True)
class RegexTreeMatch:
    children: List[Union[str, "RegexTreeMatch"]]
    group_name: Union[GroupName, None]
    match_dict: MatchDict


RegexTreeMatchFlow = Iterable[RegexTreeMatch | str]
