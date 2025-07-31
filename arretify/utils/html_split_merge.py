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
from typing import List, Iterable, Iterator, Tuple
from dataclasses import dataclass

from arretify.utils.functional import iter_func_to_list
from arretify.utils.html import is_tag_and_matches
from arretify.utils.split_merge import (
    Probe,
    make_while_splitter,
    RawSplit,
    Splitter,
    SplitMatch,
    SplitNotAMatch,
    SplittedElement,
    split_elements,
    flat_map_splitted_elements,
)
from arretify.types import PageElementOrString
from arretify.regex_utils import safe_group, MatchProxy, PatternProxy
from arretify.regex_utils.regex_tree.types import (
    Node,
    RegexTreeMatch,
    LiteralNode,
    BranchingNode,
    RepeatNode,
    GroupNode,
    SequenceNode,
    RegexTreeMatchFlow,
    GroupName,
)
from arretify.utils.strings import merge_strings


INLINE_TAG_TYPES = ["br"]


def pick_if_inline_tag_followed_by_match(
    is_matching: Probe[PageElementOrString],
) -> Probe[PageElementOrString]:
    """
    Builds a function that returns True for an inline tag,
    only if it is followed by an element that matches the provided `is_matching` function.
    For other elements, it will return the result of the `is_matching` function directly.

    For example :

    >>> elements = [
    ...     "Hello",
    ...     Tag(type="br"),
    ...     "World",
    ...     Tag(type="br"),
    ...     Tag(type="other_type"),
    ... ]
    >>> def is_string(elements: List[PageElementOrString], index: int) -> bool:
    ...     return isinstance(elements[index], str)
    >>> probe = pick_if_inline_tag_followed_by_match(is_string)
    >>> probe(elements, 0) # -> directly calls `is_string`
    True
    >>> probe(elements, 1) # -> calls `is_string` on the next element
    True
    >>> probe(elements, 3) # -> calls `is_string` on the next element
    False
    """

    def _pick_inline_tags_probe(elements: List[PageElementOrString], index: int) -> bool:
        for next_index, next_element in enumerate(elements[index:], start=index):
            if is_tag_and_matches(next_element, tag_name_in=INLINE_TAG_TYPES):
                continue
            else:
                return is_matching(elements, next_index)
        return False

    return _pick_inline_tags_probe


def pick_string(
    probe: Probe[PageElementOrString],
) -> Probe[PageElementOrString]:
    def _string_probe(elements: List[PageElementOrString], index: int) -> bool:
        element = elements[index]
        if isinstance(element, str):
            return probe(elements, index)
        return False

    return _string_probe


group_strings_splitter = make_while_splitter(
    pick_string(lambda elements, index: True),
    pick_string(lambda elements, index: True),
)
"""
Splitter to enable grouping of string elements.
"""


group_strings_and_inline_tags_splitter: Splitter[PageElementOrString, List[PageElementOrString]] = (
    make_while_splitter(
        pick_string(lambda elements, index: True),
        pick_if_inline_tag_followed_by_match(pick_string(lambda elements, index: True)),
    )
)
"""
Splitter to enable grouping of string elements and inline tags,
when these are preceded and followed by strings.
"""


@iter_func_to_list
def filter_out_inline_tags(
    elements: Iterable[PageElementOrString],
) -> Iterator[PageElementOrString]:
    for element in elements:
        if not is_tag_and_matches(element, tag_name_in=INLINE_TAG_TYPES):
            yield element


@dataclass(frozen=True)
class _PatternSplitterMatch:
    elements: List[PageElementOrString]
    match_proxy: MatchProxy


def make_pattern_splitter(
    pattern: PatternProxy,
) -> Splitter[PageElementOrString, _PatternSplitterMatch]:
    def _splitter(
        elements: List[PageElementOrString],
    ) -> RawSplit[PageElementOrString, _PatternSplitterMatch] | None:
        grouped_strings = split_elements(elements, group_strings_and_inline_tags_splitter)

        for i, splitted_element in enumerate(grouped_strings):
            if not isinstance(splitted_element, SplitMatch):
                continue

            # Trim strings before merging to avoid double spaces.
            # We have to do this directly in the list of elements we are working
            # with, otherwise `_slice_elements_with_string_index` will not work correctly.
            group_elements = _trim_strings_before_merging(splitted_element.value)
            merged_string = merge_strings(group_elements, strip_other_types=True)

            match_proxy = pattern.search(merged_string)
            if not match_proxy:
                continue

            before_match, match_elements, after_match = _slice_elements_with_string_index(
                group_elements,
                match_proxy.start(),
                match_proxy.end(),
            )
            before = _flatten_regex_tree_splitted_elements(grouped_strings[:i]) + before_match
            after = after_match + _flatten_regex_tree_splitted_elements(grouped_strings[i + 1 :])

            return (
                before,
                _PatternSplitterMatch(elements=match_elements, match_proxy=match_proxy),
                after,
            )
        return None

    return _splitter


def _trim_strings_before_merging(elements: List[PageElementOrString]) -> List[PageElementOrString]:
    """
    Trims spaces in string elements before and after an inline tag in order
    to avoid double spaces. Example:

    >>> _trim_strings_before_merging(["Hello ", <br/>, " World"])
    ["Hello", <br/>, " World"]
    """
    elements = list(elements)
    for i, element in enumerate(elements):
        if not is_tag_and_matches(element, tag_name_in=INLINE_TAG_TYPES) or i == 0:
            continue

        previous_element = elements[i - 1]
        if not isinstance(previous_element, str):
            continue

        next_string_element_index = i + 1
        while next_string_element_index < len(elements) and not isinstance(
            elements[next_string_element_index], str
        ):
            next_string_element_index += 1
        if next_string_element_index >= len(elements):
            continue
        next_string_element = elements[next_string_element_index]
        assert isinstance(next_string_element, str)

        if previous_element.endswith(" ") and next_string_element.startswith(" "):
            elements[i - 1] = previous_element.rstrip()
    return elements


@iter_func_to_list
def _flatten_regex_tree_splitted_elements(
    splitted_list: List[SplittedElement[PageElementOrString, List[PageElementOrString]]],
) -> Iterator[PageElementOrString]:
    for splitted_element in splitted_list:
        if isinstance(splitted_element, SplitMatch):
            yield from splitted_element.value
        elif isinstance(splitted_element, SplitNotAMatch):
            yield from splitted_element.value
        else:
            raise RuntimeError(
                "Unexpected type in splitted_list, expected SplitMatch or SplitNotAMatch"
            )


def _slice_elements_with_string_index(
    elements: List[PageElementOrString], start: int, end: int
) -> RawSplit[PageElementOrString, List[PageElementOrString]]:
    before_match, match_elements = _split_before_string_index(elements, start)
    match_elements, after_match = _split_before_string_index(match_elements, end - start)
    return before_match, match_elements, after_match


def _split_before_string_index(
    elements: List[PageElementOrString], split_index: int
) -> Tuple[List[PageElementOrString], List[PageElementOrString]]:
    current_index = 0
    for i, element in enumerate(elements):
        if not isinstance(element, str):
            continue
        current_index += len(element)
        if current_index <= split_index:
            continue
        surplus = current_index - split_index

        string_before = element[:-surplus]
        before = elements[:i]
        if string_before:
            before.append(string_before)

        string_after = element[-surplus:]
        after = [string_after] + elements[i + 1 :]
        return (before, after)
    return (elements, [])


def regex_tree_match(elements: List[PageElementOrString], node: GroupNode) -> RegexTreeMatch:
    try:
        results = list(_regex_tree_match_recursive(elements, node, None))
    except NoMatch:
        raise ValueError("No match found for the provided regex tree node.")

    if len(results) != 1 or not isinstance(results[0], RegexTreeMatch):
        raise RuntimeError(f"expected exactly one match group, got {results}")
    else:
        return results[0]


def _regex_tree_match_recursive(
    elements: List[PageElementOrString],
    node: Node,
    current_group: RegexTreeMatch | None,
) -> RegexTreeMatchFlow:
    # For BranchingNode, we can't use `pattern` to match the string,
    # we have to try each child until we find a match.
    if isinstance(node, BranchingNode):
        for child in node.children.values():
            try:
                children_results = list(_regex_tree_match_recursive(elements, child, current_group))
            except NoMatch:
                continue
            # Yield and return on first match
            yield from children_results
            return
        else:
            raise NoMatch()

    elif isinstance(node, GroupNode):
        child_group = RegexTreeMatch(
            children=[],
            group_name=node.group_name,
            match_dict=dict(),
        )
        child_group.children.extend(_regex_tree_match_recursive(elements, node.child, child_group))
        yield child_group
        return

    # For other nodes, there is no problem using `pattern`.
    split = make_pattern_splitter(node.pattern)(elements)
    if not split:
        raise NoMatch()
    if not current_group:
        raise RuntimeError("current_group should not be None")
    before, node_match, after = split
    if before or after:
        raise NoMatch()

    if isinstance(node, LiteralNode):
        # Remove None values from the match_dict
        current_group.match_dict.update(
            {k: v for k, v in node_match.match_proxy.groupdict().items() if v is not None}
        )
        yield from node_match.elements
        return

    elif isinstance(node, RepeatNode):
        yield from flat_map_splitted_elements(
            split_elements(
                node_match.elements,
                make_pattern_splitter(node.child.pattern),
            ),
            lambda repeat_match: _regex_tree_match_recursive(
                repeat_match.elements,
                node.child,
                current_group,
            ),
        )

    elif isinstance(node, SequenceNode):
        yield from flat_map_splitted_elements(
            _split_match_by_named_groups(node_match.match_proxy, node_match.elements),
            lambda named_group_match: _regex_tree_match_recursive(
                named_group_match.elements,
                node.children[named_group_match.group_name],
                current_group,
            ),
        )

    else:
        raise RuntimeError(f"unexpected node type: {node}")


class NoMatch(Exception):
    """
    Enables the algorithm to break out of the current branch and try the next one.
    """


@dataclass(frozen=True)
class _NamedGroupSplitterMatch:
    elements: List[PageElementOrString]
    group_name: GroupName


@iter_func_to_list
def _split_match_by_named_groups(
    match_proxy: MatchProxy,
    elements: List[PageElementOrString],
) -> Iterator[SplittedElement[PageElementOrString, _NamedGroupSplitterMatch]]:
    safe_group(match_proxy, 0)
    # Offset in original text
    match_proxy.start(0)
    match_dict = match_proxy.groupdict()

    # List all named groups and sort them by start index
    group_names = list(match_dict.keys())
    # Sorting seems to work fine if two groups have same start.
    # The containing group then is put before the nested group in the list,
    # Which is the desired behavior.
    group_names.sort(key=lambda n: match_proxy.start(n))
    max_group_end = 0
    for group_name in group_names:
        before, match_elements, elements = _slice_elements_with_string_index(
            elements,
            start=match_proxy.start(group_name) - max_group_end,
            end=match_proxy.end(group_name) - max_group_end,
        )
        max_group_end = match_proxy.end(group_name)
        if before:
            yield SplitNotAMatch(before)
        if match_elements:
            yield SplitMatch(
                _NamedGroupSplitterMatch(elements=match_elements, group_name=group_name)
            )

    if elements:
        yield SplitNotAMatch(elements)
