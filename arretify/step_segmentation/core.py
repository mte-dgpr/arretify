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

from arretify.parsing_utils.patterns import is_continuing_sentence
from arretify.utils.functional import iter_func_to_list
from arretify.regex_utils import PatternProxy, MatchProxy
from arretify.utils.strings import merge_strings
from arretify.utils.split_merge import (
    make_while_splitter,
    make_single_line_splitter,
    Splitter,
    Probe,
    RawSplit,
    split_elements,
    merge_splitted_elements,
    SplitMatch,
    split_before_match,
)


NodeOrText = Union["Node", str]

TRANSPARENT_NODE_TYPES = ["page_separator", "page_footer"]
"""
List of node types that are considered transparent for text extraction purposes.
"""

INLINE_NODE_TYPES = ["address"]
"""
List of node types that contains specific bits of text information inside a text_span.
"""


@dataclass(frozen=True)
class Node:
    """
    Node for representing our segmented arrêté as a tree structure.
    """

    type: str
    children: List[NodeOrText]
    data: Dict[str, Any] = field(default_factory=dict)


def pick_if_transparent_node_followed_by_match(
    is_matching: Probe[NodeOrText],
) -> Probe[NodeOrText]:
    """
    Builds a function that returns True for a transparent node,
    only if it is followed by an element that matches the provided `is_matching` function.
    For other elements, it will return the result of the `is_matching` function directly.

    For example :

    >>> elements = [
    ...     "Hello",
    ...     Node(type="page_separator", children=[]),
    ...     "World",
    ...     Node(type="page_separator", children=[]),
    ...     Node(type="other_type", children=[]),
    ... ]
    >>> def is_string(elements: List[NodeOrText], index: int) -> bool:
    ...     return isinstance(elements[index], str)
    >>> probe = pick_if_transparent_node_followed_by_match(is_string)
    >>> probe(elements, 0) # -> directly calls `is_string`
    True
    >>> probe(elements, 1) # -> calls `is_string` on the next element
    True
    >>> probe(elements, 3) # -> calls `is_string` on the next element
    False
    """

    def _pick_transparent_nodes_probe(elements: List[NodeOrText], index: int) -> bool:
        for next_index, next_element in enumerate(elements[index:], start=index):
            if is_node(next_element, type_in=TRANSPARENT_NODE_TYPES):
                continue
            else:
                return is_matching(elements, next_index)
        return False

    return _pick_transparent_nodes_probe


def pick_text_span_node(
    probe: Probe[NodeOrText],
) -> Probe[NodeOrText]:
    def _probe(elements: List[NodeOrText], index: int) -> bool:
        element = elements[index]
        if is_node(element, type_in=["text_span"]):
            return probe(elements, index)
        return False

    return _probe


def pick_str(
    probe: Probe[NodeOrText],
) -> Probe[NodeOrText]:
    def _probe(elements: List[NodeOrText], index: int) -> bool:
        element = elements[index]
        if isinstance(element, str):
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
        pick_if_transparent_node_followed_by_match(pick_text_span_node(while_condition)),
    )


def make_single_line_splitter_for_text_span_nodes(
    is_matching: Probe[NodeOrText],
) -> Splitter[NodeOrText, List[NodeOrText]]:
    return make_single_line_splitter(
        is_matching=pick_text_span_node(is_matching),
    )


def make_pattern_splitter(
    pattern: PatternProxy,
) -> Splitter[NodeOrText, MatchProxy]:
    def _splitter(
        elements: List[NodeOrText],
    ) -> RawSplit[NodeOrText, MatchProxy] | None:
        splitted_elements = split_elements(elements, group_str_splitter)
        for i, splitted_element in enumerate(splitted_elements):
            if not isinstance(splitted_element, SplitMatch):
                continue

            string: str = merge_strings([get_string(element) for element in splitted_element.value])
            match_proxy = pattern.search(string)
            if not match_proxy:
                continue

            before = merge_splitted_elements(splitted_elements[:i])
            if match_proxy.start() > 0:
                before.append(string[: match_proxy.start()])

            after = merge_splitted_elements(splitted_elements[i + 1 :])
            if match_proxy.end() < len(string):
                after.insert(0, string[match_proxy.end() :])

            return (
                before,
                match_proxy,
                after,
            )
        return None

    return _splitter


group_text_span_nodes_splitter = cast(
    Splitter[NodeOrText, List[NodeOrText]],
    make_while_splitter(
        pick_text_span_node(lambda elements, index: True),
        pick_if_transparent_node_followed_by_match(
            pick_text_span_node(lambda elements, index: True)
        ),
    ),
)
"""
Splitter to enable grouping of text_span nodes.
"""


group_str_splitter = cast(
    Splitter[NodeOrText, List[NodeOrText]],
    make_while_splitter(
        pick_str(lambda elements, index: True),
        pick_str(lambda elements, index: True),
    ),
)
"""
Splitter to enable grouping of strings.
"""


def make_recombine_interrupted_lines_splitter(
    start_node_type: str,
) -> Splitter[NodeOrText, List[NodeOrText]]:
    """
    Builds a splitter for groupping text that is interrupted by page separators.
    """

    def _splitter(
        elements: List[NodeOrText],
    ) -> RawSplit[NodeOrText, List[NodeOrText]] | None:
        before: List[NodeOrText] = []
        while elements:
            # Find the next starting element
            before_start, elements = split_before_match(
                elements, lambda elements, i: is_node(elements[i], type_in=[start_node_type])
            )
            before.extend(before_start)
            if not elements:
                break

            start_element = elements.pop(0)
            match_elements = [start_element]
            previous_text = get_string(start_element)
            # Continue to add elements as long as we find continuing sentences,
            # i.e a group that follows the pattern:
            #   <page_separator>    # One or several page separators
            #   <text_span>         # A text span that continues the previous text
            while True:
                page_separators, elements = split_before_match(
                    elements,
                    lambda elements, i: (
                        i > 0  # need at least one page separator
                        and all(is_node(el, type_in=["page_separator"]) for el in elements[:i])
                        and is_node(elements[i], type_in=["text_span"])
                        and is_continuing_sentence(previous_text, get_string(elements[i]))
                    ),
                )

                if not elements:
                    # Restore elements if no match
                    elements = page_separators
                    break

                # We have a match, add the page separators and the next element.
                match_elements.extend(page_separators)
                next_element = elements.pop(0)
                match_elements.append(next_element)
                previous_text = get_string(next_element)

            if len(match_elements) > 1:
                return (before, match_elements, elements)
            else:
                before.extend(match_elements)

        return None

    return _splitter


def is_node(node: NodeOrText, type_in: List[str] | None = None) -> TypeGuard[Node]:
    if not isinstance(node, Node):
        return False

    if type_in is not None:
        return node.type in type_in
    return True


def get_string(node: NodeOrText) -> str:
    """
    Extracts the string from a Node.
    If the node is a str, it returns it.
    If the node is a Node, it recursively extracts strings from its text_span children.
    If its has other than text_span children, it will raises a ValueError.
    """
    if isinstance(node, str):
        return node
    strings: List[str] = [_get_string(child) for child in node.children]
    return merge_strings(strings)


def _get_string(element: NodeOrText) -> str:
    if isinstance(element, str):
        return element
    elif is_node(element, type_in=["text_span", *INLINE_NODE_TYPES]):
        return merge_strings(_get_string(child) for child in element.children)
    elif is_node(element, type_in=TRANSPARENT_NODE_TYPES):
        return ""
    else:
        raise ValueError(f"Unexpected element '{element}'")


@iter_func_to_list
def get_strings(nodes: List[NodeOrText]) -> Iterator[str]:
    for node in nodes:
        if is_node(node, type_in=["text_span"]):
            yield get_string(node)
        elif is_node(node, type_in=TRANSPARENT_NODE_TYPES):
            continue
        else:
            raise ValueError(f"Node '{node}' is not a text_span or an transparent node")


def combine_text_spans(
    elements: List[NodeOrText],
) -> Node:
    """
    Combines a list of strings and text_span nodes into a single text_span node.
    """
    children: List[NodeOrText] = []
    first_text_span: Node | None = None
    last_text_span: Node | None = None
    for element in elements:
        if is_node(element, type_in=["text_span"]):
            if first_text_span is None:
                first_text_span = element
            last_text_span = element
            for text_span_child in element.children:
                if isinstance(text_span_child, str) or is_node(
                    text_span_child, type_in=TRANSPARENT_NODE_TYPES + INLINE_NODE_TYPES
                ):
                    children.append(text_span_child)
                else:
                    raise ValueError(f"Unexpected child '{text_span_child}' in of text_span node")

        elif is_node(element, type_in=TRANSPARENT_NODE_TYPES):
            children.append(element)

        else:
            raise ValueError(f"Unexpected element '{element}' ")

    assert first_text_span is not None and last_text_span is not None, "No text_span found"
    return Node(
        type="text_span",
        children=children,
        data=dict(start=first_text_span.data["start"], end=last_text_span.data["end"]),
    )
