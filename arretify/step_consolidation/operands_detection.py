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

from arretify.semantic_tag_specs import (
    DocumentReferenceSpec,
    OperationSpec,
    PageFooterSpec,
    PageSeparatorSpec,
    SectionReferenceSpec,
)
from arretify.types import DocumentContext, ProtectedTag
from arretify.utils.html import ensure_tag_id, is_tag
from arretify.utils.html_element_ranges import (
    get_contiguous_elements_left,
    get_contiguous_elements_right,
)
from arretify.utils.html_semantic import (
    SemanticTagSpec,
    get_semantic_tag_data,
    is_semantic_tag,
    update_semantic_tag_data,
)
from arretify.utils.references import build_reference_tree

_LOGGER = logging.getLogger(__name__)


# TODO : refactor to factorize with list in step_segmentation
INLINE_TAG_SCHEMAS: list[SemanticTagSpec] = [
    PageFooterSpec,
    PageSeparatorSpec,
]


def resolve_references_and_operands(
    document_context: DocumentContext, operation_tag: ProtectedTag
) -> None:
    operation_data = get_semantic_tag_data(OperationSpec, operation_tag)
    if operation_data.direction != "rtl":
        raise ValueError("Only right-to-left is supported so far")

    reference_tags: list[ProtectedTag] = _find_left_references(document_context, operation_tag)
    if len(reference_tags) == 0:
        _LOGGER.warning("No references found in operation")
        return
    operation_data = update_semantic_tag_data(
        OperationSpec,
        operation_tag,
        references=[ensure_tag_id(document_context.id_counters, tag) for tag in reference_tags],
    )

    if operation_data.has_operand:
        operand_tag: ProtectedTag | None = _find_right_operand(document_context, operation_tag)
        if operand_tag is None:
            _LOGGER.warning("No right operand found for operation")
            return
        operation_data = update_semantic_tag_data(
            OperationSpec,
            operation_tag,
            operand=ensure_tag_id(document_context.id_counters, operand_tag),
        )


def _find_right_operand(
    document_context: DocumentContext, start_tag: ProtectedTag
) -> ProtectedTag | None:
    for element in get_contiguous_elements_right(start_tag):
        if is_tag(
            element,
            tag_name_in=[
                "blockquote",
                "q",
                "table",
            ],
        ):
            return element

        # We ignore inline tags like page separators and footers
        # and look recursively for the next neighbouring element.
        elif is_semantic_tag(element, spec_in=INLINE_TAG_SCHEMAS):
            return _find_right_operand(document_context, element)
    return None


def _find_left_references(
    document_context: DocumentContext, start_tag: ProtectedTag
) -> list[ProtectedTag]:
    contiguous_elements_left = get_contiguous_elements_left(start_tag)
    reference_tags: list[ProtectedTag] = []

    for element in contiguous_elements_left:
        if is_semantic_tag(
            element,
            spec_in=[
                SectionReferenceSpec,
                DocumentReferenceSpec,
            ],
        ):
            # Take the leaves of the reference tree, i.e. the most
            # specific reference in a chain of sections.
            # For example in "l'alinéa 3 de l'article 5 du présent arrêté",
            # the operation applies to "alinéa 3".
            reference_tree = build_reference_tree(element)
            reference_tags = [branch[-1] for branch in reference_tree]
            if len(reference_tags) == 0:
                raise ValueError("No section or document reference found in operation")
            break

        # We ignore inline tags like page separators and footers
        # and look recursively for the next neighbouring element.
        elif is_semantic_tag(element, spec_in=INLINE_TAG_SCHEMAS):
            return _find_left_references(document_context, element)

    if len(reference_tags) == 0:
        for element in contiguous_elements_left:
            if is_semantic_tag(element, spec_in=[DocumentReferenceSpec]):
                reference_tags = [element]
                break

    return reference_tags
