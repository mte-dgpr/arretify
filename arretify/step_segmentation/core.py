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
from arretify.regex_utils import PatternProxy, regex_tree
from arretify.regex_utils.regex_tree.execute import match


# -------------------- Generic splitting utils -------------------- #
# TODO : merge with other splitting utils voir #391

T1 = TypeVar("T1")
T2 = TypeVar("T2")

RawSplit = Tuple[List[T1], T2, List[T1]]
"""
Generic type alias representing a raw search & split operation on a list of elements.
It is subscribed like so `RawSplit[ElementType, MatchType]`
It represents a tuple `(before, match, after)` where:
- `before` is of type `List[ElementType]` and represents a
    list of elements before the match.
- `match` is of type `MatchType` and represents the matched element.
- `after` is of type `List[ElementType]` and represents a
    list of elements after the match.
"""

Splitter = Callable[[List[T1]], RawSplit[T1, T2] | None]
"""
Generic type alias for a function that takes a list of elements,
and returns a single RawSplit result or None if no match is found.
It is subscribed like so `Splitter[ElementType, MatchType]`
"""


@dataclass(frozen=True)
class SplitMatch(Generic[T1]):
    value: T1


@dataclass(frozen=True)
class SplitNotAMatch(Generic[T1]):
    value: T1


SplittedElement = SplitNotAMatch[List[T1]] | SplitMatch[T2]
"""
Generic type alias for an element in a splitted list.

It is subscribed like so `SplittedElement[ElementType, MatchType]`
It represents either:
- `SplitNotAMatch[List[ElementType]]` which encapsulates a list of elements that did not match.
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

Probe = Callable[[List[T1], int], bool]


@iter_func_to_list
def split_elements(
    elements: List[T1],
    splitter: Splitter[T1, T2],
) -> Iterator[SplittedElement[T1, T2]]:
    """
    Split a list of elements using the provided splitter function.

    For example :

    >>> some_numbers = [1, 3, 11, 10, 6, 23]
    >>> def multiple_of_3(elements: List[int]) -> RawSplit[int, int] | None:
    ...     for i, element in enumerate(elements):
    ...         if element % 3 == 0:
    ...             return elements[:i], element, elements[i + 1:]
    ...     return None
    >>> list(split_elements(some_numbers, multiple_of_3))
    [SplitNotAMatch([1]), SplitMatch(3), SplitNotAMatch([11, 10]), SplitMatch(6), SplitNotAMatch([23])]
    """  # noqa: E501
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


@iter_func_to_list
def map_splitted_elements(
    splitted_list: List[SplittedElement[T1, T2]],
    map_func: Callable[[T2], T1],
) -> Iterator[T1]:
    """
    Map a function over a list of SplittedElement.

    For example :

    >>> splitted_list = [
    ...     SplitNotAMatch([1, 2]),
    ...     SplitMatch('hello'),
    ...     SplitNotAMatch([4]),
    ...     SplitMatch('world'),
    ... ]
    >>> def map_func(word: str) -> str:
    ...     return word.upper()
    >>> list(map_splitted_elements(splitted_list, map_func))
    [1, 2, 'HELLO', 4, 'WORLD']
    """
    for splitted_element in splitted_list:
        if isinstance(splitted_element, SplitMatch):
            yield map_func(splitted_element.value)
        else:
            yield from splitted_element.value


@iter_func_to_list
def flat_map_splitted_elements(
    splitted_list: List[SplittedElement[T1, T2]],
    map_func: Callable[[T2], List[T1]],
) -> Iterator[T1]:
    for splitted_element in splitted_list:
        if isinstance(splitted_element, SplitMatch):
            yield from map_func(splitted_element.value)
        else:
            yield from splitted_element.value


def split_before_match(
    elements: List[T1],
    is_matching: Probe[T1],
) -> Tuple[List[T1], List[T1]]:
    """
    Split the input list into two parts, by using the `is_matching` function.

    Examples :

    strings = ["a", "b", "c"]
    >>> split_before_match(strings, lambda s: s == "b")
    (["a"], ["b", "c"])
    >>> split_before_match(strings, lambda s: s == "d")
    (["a", "b", "c"], [])
    >>> split_before_match(strings, lambda s: s == "a")
    ([], ["a", "b", "c"])
    """
    i = 0
    while i < len(elements):
        if is_matching(elements, i):
            break
        i += 1
    return elements[:i], elements[i:]


def make_single_line_splitter(
    is_matching: Probe[T1],
) -> Splitter:
    """
    Splits around the first matching element.

    For example :

    >>> strings = ["a", "b", "b", "c"]
    >>> splitter = make_single_line_splitter(lambda s: s == "b")
    >>> splitter(strings)
    (["a"], ["b"], ["b", "c"])
    """

    def _splitter(elements: List[T1]) -> RawSplit[T1, List[T1]] | None:
        before, after = split_before_match(elements, is_matching)
        if after:
            return (before, [after[0]], after[1:])
        return None

    return _splitter


def make_while_splitter(
    start_condition: Probe[T1],
    while_condition: Probe[T1],
) -> Splitter[T1, List[T1]]:
    """
    Starts the split at the first element matched by `start_condition`, and continues
    to match until the first element that does not match `while_condition`.

    For example :

    >>> strings = ["a", "b", "b", "c"]
    >>> splitter = make_while_splitter(lambda s, i: s == "b", lambda s, i: s == "b")
    >>> splitter(strings)
    (["a"], ["b", "b"], ["c"])
    """

    def _splitter(elements: List[T1]) -> RawSplit[T1, List[T1]] | None:
        before, after = split_before_match(elements, start_condition)
        if not after:
            return None
        match, after = split_before_match(
            after, lambda elements, index: not while_condition(elements, index)
        )
        return before, match, after

    return _splitter


def negate(
    probe: Probe[T1],
) -> Probe[T1]:
    """
    Negates a probe function.

    For example :

    >>> strings = ["a", "b"]
    >>> is_b = lambda elements, index: elements[index] == "b"
    >>> is_not_b = negate(is_b)
    >>> is_not_b(strings, 0)
    True
    >>> is_not_b(strings, 1)
    False
    """

    def _negated_probe(elements: List[T1], index: int) -> bool:
        return not probe(elements, index)

    return _negated_probe


# -------------------- Segmentation step splitting utils -------------------- #

NodeOrText = Union[TextSegment, "Node"]

INLINE_NODE_TYPES = ["page_separator", "page_footer"]


@dataclass(frozen=True)
class Node:
    """
    Node for representing our segmented arrêté as a tree structure.
    """

    type: str
    children: List[NodeOrText]
    data: Dict[str, Any] = field(default_factory=dict)


def group_text_segments_splitter(
    elements: List[NodeOrText],
) -> RawSplit[NodeOrText, List[TextSegment]] | None:
    """
    Splitter to enable grouping of TextSegment elements.
    """
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


def pick_if_inline_node_followed_by_match(
    is_matching: Probe[NodeOrText],
) -> Probe[NodeOrText]:
    """
    Builds a function that returns True for an inline node,
    only if it is followed by an element that matches the provided `is_matching` function.
    For other elements, it will return the result of the `is_matching` function directly.

    For example :

    >>> elements = [
    ...     TextSegment("Hello"),
    ...     Node(type="page_separator", children=[]),
    ...     TextSegment("World"),
    ...     Node(type="page_separator", children=[]),
    ...     Node(type="other_type", children=[]),
    ... ]
    >>> def is_text_segment(elements: List[NodeOrText], index: int) -> bool:
    ...     return isinstance(elements[index], TextSegment)
    >>> probe = pick_if_inline_node_followed_by_match(is_text_segment)
    >>> probe(elements, 0) # -> directly calls `is_text_segment`
    True
    >>> probe(elements, 1) # -> calls `is_text_segment` on the next element
    True
    >>> probe(elements, 3) # -> calls `is_text_segment` on the next element
    False
    """

    def _pick_inline_nodes_probe(elements: List[NodeOrText], index: int) -> bool:
        for next_index, next_element in enumerate(elements[index:], start=index):
            if is_node(next_element, type_in=INLINE_NODE_TYPES):
                continue
            else:
                return is_matching(elements, next_index)
        return False

    return _pick_inline_nodes_probe


def reject_if_not_text_segment(
    probe: Probe[NodeOrText],
) -> Probe[NodeOrText]:
    def _text_segment_probe(elements: List[NodeOrText], index: int) -> bool:
        element = elements[index]
        if isinstance(element, TextSegment):
            return probe(elements, index)
        return False

    return _text_segment_probe


def make_probe_from_pattern_proxy(
    pattern: PatternProxy, use_search: bool = False
) -> Probe[NodeOrText]:
    def _probe(elements: List[NodeOrText], index: int) -> bool:
        element = elements[index]
        assert isinstance(element, TextSegment)
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
        assert isinstance(element, TextSegment)
        return bool(match(regex_tree_node, element.contents))

    return _probe


def make_while_splitter_for_text_segments(
    start_condition: Probe[NodeOrText],
    while_condition: Probe[NodeOrText],
) -> Splitter[NodeOrText, List[NodeOrText]]:
    return make_while_splitter(
        reject_if_not_text_segment(start_condition),
        pick_if_inline_node_followed_by_match(reject_if_not_text_segment(while_condition)),
    )


def make_single_line_splitter_for_text_segments(
    is_matching: Probe[NodeOrText],
) -> Splitter[NodeOrText, List[NodeOrText]]:
    return make_single_line_splitter(
        is_matching=reject_if_not_text_segment(is_matching),
    )


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
