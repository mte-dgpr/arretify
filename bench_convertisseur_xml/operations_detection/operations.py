import re
from typing import List, Pattern, Tuple, cast, Iterator, Dict, Iterable
from dataclasses import dataclass

from bs4 import BeautifulSoup, Tag, PageElement

from bench_convertisseur_xml.regex_utils import (
    PatternProxy, Settings, regex_tree, split_string_with_regex_tree, 
    flat_map_regex_tree_match, iter_regex_tree_match_strings, filter_regex_tree_match_children
)
from bench_convertisseur_xml.utils.html import make_data_tag, make_new_tag
from bench_convertisseur_xml.html_schemas import OPERATION_SCHEMA
from bench_convertisseur_xml.types import OperationType, PageElementOrString
from bench_convertisseur_xml.utils.functional import flat_map_string

OPERATION_TYPES_GROUP_NAMES = [
    OperationType.ADD.value, 
    OperationType.DELETE.value, 
    OperationType.REPLACE.value,
]


# Operation `target(1) operation description(2) operand(3, optional)`
# Example: 
# les dispositions de l'article 8.1.1.1 l'arrêté du 12 mai 2016(1) sont complétées par les dispositions suivantes :(2)
# Un contrôle trimestriel de l'alarme en point bas des lignes de zingage et des lignes époxy est mis en place par l'exploitant.(3)
# 
# This regex detects the part (2) of the operation.
RTL_OPERATION_NODE = regex_tree.Group(
    regex_tree.Sequence([
        # If there is a sentence end left of the operation, 
        # it means there is no (1), therefore we reject the match.
        r'^[^.]*',
        regex_tree.Branching([
            r'est( \w+)? ',
            r'sont( \w+)? ',
        ]),
        regex_tree.Branching([
            regex_tree.Group(
                regex_tree.Branching([
                    r'complétée?s?',
                ]),
                group_name=OperationType.ADD.value,
            ),
            regex_tree.Group(
                regex_tree.Branching([
                    r'abrogée?s?',
                    r'supprimée?s?',
                ]),
                group_name=OperationType.DELETE.value,
            ),
            regex_tree.Group(
                regex_tree.Branching([
                    r'modifiée?s?',
                    r'remplacée?s?',
                    r'mise?s? à jour',
                ]),
                group_name=OperationType.REPLACE.value,
            ),
        ]),
        # When the string is not ended by a period (.), we consider that 
        # there is a right operand.
        regex_tree.Quantifier(regex_tree.Group(
            r'[^\.]*$',
            group_name='__has_right_operand',
        ), quantifier='*'),
    ]),
    group_name='__operation',
)


def parse_operations(
    soup: BeautifulSoup, 
    children: Iterable[PageElementOrString],
) -> List[PageElementOrString]:
    return list(flat_map_string(
        children, 
        lambda string: flat_map_regex_tree_match(
            split_string_with_regex_tree(RTL_OPERATION_NODE, string),
            lambda operation_match: [
                make_data_tag(
                    soup, 
                    OPERATION_SCHEMA, 
                    contents=flat_map_regex_tree_match(
                        operation_match.children,
                        lambda group_match: _render_group_match(soup, group_match),
                        allowed_group_names=['__has_right_operand', *OPERATION_TYPES_GROUP_NAMES],
                    ),
                    data=_extract_operation_data(operation_match),
                )
            ]
        )
    ))


def _render_group_match(soup: BeautifulSoup, group_match: regex_tree.Match) -> Iterator[PageElementOrString]:
    if group_match.group_name == '__has_right_operand':
        yield from iter_regex_tree_match_strings(group_match)
    elif group_match.group_name in OPERATION_TYPES_GROUP_NAMES:
        yield make_new_tag(soup, 'b', contents=iter_regex_tree_match_strings(group_match))
    else:
        raise RuntimeError(f"Unexpected group name {group_match.group_name}")


def _extract_operation_data(operation_match: regex_tree.Match) -> Dict[str, str | None]:
    match_dict = operation_match.match_dict
    operation_type_groups = filter_regex_tree_match_children(
        operation_match, 
        OPERATION_TYPES_GROUP_NAMES,
    )
    if len(operation_type_groups) != 1:
        raise RuntimeError("Expected exactly one operation type group")
    operation_type_group = operation_type_groups[0]

    has_right_operand = None
    if len(filter_regex_tree_match_children(operation_match, ["__has_right_operand"])):
        has_right_operand = 'true'

    return dict(
        operation_type=operation_type_group.group_name,
        keyword=''.join(iter_regex_tree_match_strings(operation_type_group)),
        has_right_operand=has_right_operand,
    )