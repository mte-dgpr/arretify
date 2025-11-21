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
from typing import Callable, Generic, Iterable, Iterator, Sequence, Tuple, TypeVar

from arretify.utils.functional import iter_func_to_list

# -------------------- Generic splitting utils -------------------- #
# TODO : merge with other splitting utils voir #391

T1 = TypeVar("T1")
T2 = TypeVar("T2")
T3 = TypeVar("T3")

RawSplit = Tuple[list[T1], T2, list[T1]]
"""
Generic type alias representing a raw search & split operation on a list of elements.
It is subscribed like so `RawSplit[ElementType, MatchType]`
It represents a tuple `(before, match, after)` where:
- `before` is of type `list[ElementType]` and represents a
    list of elements before the match.
- `match` is of type `MatchType` and represents the matched element.
- `after` is of type `list[ElementType]` and represents a
    list of elements after the match.
"""

Splitter = Callable[[Sequence[T1]], RawSplit[T1, T2] | None]
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


SplittedElement = SplitNotAMatch[Sequence[T1]] | SplitMatch[T2]
"""
Generic type alias for an element in a splitted list.

It is subscribed like so `SplittedElement[ElementType, MatchType]`
It represents either:
- `SplitNotAMatch[Sequence[ElementType]]` which encapsulates a list of elements that did not match.
- `SplitMatch[MatchType]` which contains the matched element.

This is useful for processing a list of elements and tagging as matches or non-matches
in a generic manner. This enables proper typing and handling of the results like so :

```
if isinstance(splitted_element, SplitMatch):
    splitted_element.value  # This is of type MatchType
elif isinstance(splitted_element, SplitNotAMatch):
    splitted_element.value  # This is of type Sequence[ElementType]
```
"""

Probe = Callable[[Sequence[T1], int], bool]


@iter_func_to_list
def split_elements(
    elements: Sequence[T1],
    splitter: Splitter[T1, T2],
) -> Iterator[SplittedElement[T1, T2]]:
    """
    Split a list of elements using the provided splitter function.

    For example :

    >>> some_numbers = [1, 3, 11, 10, 6, 23]
    >>> def multiple_of_3(elements: Sequence[int]) -> RawSplit[int, int] | None:
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
    splitted_list: Sequence[SplittedElement[T1, T2]],
    map_func: Callable[[T2], T3],
) -> Iterator[T1 | T3]:
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
    splitted_list: Sequence[SplittedElement[T1, T2]],
    map_func: Callable[[T2], Iterable[T3]],
) -> Iterator[T1 | T3]:
    for splitted_element in splitted_list:
        if isinstance(splitted_element, SplitMatch):
            yield from map_func(splitted_element.value)
        else:
            yield from splitted_element.value


def split_and_map_elements(
    elements: Sequence[T1],
    splitter: Splitter[T1, T2],
    map_func: Callable[[T2], T3],
) -> list[T1 | T3]:
    """
    Convenience function that chains `split_elements` and `map_splitted_elements`.
    Splits the input list using the provided splitter,
    maps the matched elements using the provided map function,
    and returns a new list with the mapped elements.

    For example :

    >>> some_numbers = [1, 3, 11, 10, 6, 23]
    >>> def multiple_of_3(elements: Sequence[int]) -> RawSplit[int, int] | None:
    ...     for i, element in enumerate(elements):
    ...         if element % 3 == 0:
    ...             return elements[:i], element, elements[i + 1:]
    ...     return None
    >>> def map_func(n: int) -> str:
    ...     return f"Number {n} is multiple of 3"
    >>> split_and_map_elements(some_numbers, multiple_of_3, map_func)
    [1, 'Number 3 is multiple of 3', 11, 10, 'Number 6 is multiple of 3', 23]
    """  # noqa: E501
    return map_splitted_elements(split_elements(elements, splitter), map_func)


@iter_func_to_list
def merge_splitted_elements(
    splitted_list: Sequence[SplittedElement[T1, Sequence[T1]]],
) -> Iterator[T1]:
    """
    Flatten a list of SplittedElement.
    Works only if type of match and non match are the same.

    For example :

    >>> splitted_list = [
    ...     SplitNotAMatch([1, 2]),
    ...     SplitMatch([3, 4]),
    ...     SplitNotAMatch([5]),
    ... ]
    >>> list(merge_splitted_elements(splitted_list))
    [1, 2, 3, 4, 5]
    """

    for splitted_element in splitted_list:
        if isinstance(splitted_element, SplitMatch):
            yield from splitted_element.value
        elif isinstance(splitted_element, SplitNotAMatch):
            yield from splitted_element.value
        else:
            raise RuntimeError(
                "Unexpected type in splitted_list, expected SplitMatch or SplitNotAMatch"
            )


def split_before_match(
    elements: Sequence[T1],
    is_matching: Probe[T1],
) -> Tuple[list[T1], list[T1]]:
    """
    Split the input list into two parts, by using the `is_matching` function.

    Examples :

    strings = ["a", "b", "c"]
    >>> split_before_match(strings, lambda s: s == "b")
    (["a"], ["b", "c"])
    >>> split_before_match(strings, lambda s: s == "d") # No match
    (["a", "b", "c"], [])
    >>> split_before_match(strings, lambda s: s == "a")
    ([], ["a", "b", "c"])
    """
    i = 0
    while i < len(elements):
        if is_matching(elements, i):
            break
        i += 1
    return list(elements[:i]), list(elements[i:])


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

    def _splitter(elements: Sequence[T1]) -> RawSplit[T1, list[T1]] | None:
        before, after = split_before_match(elements, is_matching)
        if after:
            return (before, [after[0]], after[1:])
        return None

    return _splitter


def make_while_splitter(
    start_condition: Probe[T1],
    while_condition: Probe[T1],
) -> Splitter[T1, list[T1]]:
    """
    Starts the split at the first element matched by `start_condition`, and continues
    to match until the first element that does not match `while_condition`.

    For example :

    >>> strings = ["a", "b", "b", "c"]
    >>> splitter = make_while_splitter(lambda s, i: s == "b", lambda s, i: s == "b")
    >>> splitter(strings)
    (["a"], ["b", "b"], ["c"])
    """

    def _splitter(elements: Sequence[T1]) -> RawSplit[T1, list[T1]] | None:
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

    def _negated_probe(elements: Sequence[T1], index: int) -> bool:
        return not probe(elements, index)

    return _negated_probe
