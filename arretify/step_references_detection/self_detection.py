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

from arretify.regex_utils import iter_regex_tree_match_page_elements_or_strings, regex_tree
from arretify.semantic_tag_specs import DocumentReferenceData, DocumentReferenceSpec
from arretify.types import DocumentContext, DocumentType, ProtectedTagOrStr
from arretify.utils.html_create import make_semantic_tag
from arretify.utils.html_split_merge import make_regex_tree_splitter
from arretify.utils.split_merge import split_and_map_elements

SELF_NODE = regex_tree.Group(
    regex_tree.Branching(
        [
            r"(le )?présent arrêté",
        ]
    ),
    group_name="__self",
)


def parse_self_references(
    document_context: DocumentContext,
    contents: Sequence[ProtectedTagOrStr],
) -> list[ProtectedTagOrStr]:
    return split_and_map_elements(
        contents,
        make_regex_tree_splitter(SELF_NODE),
        lambda self_group_match: make_semantic_tag(
            document_context.protected_soup,
            DocumentReferenceSpec,
            data=DocumentReferenceData(
                type=DocumentType.self,
            ),
            contents=iter_regex_tree_match_page_elements_or_strings(self_group_match),
        ),
    )
