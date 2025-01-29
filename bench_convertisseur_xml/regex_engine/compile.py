import enum
import re
from typing import List, Dict, TypedDict, Union
from dataclasses import dataclass, replace

from .types import QuantifierNode, GroupNode, ContainerNode, LeafNode, Node, NodeMap, Settings
from bench_convertisseur_xml.types import GroupName
from bench_convertisseur_xml.utils.regex import without_named_groups, join_with_or


def Leaf(pattern_string: str, settings: Settings | None=None) -> LeafNode:
    settings = settings or Settings()
    return LeafNode(
        id=_get_unique_id(),
        pattern=re.compile(
            pattern_string, 
            flags=_settings_to_flags(settings),
        ),
        settings=settings,
    )


def Branching(child_or_str_list: List[Node | str], settings: Settings | None=None) -> ContainerNode:
    settings = settings or Settings()
    children_list: List[Node] = []
    for child_or_str in child_or_str_list:
        children_list.append(_initialize_child(child_or_str, settings))

    return ContainerNode(
        id=_get_unique_id(),
        pattern=re.compile(
            join_with_or([
                f'(?P<{child.id}>{without_named_groups(child.pattern.pattern)})' 
                for child in children_list
            ]),
            flags=_settings_to_flags(settings),
        ),
        children={child.id: child for child in children_list},
        settings=settings,
    )


def Sequence(child_or_str_list: List[Node | str], settings: Settings | None=None) -> ContainerNode:
    settings = settings or Settings()
    pattern_string = ''
    children: NodeMap = {}
    child: Node
    for child_or_str in child_or_str_list:
        child = _initialize_child(child_or_str, settings)
        pattern_string += f'(?P<{child.id}>{without_named_groups(child.pattern.pattern)})'
        children[child.id] = child
    
    return ContainerNode(
        id=_get_unique_id(),
        pattern=re.compile(
            pattern_string,
            flags=_settings_to_flags(settings),
        ),
        children=children,
        settings=settings,
    )


def Group(
    child_or_str: Union[Node, str],
    group_name: GroupName,
    settings: Settings | None=None,
) -> GroupNode:
    settings = settings or Settings()
    child = _initialize_child(child_or_str, settings)
    return GroupNode(
        id=_get_unique_id(),
        group_name=group_name,
        pattern=re.compile(
            f'(?P<{child.id}>{without_named_groups(child.pattern.pattern)})',
            flags=_settings_to_flags(settings),
        ),
        child=child,
        settings=settings,
    )


def Quantifier(
    child_or_str: Union[Node, str],
    quantifier: str,
    settings: Settings | None=None,
) -> QuantifierNode:
    settings = settings or Settings()
    child = _initialize_child(child_or_str, settings)
    return QuantifierNode(
        id=_get_unique_id(),
        quantifier=quantifier,
        pattern=re.compile(
            f'({without_named_groups(child.pattern.pattern)}){quantifier}',
            flags=_settings_to_flags(settings),
        ),
        child=child,
        settings=settings,
    )


def _get_unique_id() -> str:
    global _COUNTER
    _COUNTER += 1
    return f'{_PREFIX}{_COUNTER}'
_COUNTER = 0
_PREFIX = '_ID_'


def _settings_to_flags(settings: Settings) -> int:
    return re.IGNORECASE if settings.ignore_case else 0


def _initialize_child(node_or_str: Node | str, default_settings: Settings) -> Node:
    # If child is a string, we create a leaf node from it.
    if isinstance(node_or_str, str):
        return Leaf(node_or_str, settings=default_settings)
    # If the child is already a node, we ensures that it has a unique id.
    # This allows using the same node in multiple places in the tree.
    else:
        return replace(node_or_str, id=_get_unique_id())