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
from dataclasses import dataclass
from dataclasses import replace as dataclass_replace
from typing import Iterator, Sequence, Tuple, TypeVar

from arretify.regex_utils import MatchProxy, PatternProxy, safe_group
from arretify.regex_utils.regex_tree.types import (
    BranchingNode,
    GroupName,
    GroupNode,
    LiteralNode,
    Node,
    RegexTreeMatch,
    RegexTreeMatchFlow,
    RepeatNode,
    SequenceNode,
)
from arretify.types import ProtectedTagOrStr
from arretify.utils.functional import iter_func_to_list
from arretify.utils.html import INLINE_TAG_TYPES, is_tag
from arretify.utils.split_merge import (
    Probe,
    RawSplit,
    SplitMatch,
    SplitNotAMatch,
    SplittedElement,
    Splitter,
    flat_map_splitted_elements,
    make_while_splitter,
    merge_splitted_elements,
    split_and_map_elements,
    split_elements,
)
from arretify.utils.strings import merge_strings

T = TypeVar("T")


# -------------------- Split / merge for html -------------------- #
def pick_if_inline_tag_followed_by_match(
    is_matching: Probe[ProtectedTagOrStr],
) -> Probe[ProtectedTagOrStr]:
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
    >>> def is_string(elements: Sequence[ProtectedTagOrStr], index: int) -> bool:
    ...     return isinstance(elements[index], str)
    >>> probe = pick_if_inline_tag_followed_by_match(is_string)
    >>> probe(elements, 0) # -> directly calls `is_string`
    True
    >>> probe(elements, 1) # -> calls `is_string` on the next element
    True
    >>> probe(elements, 3) # -> calls `is_string` on the next element
    False
    """

    def _pick_inline_tags_probe(elements: Sequence[ProtectedTagOrStr], index: int) -> bool:
        for next_index, next_element in enumerate(elements[index:], start=index):
            if is_tag(next_element, tag_name_in=INLINE_TAG_TYPES):
                continue
            else:
                return is_matching(elements, next_index)
        return False

    return _pick_inline_tags_probe


def pick_string(
    probe: Probe[ProtectedTagOrStr],
) -> Probe[ProtectedTagOrStr]:
    def _string_probe(elements: Sequence[ProtectedTagOrStr], index: int) -> bool:
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


group_strings_and_inline_tags_splitter: Splitter[ProtectedTagOrStr, Sequence[ProtectedTagOrStr]] = (
    make_while_splitter(
        pick_string(lambda elements, index: True),
        pick_if_inline_tag_followed_by_match(pick_string(lambda elements, index: True)),
    )
)
"""
Splitter to enable grouping of string elements and inline tags,
when these are preceded and followed by strings.
"""


def recombine_strings(contents: Sequence[ProtectedTagOrStr]) -> list[ProtectedTagOrStr]:
    """
    Groups and recombines consecutive string elements in `contents` into single string elements.
    """
    return split_and_map_elements(
        contents,
        group_strings_splitter,
        merge_strings,
    )


def make_regex_tree_splitter(
    node: GroupNode,
) -> Splitter[ProtectedTagOrStr, RegexTreeMatch]:
    """
    Splits a list of elements based on a regex tree node.
    """
    pattern_splitter = make_pattern_splitter_ignoring_inline_tags(node.pattern)

    def _splitter(
        elements: Sequence[ProtectedTagOrStr],
    ) -> RawSplit[ProtectedTagOrStr, RegexTreeMatch] | None:
        split = pattern_splitter(elements)
        if not split:
            return None
        before, match, after = split
        return (
            before,
            regex_tree_match(
                match.elements,
                node,
            ),
            after,
        )

    return _splitter


@dataclass(frozen=True)
class _PatternSplitterMatch:
    elements: Sequence[ProtectedTagOrStr]
    match_proxy: MatchProxy


def make_pattern_splitter_ignoring_inline_tags(
    pattern: PatternProxy,
) -> Splitter[ProtectedTagOrStr, _PatternSplitterMatch]:
    def _splitter(
        elements: Sequence[ProtectedTagOrStr],
    ) -> RawSplit[ProtectedTagOrStr, _PatternSplitterMatch] | None:
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
            before = merge_splitted_elements(grouped_strings[:i]) + before_match
            after = after_match + merge_splitted_elements(grouped_strings[i + 1 :])

            return (
                before,
                _PatternSplitterMatch(elements=match_elements, match_proxy=match_proxy),
                after,
            )
        return None

    return _splitter


def _trim_strings_before_merging(
    elements: Sequence[ProtectedTagOrStr],
) -> list[ProtectedTagOrStr]:
    """
    Trims spaces in string elements before and after an inline tag in order
    to avoid double spaces. Example:

    >>> _trim_strings_before_merging(["Hello ", <br/>, " World"])
    ["Hello", <br/>, " World"]
    """
    elements = list(elements)
    for i, element in enumerate(elements):
        if not is_tag(element, tag_name_in=INLINE_TAG_TYPES) or i == 0:
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


def _slice_elements_with_string_index(
    elements: Sequence[str | T], start: int, end: int
) -> RawSplit[str | T, list[str | T]]:
    """
    Takes a list and slices it based only on its string elements (`end` is exclusive).

    Example :

    >>> elements = ["Hello", <br/>, "World"]
    >>> _slice_elements_with_string_index(elements, 2, 7)
    (["He"], ["llo", "<br/>", "Wo"], ["rld"])
    """
    before_match, match_elements = _split_before_string_index(elements, start)
    # Remove tags at the start of match_elements, so the match doesn't start with a tag.
    while match_elements and not isinstance(match_elements[0], str):
        before_match.append(match_elements.pop(0))
    match_elements, after_match = _split_before_string_index(match_elements, end - start)
    return before_match, match_elements, after_match


def _split_before_string_index(
    elements: Sequence[str | T], split_index: int
) -> Tuple[list[str | T], list[str | T]]:
    current_index = 0
    for i, element in enumerate(elements):
        if not isinstance(element, str):
            continue
        current_index += len(element)
        if current_index < split_index:
            continue

        surplus = current_index - split_index
        if surplus == 0:
            string_before = element
            string_after = ""
        else:
            string_before = element[:-surplus]
            string_after = element[-surplus:]

        before = list(elements[:i]) + ([string_before] if string_before else [])
        after = ([string_after] if string_after else []) + list(elements[i + 1 :])
        return (before, after)
    return (list(elements), [])


# -------------------- Regex tree matching -------------------- #
class NoMatch(Exception):
    """
    Enables the algorithm to break out of the current branch and try the next one.
    """


@dataclass(frozen=True)
class _NamedGroupSplitterMatch:
    elements: Sequence[ProtectedTagOrStr]
    group_name: GroupName


def regex_tree_match(elements: Sequence[ProtectedTagOrStr], node: GroupNode) -> RegexTreeMatch:
    try:
        results = list(_regex_tree_match_recursive(elements, node, None))
    except NoMatch:
        raise ValueError("No match found for the provided regex tree node.")

    if len(results) != 1 or not isinstance(results[0], RegexTreeMatch):
        raise RuntimeError(f"expected exactly one match group, got {results}")
    else:
        return results[0]


def _regex_tree_match_recursive(
    elements: Sequence[ProtectedTagOrStr],
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
        yield dataclass_replace(
            child_group,
            children=list(_regex_tree_match_recursive(elements, node.child, child_group)),
        )
        return

    # For other nodes, there is no problem using `pattern`.
    split = make_pattern_splitter_ignoring_inline_tags(node.pattern)(elements)
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
                make_pattern_splitter_ignoring_inline_tags(node.child.pattern),
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


@iter_func_to_list
def _split_match_by_named_groups(
    match_proxy: MatchProxy,
    elements: Sequence[ProtectedTagOrStr],
) -> Iterator[SplittedElement[ProtectedTagOrStr, _NamedGroupSplitterMatch]]:
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
