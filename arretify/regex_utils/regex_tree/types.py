#
# Copyright (c) 2025 Direction générale de la prévention des risques (DGPR).
#
# This file is part of Arrêtify.
# See https://github.com/mte-dgpr/arretify for further info.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from dataclasses import dataclass
from typing import Dict, Iterable, Sequence, Union

from arretify.types import ProtectedTag, ProtectedTagOrStr

from ..core import PatternProxy
from ..types import GroupName, QuantifierRange, Settings

NodeMap = Dict[GroupName, "Node"]
Node = Union[
    "SequenceNode",
    "BranchingNode",
    "LiteralNode",
    "GroupNode",
    "RepeatNode",
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
    key: str | None


@dataclass(frozen=True, repr=False)
class GroupNode(BaseNode):
    group_name: GroupName
    child: Node


@dataclass(frozen=True, repr=False)
class RepeatNode(BaseNode):
    quantifier: QuantifierRange
    child: Node


@dataclass(frozen=True)
class RegexTreeMatch:
    children: Sequence[Union[ProtectedTag, str, "RegexTreeMatch"]]
    group_name: Union[GroupName, None]
    match_dict: MatchDict


RegexTreeMatchFlow = Iterable[RegexTreeMatch | ProtectedTagOrStr]
