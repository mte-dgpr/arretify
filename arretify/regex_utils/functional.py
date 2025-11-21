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
from typing import Callable, Iterable, Iterator, Sequence, TypeVar, Union

from arretify.types import ProtectedTagOrStr

from .core import MatchFlow, MatchProxy
from .regex_tree.types import RegexTreeMatch, RegexTreeMatchFlow
from .types import GroupName

R = TypeVar("R")


def map_matches(
    elements: MatchFlow,
    map_func: Callable[[MatchProxy], R],
) -> Iterator[Union[str, R]]:
    for element in elements:
        if isinstance(element, str):
            yield element
        else:
            yield map_func(element)


def flat_map_regex_tree_match(
    regex_tree_match_flow: RegexTreeMatchFlow,
    map_func: Callable[[RegexTreeMatch], Iterable[ProtectedTagOrStr]],
    allowed_group_names: Sequence[GroupName] | None = None,
) -> Iterator[ProtectedTagOrStr]:
    for mapped in _map_regex_tree_match_generic(
        regex_tree_match_flow,
        map_func,
        allowed_group_names,
    ):
        if isinstance(mapped, Iterable):
            yield from mapped
        else:
            yield mapped


def map_regex_tree_match(
    regex_tree_match_flow: RegexTreeMatchFlow,
    map_func: Callable[[RegexTreeMatch], ProtectedTagOrStr],
    allowed_group_names: Sequence[GroupName] | None = None,
) -> Iterator[ProtectedTagOrStr]:
    return _map_regex_tree_match_generic(
        regex_tree_match_flow,
        map_func,
        allowed_group_names,
    )


def _map_regex_tree_match_generic(
    regex_tree_match_flow: RegexTreeMatchFlow,
    map_func: Callable[[RegexTreeMatch], R],
    allowed_group_names: Sequence[GroupName] | None = None,
) -> Iterator[R | ProtectedTagOrStr]:
    for str_or_group in regex_tree_match_flow:
        if isinstance(str_or_group, RegexTreeMatch):
            if (
                allowed_group_names is not None
                and str_or_group.group_name not in allowed_group_names
            ):
                raise ValueError(
                    f"received unexpected group named {str_or_group.group_name}. "
                    f"Allowed : {allowed_group_names}"
                )
            yield map_func(str_or_group)
        else:
            yield str_or_group


def iter_regex_tree_match_page_elements_or_strings(
    match: RegexTreeMatch,
) -> Iterator[ProtectedTagOrStr]:
    """
    Iterates over the strings in a regex tree match by traversing the whole tree.

    >>> match = RegexTreeMatch(
    ...     children=["hello", RegexTreeMatch(children=["world", "!"], group_name=None, match_dict={}), "python"],
    ...     group_name=None,
    ...     match_dict={}
    ... )
    >>> list(iter_regex_tree_match_page_elements_or_strings(match))
    ['hello', 'world', '!', 'python']
    """  # noqa: E501
    for child in match.children:
        if isinstance(child, RegexTreeMatch):
            yield from iter_regex_tree_match_page_elements_or_strings(child)
        else:
            yield child


def filter_regex_tree_match_children(
    match: RegexTreeMatch,
    group_names: Sequence[GroupName],
) -> list[RegexTreeMatch]:
    """
    Filters the children of a regex tree match by group names.

    >>> match = RegexTreeMatch(
    ...     children=[
    ...         RegexTreeMatch(children=[], group_name="g1", match_dict={}),
    ...         RegexTreeMatch(children=[], group_name="g2", match_dict={}),
    ...     ],
    ...     group_name=None,
    ...     match_dict={}
    ... )
    >>> filter_regex_tree_match_children(match, ["g1"])
    [RegexTreeMatch(children=[], group_name='g1', match_dict={})]
    """
    return [
        child
        for child in match.children
        if isinstance(child, RegexTreeMatch) and child.group_name in group_names
    ]
