from typing import Iterator, Literal, Iterable, cast

from bench_convertisseur_xml.types import PageElementOrString
from bench_convertisseur_xml.utils.generators import remove_empty_strings_from_flow
from .core import MatchFlow, safe_group


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
            yield accumulator + safe_group(str_or_match, 0)
            accumulator = ''
        else:
            yield accumulator
            accumulator = safe_group(str_or_match, 0)
    yield accumulator