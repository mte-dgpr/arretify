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

from arretify.semantic_tag_specs import (
    AlineaSpec,
    DocumentReferenceSpec,
    OperationSpec,
    SectionReferenceSpec,
)
from arretify.types import DocumentContext, ProtectedTagOrStr
from arretify.utils.html_create import replace_contents
from arretify.utils.html_semantic import css_selector

from .operands_detection import resolve_references_and_operands
from .operations_detection import parse_operations


def step_consolidation(document_context: DocumentContext) -> DocumentContext:
    # Find consolidation operations
    for container_tag in document_context.protected_soup.select(
        f"{css_selector(AlineaSpec)}, {css_selector(AlineaSpec)} *"
    ):
        contents: list[ProtectedTagOrStr] = list(container_tag.contents)
        # Parse operations only if there's a document or section reference in the paragraph
        # Helps avoid many false positives during processing
        document_reference_tags = container_tag.select(
            f"{css_selector(DocumentReferenceSpec)}, {css_selector(SectionReferenceSpec)}"
        )
        if document_reference_tags:
            contents = parse_operations(document_context, contents)

        replace_contents(container_tag, contents)

    # Resolve operation references and operands
    for operation_tag in document_context.protected_soup.select(css_selector(OperationSpec)):
        resolve_references_and_operands(document_context, operation_tag)

    return document_context
