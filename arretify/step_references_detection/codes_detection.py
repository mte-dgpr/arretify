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

from bs4 import BeautifulSoup

from arretify.law_data.legifrance_constants import (
    get_code_titles,
)
from arretify.regex_utils import (
    regex_tree,
    map_regex_tree_match,
    split_string_with_regex_tree,
    iter_regex_tree_match_strings,
)
from arretify.regex_utils.helpers import (
    lookup_normalized_version,
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
from arretify.law_data.uri import (
    render_uri,
)


# TODO: Makes parsing very slow, because compiles into a big OR regex.
CODE_NODE = regex_tree.Group(
    regex_tree.Branching([f"(?P<title>{code})" for code in get_code_titles()]),
    group_name="__code",
)


def parse_codes_references(
    document_context: DocumentContext,
    children: Iterable[PageElementOrString],
) -> List[PageElementOrString]:
    return list(
        flat_map_string(
            children,
            lambda string: map_regex_tree_match(
                split_string_with_regex_tree(CODE_NODE, string),
                lambda code_group_match: _render_code_reference(
                    document_context.soup,
                    code_group_match,
                ),
                allowed_group_names=["__code"],
            ),
        )
    )


def _render_code_reference(
    soup: BeautifulSoup,
    code_group_match: regex_tree.Match,
) -> PageElementOrString:
    title = lookup_normalized_version(get_code_titles(), code_group_match.match_dict["title"])
    document = Document(
        type=DocumentType.code,
        title=title,
    )

    if document.title is None:
        raise ValueError("Could not find code title")

    code_reference_tag = make_data_tag(
        soup,
        DOCUMENT_REFERENCE_SCHEMA,
        data=dict(
            uri=render_uri(document),
        ),
        contents=iter_regex_tree_match_strings(code_group_match),
    )
    return code_reference_tag
