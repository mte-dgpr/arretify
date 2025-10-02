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

from arretify.semantic_tag_schemas import (
    ALINEA_SCHEMA,
    DOCUMENT_REFERENCE_SCHEMA,
    OPERATION_SCHEMA,
    SECTION_REFERENCE_SCHEMA,
)
from arretify.types import PageElementOrString, DocumentContext
from arretify.utils.html_create import replace_children

from .operations_detection import (
    parse_operations,
)
from .operands_detection import (
    resolve_references_and_operands,
)


def step_consolidation(document_context: DocumentContext) -> DocumentContext:
    # Find consolidation operations
    for container_tag in document_context.soup.select(
        f".{ALINEA_SCHEMA.css_class}, .{ALINEA_SCHEMA.css_class} *"
    ):
        new_children: list[PageElementOrString] = list(container_tag.children)
        # Parse operations only if there's a document or section reference in the paragraph
        # Helps avoid many false positives during processing
        document_reference_tags = container_tag.select(
            f".{DOCUMENT_REFERENCE_SCHEMA.css_class}, .{SECTION_REFERENCE_SCHEMA.css_class}"
        )
        if document_reference_tags:
            new_children = parse_operations(document_context, new_children)

        replace_children(container_tag, new_children)

    # Resolve operation references and operands
    for operation_tag in document_context.soup.select(f".{OPERATION_SCHEMA.css_class}"):
        resolve_references_and_operands(document_context, operation_tag)

    return document_context
