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

from bs4 import Tag

from arretify.types import PageElementOrString, DocumentContext
from arretify.utils.element_ranges import (
    iter_collapsed_range_right,
)
from arretify.utils.html import (
    ensure_element_id,
    get_group_id,
    is_tag,
)
from arretify.html_schemas import (
    SECTION_REFERENCE_SCHEMA,
    DOCUMENT_REFERENCE_SCHEMA,
)
from arretify.regex_utils import regex_tree
from arretify.utils.split_merge import split_elements, map_splitted_elements
from arretify.utils.html_split_merge import group_strings_splitter
from arretify.utils.html import filter_out_inline_tags
from arretify.utils.strings import merge_strings


CONNECTOR_SECTION_TO_PARENT_NODE = regex_tree.Group(
    regex_tree.Sequence(
        [
            # Allows a maximum of 3 random words before the connector
            r"^(\s*[^.,;\s]+){0,3}\s*",
            regex_tree.Branching(
                [
                    r"du",
                    r"de\s+l\'",
                    r"de\s+la",
                    r"des",
                ]
            ),
            r"\s*$",
        ]
    ),
    group_name="__connector_section_to_parent",
)


def match_sections_to_parents(
    document_context: DocumentContext,
    children: Sequence[PageElementOrString],
) -> list[PageElementOrString]:
    document_context.soup
    children = list(children)
    section_references = [
        tag for tag in children if is_tag(tag, css_classes_in=[SECTION_REFERENCE_SCHEMA.css_class])
    ]

    for section_reference_tag in section_references:
        parent_reference_tag = _search_parent_reference_tag(section_reference_tag)
        if parent_reference_tag is None:
            continue

        group_id = get_group_id(section_reference_tag)
        if group_id is not None:
            section_references_in_group = [
                tag for tag in section_references if get_group_id(tag) == group_id
            ]
        else:
            section_references_in_group = [section_reference_tag]

        for section_reference_tag in section_references_in_group:
            document_element_id = ensure_element_id(
                document_context.id_counters, parent_reference_tag
            )
            section_reference_tag["data-parent_reference"] = document_element_id

    return children


def _search_parent_reference_tag(
    section_reference_tag: Tag,
) -> Tag | None:
    """
    For a given section reference tag, this function searches for its parent reference tag,
    by looking for connector words in between.

    For example, with :

        <a
            class="arretify-section_reference"
        >
            l'article 5
        </a>
        du
        <a
            class="arretify-section_reference"
        >
            présent arrêté
        </a>

    And given `<article 5>` as parameter, this function will return `<présent arrêté>`.
    """
    for element_range in iter_collapsed_range_right(section_reference_tag):
        # Make sure all elements in the range are contiguous.
        if element_range[-1].parent != section_reference_tag.parent:
            return None

        # Filter out inline tags, and generate combined strings
        element_range_with_merged_strings = map_splitted_elements(
            split_elements(
                filter_out_inline_tags(element_range),
                group_strings_splitter,
            ),
            lambda elements: merge_strings(
                elements,
            ),
        )

        # Grow the range until we get 3 elements :
        # <reference tag> <connector string> <parent reference tag>
        if len(element_range_with_merged_strings) == 3:
            parent_reference_tag = element_range_with_merged_strings[2]
            if not is_tag(
                parent_reference_tag,
                css_classes_in=[
                    DOCUMENT_REFERENCE_SCHEMA.css_class,
                    SECTION_REFERENCE_SCHEMA.css_class,
                ],
            ):
                return None

            connector_str = element_range_with_merged_strings[1]
            if not isinstance(connector_str, str) or not bool(
                CONNECTOR_SECTION_TO_PARENT_NODE.pattern.match(connector_str)
            ):
                return None

            return parent_reference_tag

        elif len(element_range_with_merged_strings) < 3:
            continue

        else:
            raise RuntimeError("Found more than 3 elements in the range, which is not expected")
    return None
