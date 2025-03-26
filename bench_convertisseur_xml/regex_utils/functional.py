from typing import Callable, Iterable, Iterator, List, TypeVar

from .types import GroupName
from .core import MatchFlow, MatchProxy
from .regex_tree.types import RegexTreeMatch, RegexTreeMatchFlow
from bench_convertisseur_xml.types import PageElementOrString


R = TypeVar('R')


def map_matches(
    elements: MatchFlow,
    map_func: Callable[[MatchProxy], PageElementOrString]
) -> Iterator[PageElementOrString]:
    for element in elements:
        if isinstance(element, str):
            yield element
        else:
            yield map_func(element)


def flat_map_regex_tree_match(
    regex_tree_match_flow: RegexTreeMatchFlow,
    map_func: Callable[[RegexTreeMatch], Iterable[PageElementOrString]],
    allowed_group_names: List[GroupName] | None = None,
) -> Iterator[PageElementOrString]:
    for mapped in _map_regex_tree_match_generic(
        regex_tree_match_flow,
        map_func,
        allowed_group_names,
    ):
        if isinstance(mapped, str):
            yield mapped
        else:
            yield from mapped


def map_regex_tree_match(
    regex_tree_match_flow: RegexTreeMatchFlow,
    map_func: Callable[[RegexTreeMatch], PageElementOrString],
    allowed_group_names: List[GroupName] | None = None,
) -> Iterator[PageElementOrString]:
    return _map_regex_tree_match_generic(
        regex_tree_match_flow,
        map_func,
        allowed_group_names,
    )


def _map_regex_tree_match_generic(
    regex_tree_match_flow: RegexTreeMatchFlow,
    map_func: Callable[[RegexTreeMatch], R],
    allowed_group_names: List[GroupName] | None = None,
) -> Iterator[R | str]:
    for str_or_group in regex_tree_match_flow:
        if isinstance(str_or_group, str):
            yield str_or_group
        else:
            if allowed_group_names is not None and str_or_group.group_name not in allowed_group_names:
                raise ValueError(f"received unexpected group named {str_or_group.group_name}. Allowed : {allowed_group_names}")
            yield map_func(str_or_group)



def iter_regex_tree_match_strings(match: RegexTreeMatch) -> Iterator[str]:
    """
    Iterates over the strings in a regex tree match by traversing the whole tree.

    >>> match = RegexTreeMatch(
    ...     children=["hello", RegexTreeMatch(children=["world", "!"], group_name=None, match_dict={}), "python"],
    ...     group_name=None,
    ...     match_dict={}
    ... )
    >>> list(iter_regex_tree_match_strings(match))
    ['hello', 'world', '!', 'python']
    """
    for child in match.children:
        if isinstance(child, str):
            yield child
        else:
            yield from iter_regex_tree_match_strings(child)


def filter_regex_tree_match_children(
    match: RegexTreeMatch,
    group_names: List[GroupName],
) -> List[RegexTreeMatch]:
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
        child for child in match.children 
        if isinstance(child, RegexTreeMatch) and child.group_name in group_names
    ]