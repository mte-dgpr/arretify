from typing import Callable, Iterable, Iterator, List

from .types import MatchGroup, MatchGroupFlow
from bench_convertisseur_xml.types import GroupName, PageElementOrString


def flat_map_match_group(
    match_group_flow: MatchGroupFlow,
    map_func: Callable[[MatchGroup], Iterable[PageElementOrString]],
    allowed_group_names: List[GroupName] | None = None,
) -> Iterator[PageElementOrString]:
    for str_or_group in match_group_flow:
        if isinstance(str_or_group, str):
            yield str_or_group
        else:
            if allowed_group_names is not None and str_or_group.group_name not in allowed_group_names:
                raise ValueError(f"received unexpected group named {str_or_group.group_name}. Allowed : {allowed_group_names}")
            yield from map_func(str_or_group)
