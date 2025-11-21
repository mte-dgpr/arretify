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

from arretify.regex_utils import regex_tree
from arretify.semantic_tag_specs import DocumentReferenceSpec, SectionReferenceSpec
from arretify.types import DocumentContext, ProtectedTag, ProtectedTagOrStr, unprotect_page_element
from arretify.utils.html import ensure_tag_id, filter_out_inline_tags, get_group_id
from arretify.utils.html_element_ranges import iter_collapsed_range_right
from arretify.utils.html_semantic import is_semantic_tag, update_semantic_tag_data
from arretify.utils.html_split_merge import recombine_strings

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
    contents: Sequence[ProtectedTagOrStr],
) -> list[ProtectedTagOrStr]:
    document_context.protected_soup
    contents = list(contents)
    section_references = [
        tag for tag in contents if is_semantic_tag(tag, spec_in=[SectionReferenceSpec])
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
            update_semantic_tag_data(
                SectionReferenceSpec,
                section_reference_tag,
                parent_reference=ensure_tag_id(document_context.id_counters, parent_reference_tag),
            )

    return contents


def _search_parent_reference_tag(
    section_reference_tag: ProtectedTag,
) -> ProtectedTag | None:
    """
    For a given section reference tag, this function searches for its parent reference tag,
    by looking for connector words in between.

    For example, with :

        <a
            data-spec="section_reference"
        >
            l'article 5
        </a>
        du
        <a
            data-spec="section_reference"
        >
            présent arrêté
        </a>

    And given `<article 5>` as parameter, this function will return `<présent arrêté>`.
    """
    for element_range in iter_collapsed_range_right(section_reference_tag):
        # Make sure all elements in the range are contiguous.
        if (
            unprotect_page_element(element_range[-1]).parent
            != unprotect_page_element(section_reference_tag).parent
        ):
            return None

        # Filter out inline tags, and generate combined strings
        element_range_with_merged_strings = recombine_strings(filter_out_inline_tags(element_range))

        # Grow the range until we get 3 elements :
        # <reference tag> <connector string> <parent reference tag>
        if len(element_range_with_merged_strings) == 3:
            parent_reference_tag = element_range_with_merged_strings[2]
            if not is_semantic_tag(
                parent_reference_tag,
                spec_in=[
                    DocumentReferenceSpec,
                    SectionReferenceSpec,
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
