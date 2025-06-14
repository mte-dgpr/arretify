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
from typing import Iterable, List, Optional, cast

from bs4 import BeautifulSoup, Tag

from arretify.regex_utils import (
    regex_tree,
    map_regex_tree_match,
    split_string_with_regex_tree,
)
from arretify.parsing_utils.dates import (
    DATE_NODE,
    render_date_regex_tree_match,
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
    children: Iterable[PageElementOrString],
) -> List[PageElementOrString]:
    return list(
        flat_map_string(
            children,
            lambda string: map_regex_tree_match(
                split_string_with_regex_tree(DECRET_NODE, string),
                lambda decret_match: _render_decret_container(
                    document_context.soup,
                    decret_match,
                ),
                allowed_group_names=["__decret"],
            ),
        )
    )


def _render_decret_container(
    soup: BeautifulSoup,
    decret_match: regex_tree.Match,
) -> PageElementOrString:
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
        if isinstance(tag_or_str, Tag) and tag_or_str.name == "time":
            decret_date = cast(str, tag_or_str["datetime"])
            break
    if decret_date is None:
        _LOGGER.warning(f"Could not find date for decret {decret_tag_contents}")

    document = Document(
        type=DocumentType.decret,
        date=decret_date,
        num=decret_match.match_dict.get("identifier", None),
    )

    return make_data_tag(
        soup,
        DOCUMENT_REFERENCE_SCHEMA,
        data=dict(
            uri=render_uri(document),
        ),
        contents=decret_tag_contents,
    )
