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
from typing import Iterable, List


from arretify.regex_utils import (
    regex_tree,
    map_regex_tree_match,
    split_string_with_regex_tree,
    iter_regex_tree_match_strings,
)
from arretify.types import PageElementOrString, DocumentContext
from arretify.utils.functional import flat_map_string
from arretify.html_schemas import (
    DOCUMENT_REFERENCE_SCHEMA,
)
from arretify.utils.html import (
    make_data_tag,
)
from arretify.law_data.types import (
    Document,
    DocumentType,
)


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
    children: Iterable[PageElementOrString],
) -> List[PageElementOrString]:
    document = Document(type=DocumentType.self)
    return list(
        flat_map_string(
            children,
            lambda string: map_regex_tree_match(
                split_string_with_regex_tree(SELF_NODE, string),
                lambda self_group_match: make_data_tag(
                    document_context.soup,
                    DOCUMENT_REFERENCE_SCHEMA,
                    data=document.get_data_attributes(),
                    contents=iter_regex_tree_match_strings(self_group_match),
                ),
                allowed_group_names=["__self"],
            ),
        )
    )
