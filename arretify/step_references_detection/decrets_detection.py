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
import logging
from typing import Optional, Sequence, cast

from arretify.parsing_utils.dates import DATE_NODE, render_date_regex_tree_match
from arretify.regex_utils import map_regex_tree_match, regex_tree
from arretify.semantic_tag_specs import DocumentReferenceData, DocumentReferenceSpec
from arretify.types import DocumentContext, DocumentType, ProtectedSoup, ProtectedTagOrStr
from arretify.utils.html import is_tag
from arretify.utils.html_create import make_semantic_tag
from arretify.utils.html_split_merge import make_regex_tree_splitter
from arretify.utils.split_merge import split_and_map_elements

_LOGGER = logging.getLogger(__name__)


# Examples :
# décret n°2005-635 du 30 mai 2005
DECRET_NODE = regex_tree.Group(
    regex_tree.Sequence(
        [
            r"décret\s+",
            r"(n\s*°\s*(?P<identifier>[\d\-]+)\s+)?",
            r"du\s+",
            DATE_NODE,
        ]
    ),
    group_name="__decret",
)


def parse_decrets_references(
    document_context: DocumentContext,
    contents: Sequence[ProtectedTagOrStr],
) -> list[ProtectedTagOrStr]:
    return split_and_map_elements(
        contents,
        make_regex_tree_splitter(DECRET_NODE),
        lambda decret_group_match: _render_decret_container(
            document_context.protected_soup, decret_group_match
        ),
    )


def _render_decret_container(
    soup: ProtectedSoup,
    decret_match: regex_tree.Match,
) -> ProtectedTagOrStr:
    # Parse date tag and extract date value
    decret_tag_contents = list(
        map_regex_tree_match(
            decret_match.children,
            lambda date_match: render_date_regex_tree_match(soup, date_match),
            allowed_group_names=[DATE_NODE.group_name],
        )
    )

    decret_date: Optional[str] = None
    for tag_or_str in decret_tag_contents:
        if is_tag(tag_or_str, tag_name_in=["time"]):
            decret_date = cast(str, tag_or_str["datetime"])
            break
    if decret_date is None:
        _LOGGER.warning(f"Could not find date for decret {decret_tag_contents}")

    return make_semantic_tag(
        soup,
        DocumentReferenceSpec,
        data=DocumentReferenceData(
            type=DocumentType.decret,
            date=decret_date,
            num=decret_match.match_dict.get("identifier", None),
        ),
        contents=decret_tag_contents,
    )
