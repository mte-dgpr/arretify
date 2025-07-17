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
from typing import (
    Callable,
    List,
    TypeGuard,
    Dict,
    Any,
    Tuple,
    Iterator,
    Union,
    TypeVar,
    cast,
    Generic,
)
from dataclasses import dataclass, field

from arretify.types import TextSegment
from arretify.utils.functional import iter_func_to_list


INLINE_NODE_TYPES = ["page_separator", "page_footer"]


T = TypeVar("T")


@dataclass(frozen=True)
class SplitMatch(Generic[T]):
    element: T


@dataclass(frozen=True)
class SplitNotAMatch(Generic[T]):
    element: T


NodeOrText = Union[TextSegment, "Node"]
Split = Tuple[List[NodeOrText], T, List[NodeOrText]]
Splitter = Callable[[List[NodeOrText]], Split[T] | None]
Splitted = SplitMatch[T] | SplitNotAMatch[List[NodeOrText]]
Probe = Callable[[TextSegment], bool]


@dataclass(frozen=True)
class Node:
    """
    Node for representing our segmented arrêté as a tree structure.
    """

    type: str
    children: List[NodeOrText]
    data: Dict[str, Any] = field(default_factory=dict)


@iter_func_to_list
def flat_map_node_list(
    input_list: List[NodeOrText],
    map_function: Callable[[List[NodeOrText]], List[NodeOrText]],
) -> Iterator[NodeOrText]:
    pile: List[NodeOrText] = []
    for element in input_list:
        if is_node(element, type_in=INLINE_NODE_TYPES) or isinstance(element, TextSegment):
            pile.append(element)

        else:
            if pile:
                yield from map_function(pile)
                pile = []
            yield element

    if pile:
        yield from map_function(pile)


def chain_flat_map_node_list(
    input_list: List[NodeOrText],
    map_functions: List[Callable[[List[NodeOrText]], List[NodeOrText]]],
) -> List[NodeOrText]:
    for map_function in map_functions:
        input_list = flat_map_node_list(input_list, map_function)
    return input_list


@iter_func_to_list
def split_text_segments(
    input_list: List[NodeOrText],
    splitter: Splitter[T],
) -> Iterator[Splitted[T]]:
    # Here we make a copy, because we don't know
    # if the splitter will modify the input_list.
    input_list = list(input_list)
    while input_list:
        result = splitter(input_list)
        if result is None:
            yield SplitNotAMatch(input_list)
            break
        before, match, input_list = result

        if before:
            yield SplitNotAMatch(before)
        yield SplitMatch(match)


def make_single_line_splitter(
    is_matching: Probe,
) -> Splitter:
    def _splitter(input_list: List[NodeOrText]) -> Split | None:
        before, after = split_before_match(input_list, is_matching)
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

    def _splitter(input_list: List[NodeOrText]) -> Split | None:
        before, after = split_before_match(input_list, start_is_matching)
        if not after:
            return None
        match, after = split_before_match(after, lambda t: not is_matching(t))
        return before, match, after

    return _splitter


def text_segment_group_splitter(
    input_list: List[NodeOrText],
) -> Split[List[TextSegment]] | None:
    input_list = list(input_list)
    before: List[NodeOrText] = []
    match: List[TextSegment] = []
    while input_list and is_node(input_list[0]):
        before.append(input_list[0])
        input_list.pop(0)

    while input_list and isinstance(input_list[0], TextSegment):
        match.append(input_list[0])
        input_list.pop(0)

    if match:
        return (before, match, input_list)
    return None


def split_before_match(
    input_list: List[NodeOrText],
    is_matching: Probe,
) -> Tuple[List[NodeOrText], List[NodeOrText]]:
    """
    Split the lines into two parts, by using the `is_matching` function.

    Examples :

    lines = initialize_page("a\nb\nc", 0)
    split_before_match(lines, lambda x: x.contents == "b") -> (["a"], ["b", "c"])
    split_before_match(lines, lambda x: x.contents == "d") -> (["a", "b", "c"], [])
    split_before_match(lines, lambda x: x.contents == "a") -> ([], ["a", "b", "c"])
    """
    i = 0
    while i < len(input_list):
        element = input_list[i]
        if isinstance(element, TextSegment) and is_matching(element):
            break
        i += 1
    return input_list[:i], input_list[i:]


@iter_func_to_list
def map_splitted_text_segments(
    splitted_list: List[Splitted[T]],
    map_func: Callable[[T], Node],
) -> Iterator[NodeOrText]:
    for splitted in splitted_list:
        if isinstance(splitted, SplitMatch):
            yield map_func(splitted.element)
        else:
            yield from splitted.element


@iter_func_to_list
def flat_map_splitted_text_segments(
    splitted_list: List[Splitted[T]],
    map_func: Callable[[T], List[NodeOrText]],
) -> Iterator[NodeOrText]:
    for splitted in splitted_list:
        if isinstance(splitted, SplitMatch):
            yield from map_func(splitted.element)
        else:
            yield from splitted.element


def is_node(node: Node | TextSegment, type_in: List[str] | None = None) -> TypeGuard[Node]:
    if not isinstance(node, Node):
        return False

    if type_in is not None:
        return node.type in type_in
    return True


def assert_single_text_segment(node: Node) -> TextSegment:
    assert len(node.children) == 1 and isinstance(
        node.children[0], TextSegment
    ), f"Node '{node.type}' must contain exactly one TextSegment"
    return node.children[0]


def assert_all_text_segments(
    node: Node,
) -> List[TextSegment]:
    """
    Assert that all children of the node are TextSegment.
    """
    assert all(
        isinstance(child, TextSegment) for child in node.children
    ), f"Node '{node.type}' must contain only TextSegment"
    return cast(List[TextSegment], node.children)
