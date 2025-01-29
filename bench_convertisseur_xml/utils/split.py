import re
from typing import List, Pattern, cast, List, Callable, Iterable, Iterator, Union, Dict, Tuple, Literal, TypeVar
from dataclasses import dataclass

from bench_convertisseur_xml.types import PageElementOrString
from .generators import remove_empty_strings_from_flow

StrOrMatch = str | re.Match
StrSplit = Tuple[str, re.Match, str]
MatchFlow = Iterable[StrOrMatch]


T = TypeVar('T')


@dataclass
class MatchNamedGroup:
    name: str
    text: str


def split_match_by_named_groups(
    match: re.Match,
) -> Iterator[str | MatchNamedGroup]:
    '''
    Example:
        >>> pattern = r'(?P<first>\w+)-(?P<second>\w+)'
        >>> text = 'foo-bar'
        >>> match = re.search(pattern, text)
        >>> for segment in split_match_by_named_groups(match):
        ...     print(segment)
        MatchNamedGroup(text='foo', name='first')
        '-'
        MatchNamedGroup(text='bar', name='second')    
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
            yield MatchNamedGroup(text=match.group(group_name), name=group_name)
        max_group_end = max(group_end, max_group_end)

    # Add the remainder of the match_text to the parent.
    if max_group_end < len(match_text):
        yield match_text[max_group_end:]


@remove_empty_strings_from_flow
def split_string_with_regex(
    pattern: Pattern, 
    string: str,
) -> MatchFlow:
    '''
    Example:
        >>> pattern = re.compile(r'\d+')  # Matches sequences of digits
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


def split_string_with_regex_at_beginning(
    pattern: Pattern, 
    string: str,
) -> StrSplit | None:
    '''
    Like `split_string_with_regex`, but splits only once at the first match.
    '''
    match = pattern.search(string)
    if not match:
        return None
    return (string[:match.start()], match, string[match.end():])


def split_string_with_regex_at_end(
    pattern: Pattern, 
    string: str,
) -> StrSplit | None:
    '''
    Like `split_string_with_regex`, but splits only once at the last match.
    '''
    results = list(split_string_with_regex(pattern, string))

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


def reduce_children(
    children: Iterable[PageElementOrString],
    elements: List[T],
    reducer: Callable[[Iterable[PageElementOrString], T], Iterable[PageElementOrString]]
) -> List[PageElementOrString]:
    '''
        Example:
        >>> def simple_reducer(children, element):
        ...     return list(children) + [element]
        >>> reduce_children([], ["Item1", "Item2"], simple_reducer)
        ['Item1', 'Item2']
    '''
    new_children: List[PageElementOrString] = list(children)
    for element in elements:
        new_children = list(reducer(new_children, element))
    return new_children


@remove_empty_strings_from_flow
def merge_matches_with_siblings(
    str_or_match_gen: MatchFlow,
    which_sibling: Literal['previous', 'following'],
) -> Iterator[str]:
    '''
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
    '''
    accumulator = ''
    for str_or_match in str_or_match_gen:
        if isinstance(str_or_match, str):
            accumulator += str_or_match
        elif which_sibling == 'previous':
            yield accumulator + str_or_match.group(0)
            accumulator = ''
        else:
            yield accumulator
            accumulator = str_or_match.group(0)
    yield accumulator


def merge_strings(
    str_or_element_gen: Iterable[PageElementOrString],
) -> Iterator[PageElementOrString]:
    '''
    Example:
        >>> elements = ["Hello-", "world!", Tag(name="p"), "More text"]
        >>> list(merge_strings(elements))
        ['Hello-world!', <p></p>, 'More text']
    '''
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
