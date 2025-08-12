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
    Iterator,
)
from dataclasses import dataclass, field

from arretify.utils.functional import iter_func_to_list
from arretify.types import TextSegment
from arretify.regex_utils import PatternProxy
from arretify.utils.strings import merge_strings
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


def pick_text_span_node(
    probe: Probe[NodeOrText],
) -> Probe[NodeOrText]:
    def _probe(elements: List[NodeOrText], index: int) -> bool:
        element = elements[index]
        if is_node(element, type_in=["text_span"]):
            return probe(elements, index)
        return False

    return _probe


def make_probe_from_pattern_proxy(
    pattern: PatternProxy, use_search: bool = False
) -> Probe[NodeOrText]:
    def _probe(elements: List[NodeOrText], index: int) -> bool:
        string = get_string(elements[index])
        if use_search is False:
            match = pattern.match(string)
        else:
            match = pattern.search(string)
        return bool(match)

    return _probe


def make_while_splitter_for_text_span_nodes(
    start_condition: Probe[NodeOrText],
    while_condition: Probe[NodeOrText],
) -> Splitter[NodeOrText, List[NodeOrText]]:
    return make_while_splitter(
        pick_text_span_node(start_condition),
        pick_if_inline_node_followed_by_match(pick_text_span_node(while_condition)),
    )


def make_single_line_splitter_for_text_span_nodes(
    is_matching: Probe[NodeOrText],
) -> Splitter[NodeOrText, List[NodeOrText]]:
    return make_single_line_splitter(
        is_matching=pick_text_span_node(is_matching),
    )


group_text_span_nodes_splitter = cast(
    Splitter[NodeOrText, List[NodeOrText]],
    make_while_splitter(
        pick_text_span_node(lambda elements, index: True),
        pick_if_inline_node_followed_by_match(pick_text_span_node(lambda elements, index: True)),
    ),
)
"""
Splitter to enable grouping of text_span nodes.
"""


def is_node(node: NodeOrText, type_in: List[str] | None = None) -> TypeGuard[Node]:
    if not isinstance(node, Node):
        return False

    if type_in is not None:
        return node.type in type_in
    return True


def get_string(node: NodeOrText) -> str:
    """
    Extracts the string from a Node or TextSegment.
    If the node is a TextSegment, it returns its contents.
    If the node is a Node, it recursively extracts strings from its text_span children.
    If its has other than text_span children, it will raises a ValueError.
    """
    if isinstance(node, TextSegment):
        return node.contents
    strings: List[str] = [_get_string(child) for child in node.children]
    return merge_strings(strings)


def _get_string(element: NodeOrText) -> str:
    if isinstance(element, TextSegment):
        return element.contents
    elif is_node(element, type_in=["text_span"]):
        return merge_strings(_get_string(child) for child in element.children)
    elif is_node(element, type_in=INLINE_NODE_TYPES):
        return ""
    else:
        raise ValueError(f"Unexpected element '{element}'")


@iter_func_to_list
def get_strings(nodes: List[NodeOrText]) -> Iterator[str]:
    for node in nodes:
        if is_node(node, type_in=["text_span"]):
            yield get_string(node)
        elif is_node(node, type_in=INLINE_NODE_TYPES):
            continue
        else:
            raise ValueError(f"Node '{node}' is not a text_span or an inline node")


def combine_text_spans(
    elements: List[NodeOrText],
) -> Node:
    """
    Combines a list of TextSegments and text_span nodes into a single text_span node.
    """
    children: List[NodeOrText] = []
    for element in elements:
        if is_node(element, type_in=["text_span"]):
            for text_span_child in element.children:
                if isinstance(text_span_child, TextSegment) or is_node(
                    text_span_child, type_in=INLINE_NODE_TYPES
                ):
                    children.append(text_span_child)
                else:
                    raise ValueError(f"Unexpected child '{text_span_child}' in of text_span node")

        elif is_node(element, type_in=INLINE_NODE_TYPES):
            children.append(element)

        else:
            raise ValueError(f"Unexpected element '{element}' ")

    return Node(
        type="text_span",
        children=children,
    )
