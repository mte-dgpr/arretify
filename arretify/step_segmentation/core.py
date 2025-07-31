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
    List,
    TypeGuard,
    Dict,
    Any,
    Union,
    cast,
)
from dataclasses import dataclass, field

from arretify.types import TextSegment
from arretify.regex_utils import PatternProxy
from arretify.utils.split_merge import (
    make_while_splitter,
    make_single_line_splitter,
    Splitter,
    Probe,
)


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


def pick_text_segment(
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


def make_probe_from_pattern(
    pattern: PatternProxy,
) -> Probe[NodeOrText]:
    def _probe(elements: List[NodeOrText], index: int) -> bool:
        element = elements[index]
        assert isinstance(element, TextSegment)
        return bool(pattern.match(element.contents))

    return _probe


def make_while_splitter_for_text_segments(
    start_condition: Probe[NodeOrText],
    while_condition: Probe[NodeOrText],
) -> Splitter[NodeOrText, List[NodeOrText]]:
    return make_while_splitter(
        pick_text_segment(start_condition),
        pick_if_inline_node_followed_by_match(pick_text_segment(while_condition)),
    )


def make_single_line_splitter_for_text_segments(
    is_matching: Probe[NodeOrText],
) -> Splitter[NodeOrText, List[NodeOrText]]:
    return make_single_line_splitter(
        is_matching=pick_text_segment(is_matching),
    )


group_text_segments_splitter = cast(
    Splitter[NodeOrText, List[TextSegment]],
    make_while_splitter(
        pick_text_segment(lambda elements, index: True),
        pick_if_inline_node_followed_by_match(pick_text_segment(lambda elements, index: True)),
    ),
)
"""
Splitter to enable grouping of TextSegment elements.
"""


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
