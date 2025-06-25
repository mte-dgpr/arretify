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
from typing import Callable, Iterable, List, TypeGuard, Dict, Any
from dataclasses import dataclass, field

from arretify.types import TextSegments, TextSegment, DataElementDataDict


NodeFlow = Iterable[TextSegments | "Node"]


@dataclass(frozen=True)
class Node:
    type: str
    children: List[TextSegments | "Node"]
    data: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        # Make sure children are a list and not an iterator
        if not isinstance(self.children, list):
            self.children = list(self.children)


def flat_map_node_flow(
    nodes: NodeFlow,
    map_func: Callable[[TextSegments], NodeFlow],
) -> List[TextSegments | Node]:
    output: List[TextSegments | Node] = []
    for node in nodes:
        if isinstance(node, Node):
            output.append(node)
        else:
            output.extend(map_func(node))
    return output


def assert_single_text_segments(node: Node) -> TextSegments:
    if len(node.children) != 1 or isinstance(node.children[0], Node):
        raise ValueError(
            f"Node '{node.type}' must contain exactly one TextSegments, "
            f"but found {len(node.children)} nodes."
        )
    return node.children[0]


def assert_single_text_segment(node: Node) -> TextSegment:
    text_segments = assert_single_text_segments(node)
    if len(text_segments) != 1:
        raise ValueError(
            f"Node '{node.type}' must contain exactly one line, "
            f"but found {len(text_segments)} lines."
        )
    return text_segments[0]


def is_node(node: Node | TextSegments, type_in: List[str] | None = None) -> TypeGuard[Node]:
    if not isinstance(node, Node):
        return False

    if type_in is not None:
        return node.type in type_in
    return True
