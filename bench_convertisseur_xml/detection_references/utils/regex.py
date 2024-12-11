import re
from typing import List, Pattern, cast, List, Callable, Iterator, Union, Dict, Tuple
from dataclasses import dataclass


@dataclass
class MatchNamedGroup:
    name: str
    text: str


def split_string_from_match(
    match: re.Match,
) -> Iterator[str | MatchNamedGroup]:
    match_text = match.group(0)
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
            yield MatchNamedGroup(text=match.group(group_name), name=group_name)
        max_group_end = max(group_end, max_group_end)

    # Add the remainder of the match_text to the parent.
    if max_group_end < len(match_text):
        yield match_text[max_group_end:]


def split_string_with_regex(
    regex: Pattern, 
    string: str,
) -> Iterator[str | re.Match]:
    remainder = str(string)
    while True:
        match = regex.search(remainder)
        if not match:
            yield remainder
            break
        
        match_start = match.start()
        match_end = match.end()
        
        if match_start > 0:
            yield remainder[:match_start]
        yield match
        remainder = remainder[match_end:]