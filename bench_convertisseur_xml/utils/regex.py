import re
from typing import List, Pattern, cast, List, Callable, Iterable, Union, Dict, Tuple, Literal
from dataclasses import dataclass

from bench_convertisseur_xml.types import PageElementOrString
from .generators import remove_empty_strings_from_flow


StrOrMatch = str | re.Match
StrSplit = Tuple[str, re.Match, str]
MatchFlow = Iterable[StrOrMatch]


@dataclass
class MatchNamedGroup:
    name: str
    text: str


def split_match_by_named_groups(
    match: re.Match,
) -> Iterable[str | MatchNamedGroup]:
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


@remove_empty_strings_from_flow
def split_string(
    pattern: Pattern, 
    string: str,
) -> MatchFlow:
    previous_match: re.Match | None = None
    for match in pattern.finditer(string):
        if previous_match:
            yield string[previous_match.end():match.start()]
        else:
            yield string[:match.start()]
        yield match
        previous_match = match
    
    if previous_match:
        yield string[previous_match.end():]
    else:
        yield string


def split_string_at_beginning(    
    pattern: Pattern, 
    string: str,
) -> StrSplit | None:
    match = pattern.search(string)
    if not match:
        return None
    return (string[:match.start()], match, string[match.end():])


def split_string_at_end(
    pattern: Pattern, 
    string: str,
) -> StrSplit | None:
    results = list(split_string(pattern, string))

    # Find the last Match instance
    match_index = -1
    while (match_index * -1) <= len(results) and not isinstance(results[match_index], re.Match):
        match_index -= 1
    if (match_index * -1) > len(results):
        return None

    match = cast(re.Match, results[match_index])
    return (
        string[:match.start()],
        match,
        string[match.end():],
    )


@remove_empty_strings_from_flow
def merge_match_flow(
    str_or_match_gen: MatchFlow,
    after_or_before: Literal[-1, 1] = 1,
) -> Iterable[str]:
    accumulator = ''
    for str_or_match in str_or_match_gen:
        if isinstance(str_or_match, str):
            accumulator += str_or_match
        elif after_or_before == -1:
            yield accumulator + str_or_match.group(0)
            accumulator = ''
        else:
            yield accumulator
            accumulator = str_or_match.group(0)
    yield accumulator


# TODO : move somewhere else (maybe in a new file split.py)
def merge_strings(
    str_or_element_gen: Iterable[PageElementOrString],
) -> Iterable[PageElementOrString]:
    accumulator: str | None = None
    for str_or_element in str_or_element_gen:
        if isinstance(str_or_element, str):
            accumulator = (accumulator or '') + str_or_element
        else:
            if not accumulator is None:
                yield accumulator
            accumulator = None
            yield str_or_element
    if not accumulator is None:
        yield accumulator


NAMED_GROUP_RE = re.compile(r'\?P\<\w+\>')


def without_named_groups(pattern_string: str):
    return NAMED_GROUP_RE.sub('', pattern_string)
