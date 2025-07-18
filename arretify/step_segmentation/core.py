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
    Iterable,
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
from arretify.regex_utils import PatternProxy, regex_tree
from arretify.regex_utils.regex_tree.execute import match


INLINE_NODE_TYPES = ["page_separator", "page_footer"]


T1 = TypeVar("T1")
T2 = TypeVar("T2")


Split = Tuple[List[T1], T2, List[T1]]
"""
Generic type alias representing a raw search & split operation on a list of elements.
It is subscribed like so `Split[ElementType, MatchType]`
It represents a tuple `(before, match, after)` where:
- `before` is of type `List[ElementType]` and represents a
    list of elements before the match.
- `match` is of type `MatchType` and represents the matched element.
- `after` is of type `List[ElementType]` and represents a
    list of elements after the match.
"""

Splitter = Callable[[List[T1]], Split[T1, T2] | None]
"""
Generic type alias for a function that takes a list of elements,
and returns a raw split result or None if no match is found.
It is subscribed like so `Splitter[ElementType, MatchType]`
"""


@dataclass(frozen=True)
class SplitMatch(Generic[T1]):
    value: T1


@dataclass(frozen=True)
class SplitNotAMatch(Generic[T1]):
    value: T1


Splitted = Iterable[SplitNotAMatch[List[T1]] | SplitMatch[T2]]
"""
Generic type alias for an iterable of split results.

It is subscribed like so `Splitted[ElementType, MatchType]`
It represents an iterable of either:
- `SplitNotAMatch[List[ElementType]]` which contains a list of elements that did not match.
- `SplitMatch[MatchType]` which contains the matched element.

This is useful for processing a list of elements and tagging as matches or non-matches
in a generic manner. This enables proper typing and handling of the results like so :

```
if isinstance(splitted_element, SplitMatch):
    splitted_element.value  # This is of type MatchType
elif isinstance(splitted_element, SplitNotAMatch):
    splitted_element.value  # This is of type List[ElementType]
```
"""

# TODO: Callable[[List[T1], int, T2], bool] ???
Probe = Callable[[List[T1], int], bool]

NodeOrText = Union[TextSegment, "Node"]


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
    elements: List[NodeOrText],
    map_function: Callable[[List[NodeOrText]], List[NodeOrText]],
) -> Iterator[NodeOrText]:
    pile: List[NodeOrText] = []
    for element in elements:
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
    elements: List[NodeOrText],
    map_functions: List[Callable[[List[NodeOrText]], List[NodeOrText]]],
) -> List[NodeOrText]:
    for map_function in map_functions:
        elements = flat_map_node_list(elements, map_function)
    return elements


def split_before_match(
    elements: List[T1],
    is_matching: Probe[T1],
) -> Tuple[List[T1], List[T1]]:
    """
    Split the input list into two parts, by using the `is_matching` function.

    Examples :

    strings = ["a", "b", "c"]
    split_before_match(strings, lambda s: s == "b") -> (["a"], ["b", "c"])
    split_before_match(strings, lambda s: s == "d") -> (["a", "b", "c"], [])
    split_before_match(strings, lambda s: s == "a") -> ([], ["a", "b", "c"])
    """
    i = 0
    while i < len(elements):
        if is_matching(elements, i):
            break
        i += 1
    return elements[:i], elements[i:]


@iter_func_to_list
def split_text_segments(
    elements: List[T1],
    splitter: Splitter[T1, T2],
) -> Splitted[T1, T2]:
    # Here we make a copy, because we don't know
    # if the splitter will modify the elements.
    elements = list(elements)
    while elements:
        result = splitter(elements)
        if result is None:
            yield SplitNotAMatch(elements)
            break
        before, match, elements = result

        if before:
            yield SplitNotAMatch(before)
        yield SplitMatch(match)


def make_single_line_splitter(
    is_matching: Probe[T1],
) -> Splitter:
    def _splitter(elements: List[T1]) -> Split[T1, List[T1]] | None:
        before, after = split_before_match(elements, is_matching)
        if after:
            return (before, [after[0]], after[1:])
        return None

    return _splitter


def make_while_splitter(
    is_matching: Probe[T1],
    start_is_matching: Probe[T1] | None = None,
) -> Splitter[T1, List[T1]]:
    if start_is_matching is None:
        start_is_matching = is_matching

    def _splitter(elements: List[T1]) -> Split[T1, List[T1]] | None:
        before, after = split_before_match(elements, start_is_matching)
        if not after:
            return None
        match, after = split_before_match(
            after, lambda elements, index: not is_matching(elements, index)
        )
        return before, match, after

    return _splitter


def make_negated_probe(
    probe: Probe[T1],
) -> Probe[T1]:
    def _negated_probe(elements: List[T1], index: int) -> bool:
        return not probe(elements, index)

    return _negated_probe


def text_segment_group_splitter(
    elements: List[NodeOrText],
) -> Split[NodeOrText, List[TextSegment]] | None:
    elements = list(elements)
    before: List[NodeOrText] = []
    match: List[TextSegment] = []
    while elements and is_node(elements[0]):
        before.append(elements[0])
        elements.pop(0)

    while elements and isinstance(elements[0], TextSegment):
        match.append(elements[0])
        elements.pop(0)

    if match:
        return (before, match, elements)
    return None


def make_pass_through_probe_for_inline_nodes(
    is_matching: Probe[NodeOrText],
) -> Probe[NodeOrText]:
    def _probe(elements: List[NodeOrText], index: int) -> bool:
        for next_index, next_element in enumerate(elements[index:], start=index):
            if isinstance(next_element, TextSegment):
                return is_matching(elements, next_index)
            elif is_node(next_element, type_in=INLINE_NODE_TYPES):
                continue
            else:
                return False

    return _probe


def make_text_segment_probe(
    is_matching: Probe[NodeOrText],
) -> Probe[NodeOrText]:
    def _probe(elements: List[NodeOrText], index: int) -> bool:
        element = elements[index]
        if isinstance(element, TextSegment):
            return is_matching(elements, index)
        return False

    return _probe


def make_probe_from_pattern_proxy(
    pattern: PatternProxy, use_search: bool = False
) -> Probe[TextSegment]:
    def _probe(elements: List[NodeOrText], index: int) -> bool:
        element = elements[index]
        if use_search is False:
            match = pattern.match(element.contents)
        else:
            match = pattern.search(element.contents)
        return bool(match)

    return _probe


def make_probe_from_regex_tree(
    regex_tree_node: regex_tree.GroupNode,
) -> Probe[NodeOrText]:
    def _probe(elements: List[NodeOrText], index: int) -> bool:
        element = elements[index]
        return bool(match(regex_tree_node, element.contents))

    return _probe


def make_text_segment_while_splitter(
    is_matching: Probe[NodeOrText],
    start_is_matching: Probe[NodeOrText] | None = None,
) -> Splitter[NodeOrText, List[TextSegment]]:
    return make_while_splitter(
        is_matching=make_pass_through_probe_for_inline_nodes(is_matching),
        start_is_matching=make_text_segment_probe(start_is_matching or is_matching),
    )


def make_text_segment_single_line_splitter(
    is_matching: Probe[NodeOrText],
) -> Splitter[NodeOrText, List[TextSegment]]:
    return make_single_line_splitter(
        is_matching=make_text_segment_probe(is_matching),
    )


@iter_func_to_list
def map_splitted_text_segments(
    splitted_list: Splitted[T1, T2],
    map_func: Callable[[T2], T1],
) -> Iterator[T1]:
    for splitted_element in splitted_list:
        if isinstance(splitted_element, SplitMatch):
            yield map_func(splitted_element.value)
        else:
            yield from splitted_element.value


@iter_func_to_list
def flat_map_splitted_text_segments(
    splitted_list: Splitted[T1, T2],
    map_func: Callable[[T2], List[T1]],
) -> Iterator[T1]:
    for splitted_element in splitted_list:
        if isinstance(splitted_element, SplitMatch):
            yield from map_func(splitted_element.value)
        else:
            yield from splitted_element.value


def is_node(node: Node | TextSegment, type_in: List[str] | None = None) -> TypeGuard[Node]:
    if not isinstance(node, Node):
        return False

    if type_in is not None:
        return node.type in type_in
    return True


def assert_single_text_segment(node: Node) -> TextSegment:
    """
    Assert that the node contains exactly one TextSegment.
    """
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
