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

from arretify.semantic_tag_specs import SectionReferenceSpec
from arretify.types import DocumentContext, ProtectedTagOrStr, SectionType
from arretify.utils.functional import iter_func_to_list
from arretify.utils.html_semantic import (
    get_semantic_tag_data,
    is_semantic_tag,
    set_semantic_tag_data,
    update_data,
)
from arretify.utils.references import ReferenceTree, build_reference_tree, traverse_reference_tree


def resolve_unknown_sections(
    _: DocumentContext,
    reference_tree: ReferenceTree,
) -> None:
    for reference_tag, document, sections in traverse_reference_tree(reference_tree):
        if not sections:
            # Current is not a section, so we skip it
            continue

        current_section = sections[-1]

        # Current section is not an unknown section, so we skip it
        if current_section.type != SectionType.UNKNOWN:
            continue

        # Current section has a parent section
        elif len(sections) > 1:
            parent_section = sections[-2]
            if parent_section.type == SectionType.UNKNOWN:
                # If the parent section is also unknown, we cannot resolve it
                continue

            # In the section type hierarchy, alineas represent the deepest
            # type just below articles
            if parent_section.type == SectionType.ARTICLE:
                current_section = update_data(current_section, type=SectionType.ALINEA)

        # Current section is root or has a parent document
        else:
            if document is None:
                # If there is no document, we cannot resolve the section
                continue

            # When unknown is the sole section reference from a document,
            # it should be present in the document as a section title,
            # which means it is at least an article
            current_section = update_data(current_section, type=SectionType.ARTICLE)

        set_semantic_tag_data(
            SectionReferenceSpec,
            reference_tag,
            current_section,
        )


@iter_func_to_list
def remove_misdetected_sections(
    _: DocumentContext,
    contents: Sequence[ProtectedTagOrStr],
) -> Iterator[ProtectedTagOrStr]:
    for section_reference_tag in contents:
        if not is_semantic_tag(section_reference_tag, spec_in=[SectionReferenceSpec]):
            yield section_reference_tag
            continue

        section_reference = get_semantic_tag_data(SectionReferenceSpec, section_reference_tag)
        if section_reference.type is SectionType.ANNEXE:
            reference_tree = build_reference_tree(section_reference_tag)
            # If section is an appendix, but with no detected number or id,
            # and that furthermore it is not connected to a chain of other
            # references (sections or documents), such as "en annexe du présent arrêté",
            # we can assume it is a misdetected section.
            if (
                section_reference.start_num is None
                and section_reference.start_id is None
                and len(reference_tree) == 1
                and len(reference_tree[0]) == 1
            ):
                yield from section_reference_tag.contents
                continue

        yield section_reference_tag
