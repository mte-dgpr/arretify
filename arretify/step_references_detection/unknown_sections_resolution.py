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

from typing import List
from dataclasses import replace as dataclass_replace

from bs4 import Tag

from arretify.types import DocumentContext
from arretify.law_data.types import SectionType
from arretify.utils.references import (
    build_and_traverse_reference_tree,
    ReferenceTreeTraversal,
)
from arretify.utils.html import set_data_attributes
from arretify.html_schemas import DOCUMENT_REFERENCE_SCHEMA, SECTION_REFERENCE_SCHEMA


def resolve_unknown_sections(
    document_context: DocumentContext,
) -> DocumentContext:
    processed: List[Tag] = []
    for reference_tag in document_context.soup.select(
        f".{DOCUMENT_REFERENCE_SCHEMA.css_class}, .{SECTION_REFERENCE_SCHEMA.css_class}"
    ):
        if reference_tag in processed:
            # Skip already processed tags
            continue

        reference_tree_traversal = list(build_and_traverse_reference_tree(reference_tag))
        resolve_unknown_sections_in_tree(
            document_context,
            reference_tree_traversal,
        )
        processed.extend((tag for tag, _, __ in reference_tree_traversal))

    return document_context


def resolve_unknown_sections_in_tree(
    document_context: DocumentContext,
    reference_tree_traversal: ReferenceTreeTraversal,
) -> None:
    for reference_tag, document, sections in reference_tree_traversal:
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
                current_section = dataclass_replace(
                    current_section,
                    type=SectionType.ALINEA,
                )

        # Current section is root or has a parent document
        else:
            if document is None:
                # If there is no document, we cannot resolve the section
                continue

            # When unknown is the sole section reference from a document,
            # it should be present in the document as a section title,
            # which means it is at least an article
            current_section = dataclass_replace(
                current_section,
                type=SectionType.ARTICLE,
            )

        set_data_attributes(
            reference_tag,
            current_section.get_data_attributes(),
        )
