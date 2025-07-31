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
from typing import List, Iterable, Iterator

from arretify.utils.functional import iter_func_to_list
from arretify.utils.html import is_tag_and_matches
from arretify.utils.split_merge import Probe, make_while_splitter
from arretify.types import PageElementOrString


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


group_strings_and_inline_tags_splitter = make_while_splitter(
    pick_string(lambda elements, index: True),
    pick_if_inline_tag_followed_by_match(pick_string(lambda elements, index: True)),
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
