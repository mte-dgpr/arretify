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
from typing import Sequence

from arretify.law_data.legifrance_constants import get_code_titles
from arretify.regex_utils import iter_regex_tree_match_page_elements_or_strings, regex_tree
from arretify.regex_utils.helpers import lookup_normalized_version
from arretify.semantic_tag_specs import DocumentReferenceData, DocumentReferenceSpec
from arretify.types import DocumentContext, DocumentType, ProtectedSoup, ProtectedTagOrStr
from arretify.utils.html_create import make_semantic_tag
from arretify.utils.html_split_merge import make_regex_tree_splitter
from arretify.utils.split_merge import split_and_map_elements

# TODO: Makes parsing very slow, because compiles into a big OR regex.
CODE_NODE = regex_tree.Group(
    regex_tree.Branching([f"(?P<title>{code})" for code in get_code_titles()]),
    group_name="__code",
)


def parse_codes_references(
    document_context: DocumentContext,
    contents: Sequence[ProtectedTagOrStr],
) -> list[ProtectedTagOrStr]:
    return split_and_map_elements(
        contents,
        make_regex_tree_splitter(CODE_NODE),
        lambda code_group_match: _render_code_reference(
            document_context.protected_soup,
            code_group_match,
        ),
    )


def _render_code_reference(
    soup: ProtectedSoup,
    code_group_match: regex_tree.Match,
) -> ProtectedTagOrStr:
    return make_semantic_tag(
        soup,
        DocumentReferenceSpec,
        data=DocumentReferenceData(
            type=DocumentType.code,
            title=lookup_normalized_version(
                get_code_titles(), code_group_match.match_dict["title"]
            ),
        ),
        contents=iter_regex_tree_match_page_elements_or_strings(code_group_match),
    )
