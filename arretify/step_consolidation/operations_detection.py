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
from typing import Iterator, Sequence

from arretify.parsing_utils.numbering import COUNT_PATTERN_S
from arretify.regex_utils import (
    filter_regex_tree_match_children,
    flat_map_regex_tree_match,
    iter_regex_tree_match_page_elements_or_strings,
    join_with_or,
    regex_tree,
)
from arretify.semantic_tag_specs import OperationData, OperationSpec
from arretify.types import (
    DocumentContext,
    OperationType,
    ProtectedSoup,
    ProtectedTag,
    ProtectedTagOrStr,
)
from arretify.utils.html_create import make_semantic_tag, make_tag
from arretify.utils.html_split_merge import make_regex_tree_splitter
from arretify.utils.split_merge import split_and_map_elements
from arretify.utils.strings import merge_strings

OPERATION_TYPES_GROUP_NAMES = [
    OperationType.ADD.value,
    OperationType.DELETE.value,
    OperationType.REPLACE.value,
]


SECTION_AFTER_OPERATION_L = r"(le|la|les|l')\s"
SECTION_AFTER_OPERATION_D = r"(de|du|des|d')\s"
SECTION_AFTER_OPERATION_A = r"(à|au|à l'|aux)\s"
SECTION_POSITION_EXPR = r"(au\sdébut|à\sla\sfin|à\sla\ssuite|au\sniveau)"

TERMS_VARIANTS_LIST = [
    r"termes?",
    r"phrases?",
    r"mots?",
    r"dispositions?(\ssuivantes?)?",
]
TERMS_VARIANTS = rf"{SECTION_AFTER_OPERATION_L}({join_with_or(TERMS_VARIANTS_LIST)})"

DISPOSITION_PATTERN_S = r"les dispositions suivantes"
EXPR_CONTINUATION_LIST = [
    r"suivant\sles\sdispositions",
    r"par\sles\s(suivantes|dispositions|prescriptions)",
    r"par\sce\squi\ssuit",
    r"comme\sprécisé",
    r"celles\sdéfinies\spar",
    r"par\scelles\s(inscrites|répertoriées)",
    r"ainsi\squ'il\ssuit",
    r"dans\sles\sconditions\s(suivantes|ci-après)",
    r"ainsi",
    r"par\sle\ssuivant",
    r"de\sla\s(façon|manière)\ssuivante",
    r"comme\ssui(t|vant)",
    r"comme\s(indiqué|précisé|ci-après)",
    rf"selon\s{SECTION_AFTER_OPERATION_L}",
]

EXPR_CONTINUATION = join_with_or(EXPR_CONTINUATION_LIST)


# Operation target(1) operation description(2) operand(3, optional)
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
            r"^.*",
            regex_tree.Branching(
                [
                    r"est\sainsi",
                    r"sont\sainsi",
                    r"est",
                    r"sont",
                ]
            ),
            r"\s",
            regex_tree.Branching(
                [
                    # ADD OPERATIONS
                    regex_tree.Sequence(
                        [
                            regex_tree.Group(
                                r"créée?s?",
                                group_name=OperationType.ADD.value,
                            ),
                            r"\s",
                            regex_tree.Branching(
                                [
                                    r"un\s(nouve(l|au)\s)?",
                                    rf"{COUNT_PATTERN_S}\s(nouveaux\s)?",
                                    rf"en fin\s{SECTION_AFTER_OPERATION_D}",
                                    SECTION_AFTER_OPERATION_A,
                                    DISPOSITION_PATTERN_S,
                                ]
                            ),
                        ]
                    ),
                    regex_tree.Sequence(
                        [
                            regex_tree.Group(
                                r"insérée?s?",
                                group_name=OperationType.ADD.value,
                            ),
                            r"(?!\saux?\srecueils?\sdes\sactes\sadministratifs)",
                            r"\s",
                            regex_tree.Branching(
                                [
                                    regex_tree.Sequence(
                                        [
                                            regex_tree.Branching([r"après", r"dans"]),
                                            r"\s",
                                            SECTION_AFTER_OPERATION_L,
                                        ]
                                    ),
                                    regex_tree.Sequence(
                                        [
                                            SECTION_POSITION_EXPR,
                                            r"\s",
                                            SECTION_AFTER_OPERATION_D,
                                        ]
                                    ),
                                    r"et\s(est|sont)\sainsi\srédigés?",
                                    r"le nouve(l|au)",
                                    rf"les\s{COUNT_PATTERN_S}",
                                    rf"{COUNT_PATTERN_S}\spoints?",
                                    rf"{SECTION_AFTER_OPERATION_A}",
                                    DISPOSITION_PATTERN_S,
                                ]
                            ),
                        ]
                    ),
                    regex_tree.Sequence(
                        [
                            regex_tree.Group(
                                r"complétée?s?",
                                group_name=OperationType.ADD.value,
                            ),
                            r"[,\s]+",
                            regex_tree.Branching(
                                [
                                    r"à\s(sa|la)\sfin",
                                    r"comme\ssuit",
                                    r"ainsi",
                                    r"par\s",
                                    r"d'",
                                ]
                            ),
                        ]
                    ),
                    regex_tree.Group(
                        regex_tree.Branching(
                            [
                                r"modifiée?s?\spar\sl'ajout",
                                r"ajoutée?s?",
                            ]
                        ),
                        group_name=OperationType.ADD.value,
                    ),
                    # REPLACE OPERATIONS
                    regex_tree.Group(
                        regex_tree.Branching(
                            [
                                # Table regex
                                r"modifiée?s?\sou\ssupprimée?s?\set\sremplacée?s?",
                                r"supprimée?s?,\smodifiée?s?\sou\sajoutée?s?",
                                r"modifiée?s?,\ssupprimée?s?\sou\scomplétée?s?",
                                r"modifiée?s?,\scomplétée?s?,?\sou\sannulée?s?",
                            ],
                        ),
                        group_name=OperationType.REPLACE.value,
                    ),
                    regex_tree.Group(
                        regex_tree.Branching(
                            [
                                # Simple regex
                                r"abrogée?s?\set\ssubstituée?s?",
                                r"supprimée?s?\set(\sest|\ssont)?\sremplacée?s?",
                                r"annulée?s?\set\sremplacée?s?",
                                r"abrogée?s?\s(et|ou)\sremplacée?s?",
                                r"modifiée?s?\set\s(remplacée?|complétée?)s?",
                                r"remplacée?s?\set\scomplétée?s?",
                                r"modifiée?s?\set\srédigée?s?",
                                r"modifiée?s?\s(et|ou)\ssupprimée?s?",
                            ],
                        ),
                        group_name=OperationType.REPLACE.value,
                    ),
                    regex_tree.Sequence(
                        [
                            regex_tree.Group(
                                r"substituée?s?",
                                group_name=OperationType.REPLACE.value,
                            ),
                            r"\s",
                            r"par",
                        ]
                    ),
                    regex_tree.Sequence(
                        [
                            regex_tree.Group(
                                r"remplacée?s?",
                                group_name=OperationType.REPLACE.value,
                            ),
                            r"\s",
                            regex_tree.Branching(
                                [
                                    regex_tree.Group(
                                        r":$",
                                        group_name="__has_operand",
                                    ),
                                    EXPR_CONTINUATION,
                                    rf"par\s{TERMS_VARIANTS}",
                                    rf"par\s{SECTION_AFTER_OPERATION_L}?",
                                ]
                            ),
                        ]
                    ),
                    regex_tree.Sequence(
                        [
                            regex_tree.Group(
                                r"modifiée?s?",
                                group_name=OperationType.REPLACE.value,
                            ),
                            r"\s",
                            regex_tree.Branching(
                                [
                                    regex_tree.Group(
                                        r":$",
                                        group_name="__has_operand",
                                    ),
                                    EXPR_CONTINUATION,
                                    rf"pour\s{SECTION_AFTER_OPERATION_L}",
                                    r"pour\s(ce\s)?qui\sconcerne",
                                    (
                                        rf"par\s:?celles?\s{SECTION_AFTER_OPERATION_D}?"
                                        rf"{SECTION_AFTER_OPERATION_L}?"
                                    ),
                                    rf"conformément\s{SECTION_AFTER_OPERATION_A}",
                                    rf"au\sniveau\s{SECTION_AFTER_OPERATION_D}",
                                    r"de\smanière\stemporaire",
                                ]
                            ),
                        ]
                    ),
                    regex_tree.Sequence(
                        [
                            regex_tree.Group(
                                r"mis(e|es)? a jour",
                                group_name=OperationType.REPLACE.value,
                            ),
                            r"\s",
                            regex_tree.Branching(
                                [
                                    r"de\sla\sfaçon\ssuivante",
                                ]
                            ),
                        ]
                    ),
                    # DELETE OPERATIONS
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
    contents: Sequence[ProtectedTagOrStr],
) -> list[ProtectedTagOrStr]:
    return split_and_map_elements(
        contents,
        make_regex_tree_splitter(RTL_OPERATION_NODE),
        lambda operation_match: _render_operation_match(
            document_context.protected_soup, operation_match
        ),
    )


def _render_operation_match(
    soup: ProtectedSoup,
    operation_match: regex_tree.Match,
) -> ProtectedTag:
    return make_semantic_tag(
        soup,
        OperationSpec,
        contents=flat_map_regex_tree_match(
            operation_match.children,
            lambda group_match: _render_group_match(soup, group_match),
            allowed_group_names=[
                "__has_operand",
                *OPERATION_TYPES_GROUP_NAMES,
            ],
        ),
        data=_extract_operation_data(operation_match),
    )


def _render_group_match(
    soup: ProtectedSoup, group_match: regex_tree.Match
) -> Iterator[ProtectedTagOrStr]:
    if group_match.group_name == "__has_operand":
        yield from iter_regex_tree_match_page_elements_or_strings(group_match)
    elif group_match.group_name in OPERATION_TYPES_GROUP_NAMES:
        yield make_tag(
            soup,
            "b",
            contents=iter_regex_tree_match_page_elements_or_strings(group_match),
        )
    else:
        raise RuntimeError(f"Unexpected group name {group_match.group_name}")


def _extract_operation_data(
    operation_match: regex_tree.Match,
) -> OperationData:
    operation_type_groups = filter_regex_tree_match_children(
        operation_match,
        OPERATION_TYPES_GROUP_NAMES,
    )
    if len(operation_type_groups) != 1:
        raise RuntimeError("Expected exactly one operation type group")
    operation_type_group = operation_type_groups[0]

    has_operand = len(filter_regex_tree_match_children(operation_match, ["__has_operand"])) > 0

    return OperationData(
        operation_type=operation_type_group.group_name,
        keyword=merge_strings(
            iter_regex_tree_match_page_elements_or_strings(operation_type_group),
            strip_other_types=True,
        ),
        has_operand=has_operand,
        references=None,
        direction="rtl",
        operand=None,
    )
