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

from typing import Dict, Literal, Optional, Sequence, Union, cast

from arretify.parsing_utils.dates import DATE_NODE, render_date_regex_tree_match
from arretify.parsing_utils.patterns import ET_VIRGULE_PATTERN_S
from arretify.regex_utils import map_regex_tree_match, regex_tree
from arretify.semantic_tag_specs import DocumentReferenceData, DocumentReferenceSpec
from arretify.types import DocumentContext, DocumentType, ProtectedSoup, ProtectedTag
from arretify.utils.functional import chain_functions
from arretify.utils.html import ProtectedTagOrStr, is_tag
from arretify.utils.html_create import make_semantic_tag
from arretify.utils.html_split_merge import make_regex_tree_splitter
from arretify.utils.split_merge import (
    flat_map_splitted_elements,
    split_and_map_elements,
    split_elements,
)

Authority = Literal["préfectoral", "ministériel"]

Code = str

AUTHORITY_MAP: Dict[str, Authority] = {
    "ministériel": "ministériel",
    "préfectoral": "préfectoral",
    "ministériels": "ministériel",
    "préfectoraux": "préfectoral",
}


IDENTIFIER_NODE = regex_tree.Sequence(
    [
        regex_tree.Branching(
            [
                # Matches all codes starting with n°
                r"[nN]° ?(?P<identifier>\S+)",
                # Matches all codes of type 12-77LY87-7878 or 1L/77/9998
                r"(?P<identifier>\S+[/\-]\S+)",
            ]
        ),
        r"(?=\s|\.|$|,|\)|;)",
    ]
)


ARRETE_NODE = regex_tree.Group(
    regex_tree.Sequence(
        [
            (
                r"arrêté ((?P<authority>préfectoral|ministériel) (modifié )?)?"
                r"((?P<qualifier>complémentaire|d\'autorisation initiale?|d\'autorisation"
                r"|de mise en demeure|de mesures d\'urgence) )?"
            ),
            regex_tree.Branching(
                [
                    regex_tree.Sequence(
                        [
                            regex_tree.Repeat(
                                regex_tree.Sequence(
                                    [
                                        IDENTIFIER_NODE,
                                        r"\s",
                                    ]
                                ),
                                quantifier=(0, 1),
                            ),
                            r"(transmis a l\'exploitant par (courrier recommandé|courrier)\s)?",
                            regex_tree.Sequence(
                                [
                                    r"((du|en date du)\s)?",
                                    DATE_NODE,
                                ]
                            ),
                            # It's important to capture this in the arrete reference regex,
                            # so that we now it is not an action of modification, but rather
                            # part of the designation of the arrete.
                            r"(\s(modifié|modifiant)(?=\b))?",
                        ]
                    ),
                    IDENTIFIER_NODE,
                ]
            ),
        ]
    ),
    group_name="__arrete",
)


ARRETE_MULTIPLE_NODE = regex_tree.Group(
    regex_tree.Sequence(
        [
            r"arrêtés ((?P<authority>préfectoraux|ministériels) (modifiés )?)?",
            regex_tree.Repeat(
                regex_tree.Sequence(
                    [
                        regex_tree.Group(
                            regex_tree.Branching(
                                [
                                    # Regex with dates must come before cause the regex for codes
                                    # catches also dates.
                                    regex_tree.Sequence(
                                        [
                                            regex_tree.Repeat(
                                                regex_tree.Sequence(
                                                    [
                                                        IDENTIFIER_NODE,
                                                        r"\s",
                                                    ]
                                                ),
                                                quantifier=(0, 1),
                                            ),
                                            regex_tree.Sequence(
                                                [
                                                    r"((du|en date du)\s)?",
                                                    DATE_NODE,
                                                ]
                                            ),
                                            r"(\s(modifié|modifiant))?",
                                        ]
                                    ),
                                    IDENTIFIER_NODE,
                                ]
                            ),
                            group_name="__arrete",
                        ),
                        f"{ET_VIRGULE_PATTERN_S}?",
                    ]
                ),
                quantifier=(2, ...),
            ),
        ]
    ),
    group_name="__arrete_multiple",
)


def parse_arretes_references(
    document_context: DocumentContext,
    contents: Sequence[ProtectedTagOrStr],
) -> Sequence[ProtectedTagOrStr]:
    return chain_functions(
        document_context.protected_soup,
        contents,
        [
            # First check for multiple, cause it is the most exhaustive pattern
            _parse_multiple_arretes_references,
            _parse_arretes_references,
        ],
    )


def _extract_identifier(
    arrete_match: regex_tree.Match,
) -> Union[Code, None]:
    return arrete_match.match_dict.get("identifier", None)


def _render_arrete_container(
    soup: ProtectedSoup,
    arrete_match: regex_tree.Match,
    base_arrete_match: regex_tree.Match | None = None,
) -> ProtectedTag:
    if base_arrete_match is None:
        base_arrete_match = arrete_match

    # Parse date tag and extract date value
    arrete_tag_contents = list(
        map_regex_tree_match(
            arrete_match.children,
            lambda date_group_match: render_date_regex_tree_match(soup, date_group_match),
            allowed_group_names=[DATE_NODE.group_name],
        )
    )

    arrete_date: Optional[str] = None
    for tag_or_str in arrete_tag_contents:
        if is_tag(tag_or_str, tag_name_in=["time"]):
            arrete_date = cast(str, tag_or_str["datetime"])
            break

    # Build the arrete document object
    authority_raw = base_arrete_match.match_dict.get("authority")
    if authority_raw in ["ministériels", "ministériel"]:
        document_type = DocumentType.arrete_ministeriel
    elif authority_raw in ["préfectoraux", "préfectoral"]:
        document_type = DocumentType.arrete_prefectoral
    else:
        document_type = DocumentType.unknown_arrete

    # Render the arrete tag
    return make_semantic_tag(
        soup,
        DocumentReferenceSpec,
        data=DocumentReferenceData(
            type=document_type,
            num=_extract_identifier(arrete_match),
            date=arrete_date,
        ),
        contents=arrete_tag_contents,
    )


def _parse_arretes_references(
    soup: ProtectedSoup,
    contents: Sequence[ProtectedTagOrStr],
) -> Sequence[ProtectedTagOrStr]:
    return split_and_map_elements(
        contents,
        make_regex_tree_splitter(ARRETE_NODE),
        lambda match_tree: _render_arrete_container(
            soup,
            match_tree,
        ),
    )


def _parse_multiple_arretes_references(
    soup: ProtectedSoup,
    contents: Sequence[ProtectedTagOrStr],
) -> Sequence[ProtectedTagOrStr]:
    # For multiple arretes, we need to first parse some of the attributes in common
    # before parsing each individual arrete reference.
    return flat_map_splitted_elements(
        split_elements(
            contents,
            make_regex_tree_splitter(ARRETE_MULTIPLE_NODE),
        ),
        lambda match_tree: map_regex_tree_match(
            match_tree.children,
            lambda arrete_container_group_match: _render_arrete_container(
                soup,
                arrete_container_group_match,
                match_tree,
            ),
            allowed_group_names=["__arrete"],
        ),
    )
