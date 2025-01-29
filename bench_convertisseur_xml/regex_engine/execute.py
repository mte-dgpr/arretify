import re
from typing import Iterator, Dict, Callable, List, TypeVar, Iterable, Iterator
from dataclasses import dataclass

from .types import Node, MatchGroup, MatchDict, LeafNode, ContainerNode, QuantifierNode, GroupNode, MatchGroupFlow
from bench_convertisseur_xml.utils.split import split_string_with_regex, split_match_by_named_groups
from bench_convertisseur_xml.types import GroupName, PageElementOrString
from bench_convertisseur_xml.utils.functional import flat_map_non_string


P = TypeVar('P')


def split_string(node: GroupNode, string: str) -> MatchGroupFlow:
    for str_or_match in split_string_with_regex(node.pattern, string):
        if isinstance(str_or_match, str):
            yield str_or_match
            continue
        match_group = match(node, str_or_match.group(0))
        if not match_group:
            raise RuntimeError(f"expected '{string}' to match {node.pattern}")
        yield match_group    


def match(node: GroupNode, string: str) -> MatchGroup | None:
    results = list(_match_recursive(node, string, None))
    
    if len(results) == 0:
        return None
    elif len(results) > 1 or not isinstance(results[0], MatchGroup):
        raise RuntimeError(f"expected exactly one match group, got {results}")
    else:
        return results[0]


def _match_recursive(
    node: Node, 
    string: str,
    current_group: MatchGroup | None,
) -> MatchGroupFlow:
    match = node.pattern.match(string)
    if not match:
        return

    if isinstance(node, GroupNode):
        child_group = MatchGroup(
            children=[],
            group_name=node.group_name,
            match_dict=dict(),
        )
        child_group.children.extend(
            _match_recursive(node.child, string, child_group)
        )
        yield child_group
        return

    if not current_group:
        raise RuntimeError("current_group should not be None")

    if isinstance(node, LeafNode):
        current_group.match_dict.update(match.groupdict())
        yield match.group(0)
        return

    elif isinstance(node, QuantifierNode):
        for str_or_match in split_string_with_regex(node.child.pattern, match.group(0)):
            if isinstance(str_or_match, str):
                yield str_or_match
                continue
            yield from _match_recursive(
                node.child, str_or_match.group(0), current_group
            )

    else:
        for str_or_group in split_match_by_named_groups(match):
            if isinstance(str_or_group, str):
                yield str_or_group
                continue
            child = node.children[str_or_group.name]
            yield from _match_recursive(child, str_or_group.text, current_group)