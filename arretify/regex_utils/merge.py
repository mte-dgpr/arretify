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
from typing import Iterator, Literal

from arretify.utils.generators import remove_empty_strings_from_flow

from .core import MatchFlow, safe_group


@remove_empty_strings_from_flow
def merge_matches_with_siblings(
    str_or_match_gen: MatchFlow,
    which_sibling: Literal["previous", "following"],
) -> Iterator[str]:
    """
    Example:
        >>> def example_gen():
        ...     yield "Hello, "
        ...     yield re.match(r"world", "world!")
        ...     yield " How are you?"
        ...
        >>> list(merge_match_flow(example_gen(), which_sibling=1))
        ['Hello, ', 'world', ' How are you?']
        >>> list(merge_match_flow(example_gen(), which_sibling=-1))
        ['Hello, world', ' How are you?']
    """
    accumulator = ""
    for str_or_match in str_or_match_gen:
        if isinstance(str_or_match, str):
            accumulator += str_or_match
        elif which_sibling == "previous":
            yield accumulator + safe_group(str_or_match, 0)
            accumulator = ""
        else:
            yield accumulator
            accumulator = safe_group(str_or_match, 0)
    yield accumulator
