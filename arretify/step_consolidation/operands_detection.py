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
from typing import List, cast
import logging

from bs4 import Tag

from arretify.types import DocumentContext
from arretify.html_schemas import (
    SECTION_REFERENCE_SCHEMA,
    DOCUMENT_REFERENCE_SCHEMA,
)
from arretify.utils.html import (
    make_css_class,
    assign_element_id,
    render_str_list_attribute,
    parse_bool_attribute,
    is_tag_and_matches,
)
from arretify.utils.element_ranges import (
    get_contiguous_elements_left,
    get_contiguous_elements_right,
)
from arretify.step_references_detection.match_sections_with_documents import build_reference_tree


DOCUMENT_REFERENCE_CLASS = make_css_class(DOCUMENT_REFERENCE_SCHEMA)
SECTION_REFERENCE_CLASS = make_css_class(SECTION_REFERENCE_SCHEMA)

_LOGGER = logging.getLogger(__name__)


def resolve_references_and_operands(_: DocumentContext, operation_tag: Tag) -> None:
    if operation_tag["data-direction"] != "rtl":
        raise ValueError("Only right-to-left is supported so far")
    _resolve_rtl_references(operation_tag)
    has_operand = parse_bool_attribute(cast(str, operation_tag["data-has_operand"]))
    if has_operand:
        _resolve_rtl_operand(operation_tag)


def _resolve_rtl_references(operation_tag: Tag) -> None:
    contiguous_elements_left = get_contiguous_elements_left(operation_tag)
    reference_tags: List[Tag] = []

    for element in contiguous_elements_left:
        if is_tag_and_matches(
            element, css_classes_in=[SECTION_REFERENCE_CLASS, DOCUMENT_REFERENCE_CLASS]
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

    if len(reference_tags) == 0:
        for element in contiguous_elements_left:
            if is_tag_and_matches(element, css_classes_in=[DOCUMENT_REFERENCE_CLASS]):
                reference_tags = [element]
                break

    if len(reference_tags) == 0:
        _LOGGER.warning("No references found in operation")
        return

    operation_tag["data-references"] = render_str_list_attribute(
        [assign_element_id(tag) for tag in reference_tags]
    )


def _resolve_rtl_operand(operation_tag: Tag) -> None:
    operand_tag: Tag | None = None
    for element in get_contiguous_elements_right(operation_tag):
        if isinstance(element, Tag) and element.name in [
            "blockquote",
            "q",
            "table",
        ]:
            operand_tag = element
            break

    if operand_tag is None:
        _LOGGER.warning("No right operand found for operation")
        return

    element_id = assign_element_id(operand_tag)
    operation_tag["data-operand"] = element_id
