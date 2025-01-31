from typing import Callable, Iterable, Iterator, List

from .types import RegexTreeMatch, RegexTreeMatchFlow, GroupName
from bench_convertisseur_xml.types import PageElementOrString


def flat_map_regex_tree_match(
    regex_tree_match_flow: RegexTreeMatchFlow,
    map_func: Callable[[RegexTreeMatch], Iterable[PageElementOrString]],
    allowed_group_names: List[GroupName] | None = None,
) -> Iterator[PageElementOrString]:
    for str_or_group in regex_tree_match_flow:
        if isinstance(str_or_group, str):
            yield str_or_group
        else:
            if allowed_group_names is not None and str_or_group.group_name not in allowed_group_names:
                raise ValueError(f"received unexpected group named {str_or_group.group_name}. Allowed : {allowed_group_names}")
            yield from map_func(str_or_group)
