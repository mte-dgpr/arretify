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
from typing import Callable, Iterable, List, TypeGuard, Dict, Any, Tuple, Iterator
from dataclasses import dataclass, field

from arretify.types import TextSegments, TextSegment


NodeFlow = Iterable[TextSegments | "Node"]
NodeList = List[TextSegments | "Node"]
Split = Tuple[TextSegments, TextSegments, TextSegments]
Splitter = Callable[[TextSegments], Split | None]
Probe = Callable[[TextSegment], bool]


@dataclass(frozen=True)
class Node:
    """
    Node for representing our segmented arrêté as a tree structure.
    """

    type: str
    children: NodeList
    data: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        # Make sure children are a list and not an iterator
        if not isinstance(self.children, list):
            self.children = list(self.children)


def flat_map_node_flow(
    node_flow: NodeFlow,
    map_functions: Callable[[TextSegments], NodeFlow],
) -> NodeList:
    output: NodeList = []
    for node_or_text_segments in node_flow:
        if isinstance(node_or_text_segments, Node):
            output.append(node_or_text_segments)
        else:
            output.extend(map_functions(node_or_text_segments))
    return output


def chain_flat_map_node_flow(
    node_flow: NodeFlow,
    map_functions: List[Callable[[TextSegments], NodeFlow]],
) -> NodeList:
    for map_function in map_functions:
        node_flow = flat_map_node_flow(node_flow, map_function)
    return list(node_flow)


def split_text_segments(
    lines: TextSegments,
    splitter: Splitter,
) -> Iterator[Tuple[bool, TextSegments]]:
    lines = list(lines)
    while lines:
        result = splitter(lines)
        if result is None:
            yield (False, lines)
            break
        before, match, after = result

        if before:
            yield (False, before)
        yield (True, match)
        lines = after


def make_single_line_splitter(
    is_matching: Probe,
) -> Splitter:
    def _splitter(lines: TextSegments) -> Split | None:
        before, after = split_before_match(lines, is_matching)
        if after:
            return before, [after[0]], after[1:]
        return None

    return _splitter


def make_while_splitter(
    is_matching: Probe,
    start_is_matching: Probe | None = None,
) -> Splitter:
    if start_is_matching is None:
        start_is_matching = is_matching

    def _splitter(lines: TextSegments) -> Split | None:
        before, after = split_before_match(lines, start_is_matching)
        if not after:
            return None
        match, after = split_before_match(after, lambda t: not is_matching(t))
        return before, match, after

    return _splitter


def split_before_match(
    lines: TextSegments,
    is_matching: Probe,
) -> Tuple[TextSegments, TextSegments]:
    """
    Split the lines into two parts, by using the `is_matching` function.

    Examples :

    lines = initialize_lines(["a", "b", "c"])
    split_before_match(lines, lambda x: x.contents == "b") -> (["a"], ["b", "c"])
    split_before_match(lines, lambda x: x.contents == "d") -> (["a", "b", "c"], [])
    split_before_match(lines, lambda x: x.contents == "a") -> ([], ["a", "b", "c"])
    """
    i = 0
    while i < len(lines) and not is_matching(lines[i]):
        i += 1
    return lines[:i], lines[i:]


def map_splitted_text_segments(
    input_flow: Iterable[Tuple[bool, TextSegments]],
    map_func: Callable[[TextSegments], Node],
) -> NodeList:
    output: NodeList = []
    for is_match, text_segments in input_flow:
        if is_match:
            output.append(map_func(text_segments))
        else:
            output.append(text_segments)
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
