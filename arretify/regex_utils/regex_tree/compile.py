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
from dataclasses import replace
from typing import Sequence as SequenceType
from typing import Union

from ..core import PatternProxy
from ..helpers import (
    join_with_or,
    quantifier_to_string,
    repeated_with_separator,
    without_named_groups,
)
from ..types import Settings
from .types import (
    BranchingNode,
    GroupName,
    GroupNode,
    LiteralNode,
    Node,
    NodeMap,
    QuantifierRange,
    RepeatNode,
    SequenceNode,
)


def Literal(
    pattern_string: str, key: str | None = None, settings: Settings | None = None
) -> LiteralNode:
    """
    If a key is provided, the pattern string will be wrapped in a named group with that key.
    """
    settings = settings or Settings()
    if key is not None:
        pattern_string = f"(?P<{key}>{without_named_groups(pattern_string)})"
    return LiteralNode(
        id=_get_unique_id(),
        pattern=PatternProxy(
            pattern_string,
            settings=settings,
        ),
        key=key,
        settings=settings,
    )


def Branching(
    child_or_str_list: SequenceType[Node | str],
    settings: Settings | None = None,
) -> BranchingNode:
    """
    Order of patterns matters, from most specific to less specific.
    """
    settings = settings or Settings()
    children_list: list[Node] = []
    for child_or_str in child_or_str_list:
        children_list.append(_initialize_child(child_or_str, settings))

    return BranchingNode(
        id=_get_unique_id(),
        pattern=PatternProxy(
            join_with_or(
                [
                    f"(?P<{child.id}>{without_named_groups(child.pattern.pattern)})"
                    for child in children_list
                ]
            ),
            settings=settings,
        ),
        children={child.id: child for child in children_list},
        settings=settings,
    )


def Sequence(
    child_or_str_list: SequenceType[Node | str],
    settings: Settings | None = None,
) -> SequenceNode:
    settings = settings or Settings()
    pattern_string = ""
    children: NodeMap = {}
    child: Node
    for child_or_str in child_or_str_list:
        child = _initialize_child(child_or_str, settings)
        pattern_string += f"(?P<{child.id}>{without_named_groups(child.pattern.pattern)})"
        children[child.id] = child

    return SequenceNode(
        id=_get_unique_id(),
        pattern=PatternProxy(
            pattern_string,
            settings=settings,
        ),
        children=children,
        settings=settings,
    )


def Group(
    child_or_str: Union[Node, str],
    group_name: GroupName,
    settings: Settings | None = None,
) -> GroupNode:
    settings = settings or Settings()
    child = _initialize_child(child_or_str, settings)
    return GroupNode(
        id=_get_unique_id(),
        group_name=group_name,
        pattern=PatternProxy(
            f"(?P<{child.id}>{without_named_groups(child.pattern.pattern)})",
            settings=settings,
        ),
        child=child,
        settings=settings,
    )


def Repeat(
    child_or_str: Union[Node, str],
    quantifier: QuantifierRange,
    separator: str | None = None,
    settings: Settings | None = None,
) -> RepeatNode:
    settings = settings or Settings()
    child = _initialize_child(child_or_str, settings)

    if separator:
        child_pattern_string = without_named_groups(child.pattern.pattern)
        pattern_string = repeated_with_separator(
            child_pattern_string,
            separator,
            quantifier,
        )
    else:
        quantifier_str = quantifier_to_string(quantifier)
        pattern_string = f"({without_named_groups(child.pattern.pattern)}){quantifier_str}"

    return RepeatNode(
        id=_get_unique_id(),
        quantifier=quantifier,
        pattern=PatternProxy(
            pattern_string,
            settings=settings,
        ),
        child=child,
        settings=settings,
    )


def _get_unique_id() -> str:
    global _COUNTER
    _COUNTER += 1
    return f"{_PREFIX}{_COUNTER}"


_COUNTER = 0
_PREFIX = "_ID_"


def _initialize_child(node_or_str: Node | str, default_settings: Settings) -> Node:
    # If child is a string, we create a LiteralNode from it.
    if isinstance(node_or_str, str):
        return Literal(node_or_str, settings=default_settings)
    # If the child is already a node, we ensures that it has a unique id.
    # This allows using the same node in multiple places in the tree.
    else:
        return replace(node_or_str, id=_get_unique_id())
