import re
from typing import List, Pattern, cast, List, Callable, Iterable, Iterator, Union, Dict, Tuple, Literal
from dataclasses import dataclass

from bench_convertisseur_xml.types import PageElementOrString
from bench_convertisseur_xml.utils.generators import remove_empty_strings_from_flow
from .types import MatchNamedGroup
from .core import MatchProxy, PatternProxy, MatchFlow


StrSplit = Tuple[str, MatchProxy, str]


def split_match_by_named_groups(
    match: MatchProxy,
) -> Iterator[str | MatchNamedGroup]:
    '''
    Example:
        >>> pattern = r'(?P<first>\w+)-(?P<second>\w+)'
        >>> text = 'foo-bar'
        >>> match = re.search(pattern, text)
        >>> for segment in split_match_by_named_groups(match):
        ...     print(segment)
        MatchNamedGroup(text='foo', group_name='first')
        '-'
        MatchNamedGroup(text='bar', group_name='second')    
    '''
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
            yield MatchNamedGroup(
                text=match.group(group_name), 
                group_name=group_name
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
    '''
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
    '''
    previous_match: MatchProxy | None = None
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