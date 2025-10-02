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
from typing import cast
import logging

from bs4 import Tag

from arretify.types import DocumentContext
from arretify.semantic_tag_schemas import (
    SECTION_REFERENCE_SCHEMA,
    DOCUMENT_REFERENCE_SCHEMA,
    PAGE_SEPARATOR_SCHEMA,
    PAGE_FOOTER_SCHEMA,
)
from arretify.utils.html import (
    ensure_element_id,
    render_str_list_attribute,
    parse_bool_attribute,
    is_tag,
)
from arretify.utils.element_ranges import (
    get_contiguous_elements_left,
    get_contiguous_elements_right,
)
from arretify.utils.references import build_reference_tree


_LOGGER = logging.getLogger(__name__)


# TODO : refactor to factorize with list in step_segmentation
INLINE_TAG_SCHEMAS = [
    PAGE_FOOTER_SCHEMA,
    PAGE_SEPARATOR_SCHEMA,
]


def resolve_references_and_operands(document_context: DocumentContext, operation_tag: Tag) -> None:
    if operation_tag["data-direction"] != "rtl":
        raise ValueError("Only right-to-left is supported so far")

    reference_tags: list[Tag] = _find_left_references(document_context, operation_tag)
    if len(reference_tags) == 0:
        _LOGGER.warning("No references found in operation")
        return
    operation_tag["data-references"] = render_str_list_attribute(
        [ensure_element_id(document_context.id_counters, tag) for tag in reference_tags]
    )

    has_operand = parse_bool_attribute(cast(str, operation_tag["data-has_operand"]))
    if has_operand:
        operand_tag: Tag | None = _find_right_operand(document_context, operation_tag)
        if operand_tag is None:
            _LOGGER.warning("No right operand found for operation")
            return
        element_id = ensure_element_id(document_context.id_counters, operand_tag)
        operation_tag["data-operand"] = element_id


def _find_right_operand(document_context: DocumentContext, start_tag: Tag) -> Tag | None:
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
        elif is_tag(element, css_classes_in=[s.css_class for s in INLINE_TAG_SCHEMAS]):
            return _find_right_operand(document_context, element)
    return None


def _find_left_references(document_context: DocumentContext, start_tag: Tag) -> list[Tag]:
    contiguous_elements_left = get_contiguous_elements_left(start_tag)
    reference_tags: list[Tag] = []

    for element in contiguous_elements_left:
        if is_tag(
            element,
            css_classes_in=[
                SECTION_REFERENCE_SCHEMA.css_class,
                DOCUMENT_REFERENCE_SCHEMA.css_class,
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
        elif is_tag(element, css_classes_in=[s.css_class for s in INLINE_TAG_SCHEMAS]):
            return _find_left_references(document_context, element)

    if len(reference_tags) == 0:
        for element in contiguous_elements_left:
            if is_tag(element, css_classes_in=[DOCUMENT_REFERENCE_SCHEMA.css_class]):
                reference_tags = [element]
                break

    return reference_tags
