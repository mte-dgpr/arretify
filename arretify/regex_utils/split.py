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
from typing import Iterator, Tuple

from arretify.utils.generators import remove_empty_strings_from_flow

from .core import MatchFlow, MatchProxy, PatternProxy, safe_group
from .types import MatchNamedGroup

StrSplit = Tuple[str, MatchProxy, str]


def split_match_by_named_groups(
    match: MatchProxy,
) -> Iterator[str | MatchNamedGroup]:
    R"""
    Example:
        >>> pattern = r'(?P<first>\w+)-(?P<second>\w+)'
        >>> text = 'foo-bar'
        >>> match = re.search(pattern, text)
        >>> for segment in split_match_by_named_groups(match):
        ...     print(segment)
        MatchNamedGroup(text='foo', group_name='first')
        '-'
        MatchNamedGroup(text='bar', group_name='second')
    """
    match_text = safe_group(match, 0)
    # Offset in original text
    match_offset = match.start(0)
    match_dict = match.groupdict()

    # List all named groups and sort them by start index
    group_names = list(match_dict.keys())
    # Sorting seems to work fine if two groups have same start.
    # The containing group then is put before the nested group in the list,
    # Which is the desired behavior.
    group_names.sort(key=lambda n: match.start(n))
    max_group_end = 0
    for group_name in group_names:
        if not match.group(group_name):
            continue

        # Adjust named group start & end indices
        # with offset in original text.
        group_start = match.start(group_name) - match_offset
        group_end = match.end(group_name) - match_offset

        # Add new elements to the parent.
        # If current group is nested inside previous group, we skip.
        if group_start >= max_group_end:
            if group_start > max_group_end:
                yield match_text[max_group_end:group_start]
            yield MatchNamedGroup(
                text=safe_group(match, group_name),
                group_name=group_name,
            )
        max_group_end = max(group_end, max_group_end)

    # Add the remainder of the match_text to the parent.
    if max_group_end < len(match_text):
        yield match_text[max_group_end:]


@remove_empty_strings_from_flow
def split_string_with_regex(
    pattern: PatternProxy,
    string: str,
) -> MatchFlow:
    r"""
    Example:

        >>> pattern = PatternProxy(r'\d+')  # Matches sequences of digits
        >>> string = "abc123def456ghi"
        >>> result = list(split_string_with_regex(pattern, string))
        >>> for item in result:
        ...     if isinstance(item, str):
        ...         print(f"Substring: '{item}'")
        ...     else:
        ...         print(f"Match: '{item.group()}'")
        Substring: 'abc'
        Match: '123'
        Substring: 'def'
        Match: '456'
        Substring: 'ghi'
    """
    previous_match: MatchProxy | None = None
    for match in pattern.finditer(string):
        if previous_match:
            yield string[previous_match.end() : match.start()]
        else:
            yield string[: match.start()]
        yield match
        previous_match = match

    if previous_match:
        yield string[previous_match.end() :]
    else:
        yield string
