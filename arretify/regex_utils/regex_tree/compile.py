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
from typing import Type, Union

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
    NonCapturingNode,
    OptionalNode,
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
        children_list.append(_initialize_child(BranchingNode, child_or_str, settings))

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
    children_list = [_initialize_child(SequenceNode, c, settings) for c in child_or_str_list]

    head_nodes: list[Node] = []
    children_list_remainder = children_list[:]
    while children_list_remainder and isinstance(
        children_list_remainder[0], (OptionalNode, NonCapturingNode)
    ):
        head_nodes.append(children_list_remainder.pop(0))

    if head_nodes:
        if isinstance(head_nodes[0], NonCapturingNode):
            if len(head_nodes) > 1:
                raise ValueError(
                    "NonCapturingNode can't be followed by another "
                    "NonCapturingNode or OptionalNode"
                )

        if isinstance(head_nodes[0], OptionalNode):
            for node in head_nodes[1:]:
                if not isinstance(node, OptionalNode):
                    raise ValueError("OptionalNode can't be followed by a NonCapturingNode")

    for i, child in enumerate(children_list_remainder):
        if isinstance(child, NonCapturingNode) and i != len(children_list_remainder) - 1:
            raise ValueError("NonCapturingNode can only be at " "start or end of the sequence")

    # Build pattern
    pattern_string = ""
    children: NodeMap = {}
    for child in children_list:
        pattern_string += f"(?P<{child.id}>{without_named_groups(child.pattern.pattern)})"
        children[child.id] = child

    return SequenceNode(
        id=_get_unique_id(),
        pattern=PatternProxy(pattern_string, settings=settings),
        children=children,
        settings=settings,
    )


def Group(
    child_or_str: Union[Node, str],
    group_name: GroupName,
    settings: Settings | None = None,
) -> GroupNode:
    settings = settings or Settings()
    child = _initialize_child(GroupNode, child_or_str, settings)
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
    child = _initialize_child(RepeatNode, child_or_str, settings)

    quantifier_min, quantifier_max = quantifier
    if quantifier_min < 1:
        raise ValueError("Quantifier min must be >= 1")
    if quantifier_max is not Ellipsis and quantifier_min > quantifier_max:
        raise ValueError("Quantifier min must be <= quantifier max")

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
        separator=PatternProxy(separator, settings=settings) if separator else None,
        quantifier=quantifier,
        pattern=PatternProxy(
            pattern_string,
            settings=settings,
        ),
        child=child,
        settings=settings,
    )


def Optional(child_or_str: Union[Node, str], settings: Settings | None = None) -> OptionalNode:
    settings = settings or Settings()
    return OptionalNode(
        id=_get_unique_id(),
        pattern=PatternProxy(".*", settings=settings),
        settings=settings,
        child=_initialize_child(OptionalNode, child_or_str, settings),
    )


def NonCapturing(
    child_or_str: Union[Node, str], settings: Settings | None = None
) -> NonCapturingNode:
    settings = settings or Settings()
    return NonCapturingNode(
        id=_get_unique_id(),
        pattern=PatternProxy(".*", settings=settings),
        settings=settings,
        child=_initialize_child(NonCapturingNode, child_or_str, settings),
    )


def _get_unique_id() -> str:
    global _COUNTER
    _COUNTER += 1
    return f"{_PREFIX}{_COUNTER}"


_COUNTER = 0
_PREFIX = "_ID_"


def _initialize_child(
    parent_type: Type[Node], node_or_str: Node | str, default_settings: Settings
) -> Node:
    if isinstance(node_or_str, (OptionalNode, NonCapturingNode)) and parent_type != SequenceNode:
        raise ValueError(f"{type(node_or_str).__name__} is allowed only in {SequenceNode.__name__}")

    # If child is a string, we create a LiteralNode from it.
    if isinstance(node_or_str, str):
        return Literal(node_or_str, settings=default_settings)
    # If the child is already a node, we ensures that it has a unique id.
    # This allows using the same node in multiple places in the tree.
    else:
        return replace(node_or_str, id=_get_unique_id())
