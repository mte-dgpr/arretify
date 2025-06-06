#
# Copyright (c) 2025 Direction générale de la prévention des risques (DGPR).
#
# This file is part of Arrêtify.
# See https://github.com/mte-dgpr/arretify for further info.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from typing import List, Iterator, Dict, Iterable

from bs4 import BeautifulSoup

from arretify.regex_utils import (
    regex_tree,
    split_string_with_regex_tree,
    flat_map_regex_tree_match,
    map_regex_tree_match,
    iter_regex_tree_match_strings,
    filter_regex_tree_match_children,
)
from arretify.utils.html import (
    make_data_tag,
    make_new_tag,
    render_str_list_attribute,
    render_bool_attribute,
)
from arretify.html_schemas import OPERATION_SCHEMA
from arretify.types import (
    OperationType,
    PageElementOrString,
    DocumentContext,
)
from arretify.utils.functional import flat_map_string


OPERATION_TYPES_GROUP_NAMES = [
    OperationType.ADD.value,
    OperationType.DELETE.value,
    OperationType.REPLACE.value,
]

# Operation `target(1) operation description(2) operand(3, optional)`
# Example:
# les dispositions de l'article 8.1.1.1 l'arrêté du 12 mai 2016(1) sont complétées
# par les dispositions suivantes :(2)
# Un contrôle trimestriel de l'alarme en point bas des lignes de zingage et des
# lignes époxy est mis en place par l'exploitant.(3)
#
# This regex detects the part (2) of the operation.
RTL_OPERATION_NODE = regex_tree.Group(
    regex_tree.Sequence(
        [
            # Ignore the match if a paragraph break appears left of the operation
            r"^.*",
            regex_tree.Branching(
                [
                    r"est\sainsi\s",
                    r"sont\sainsi\s",
                    r"est\s",
                    r"sont\s",
                ]
            ),
            regex_tree.Branching(
                [
                    regex_tree.Group(
                        regex_tree.Branching(
                            [
                                r"complétée?s?(?:\s+(ainsi\s*[:]?|comme\s+suit[\s:]?))?",
                                r"complétée?s?",
                                r"créée?s?",
                                r"insérée?s?",
                                r"modifiée?s?\s+par\s+l'ajout",
                                r"ajouté\s+un\s+paragraphe\s+rédigé\s+ainsi",
                                r"ajoutée?s?",
                            ]
                        ),
                        group_name=OperationType.ADD.value,
                    ),
                    regex_tree.Group(
                        regex_tree.Branching(
                            [
                                r"substituée?s?",
                                r"supprimée?s?\s+et\s+remplacée?s?",
                                r"annulée?s?\s+et\s+remplacée?s?",
                                r"abrogée?s?\s+et\s+remplacée?s?",
                                r"modifiée?s?\s+et\s+remplacée?s?",
                                r"modifiée?s?\s+ou\s+supprimée?s?\s+et\s+remplacée?s?",
                                r"modifiée?s?",
                                r"remplacée?s?",
                            ]
                        ),
                        group_name=OperationType.REPLACE.value,
                    ),
                    regex_tree.Group(
                        regex_tree.Branching(
                            [
                                r"abrogée?s?",
                                r"supprimée?s?",
                                r"annulée?s?",
                            ]
                        ),
                        group_name=OperationType.DELETE.value,
                    ),
                ]
            ),
            # When the string is not ended by a period (.), we consider that
            # there is a right operand.
            regex_tree.Repeat(
                regex_tree.Group(
                    r"[^\.]*$",
                    group_name="__has_operand",
                ),
                quantifier=(0, ...),
            ),
        ]
    ),
    group_name="__operation",
)


def parse_operations(
    document_context: DocumentContext,
    children: Iterable[PageElementOrString],
) -> List[PageElementOrString]:
    return list(
        flat_map_string(
            children,
            lambda string: map_regex_tree_match(
                split_string_with_regex_tree(RTL_OPERATION_NODE, string),
                lambda operation_match: make_data_tag(
                    document_context.soup,
                    OPERATION_SCHEMA,
                    contents=flat_map_regex_tree_match(
                        operation_match.children,
                        lambda group_match: _render_group_match(document_context.soup, group_match),
                        allowed_group_names=[
                            "__has_operand",
                            *OPERATION_TYPES_GROUP_NAMES,
                        ],
                    ),
                    data=dict(
                        **_extract_operation_data(operation_match),
                        references=render_str_list_attribute([]),
                        direction="rtl",
                        operand="",
                    ),
                ),
            ),
        )
    )


def _render_group_match(
    soup: BeautifulSoup, group_match: regex_tree.Match
) -> Iterator[PageElementOrString]:
    if group_match.group_name == "__has_operand":
        yield from iter_regex_tree_match_strings(group_match)
    elif group_match.group_name in OPERATION_TYPES_GROUP_NAMES:
        yield make_new_tag(
            soup,
            "b",
            contents=iter_regex_tree_match_strings(group_match),
        )
    else:
        raise RuntimeError(f"Unexpected group name {group_match.group_name}")


def _extract_operation_data(
    operation_match: regex_tree.Match,
) -> Dict[str, str | None]:
    operation_type_groups = filter_regex_tree_match_children(
        operation_match,
        OPERATION_TYPES_GROUP_NAMES,
    )
    if len(operation_type_groups) != 1:
        raise RuntimeError("Expected exactly one operation type group")
    operation_type_group = operation_type_groups[0]

    has_operand = len(filter_regex_tree_match_children(operation_match, ["__has_operand"])) > 0

    return dict(
        operation_type=operation_type_group.group_name,
        keyword="".join(iter_regex_tree_match_strings(operation_type_group)),
        has_operand=render_bool_attribute(has_operand),
    )
