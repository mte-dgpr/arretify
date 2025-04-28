from typing import List, cast
import logging

from bs4 import Tag

from arretify.types import ParsingContext
from arretify.html_schemas import (
    SECTIONS_AND_DOCUMENT_REFERENCES,
    SECTION_REFERENCE_SCHEMA,
    DOCUMENT_REFERENCE_SCHEMA,
)
from arretify.utils.html import (
    make_css_class,
    has_css_class,
    assign_element_id,
    render_str_list_attribute,
    parse_bool_attribute,
)
from arretify.utils.element_ranges import (
    get_contiguous_elements_left,
    get_contiguous_elements_right,
)


DOCUMENT_REFERENCE_CLASS = make_css_class(DOCUMENT_REFERENCE_SCHEMA)
SECTION_REFERENCE_CLASS = make_css_class(SECTION_REFERENCE_SCHEMA)
SECTIONS_AND_DOCUMENT_REFERENCES_CLASS = make_css_class(SECTIONS_AND_DOCUMENT_REFERENCES)

_LOGGER = logging.getLogger(__name__)


def resolve_references_and_operands(_: ParsingContext, operation_tag: Tag) -> None:
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
        if isinstance(element, Tag) and has_css_class(
            element, SECTIONS_AND_DOCUMENT_REFERENCES_CLASS
        ):
            reference_tags = element.select(f".{SECTION_REFERENCE_CLASS}")
            if len(reference_tags) == 0:
                raise ValueError("No section reference found in operation")
            break

    if len(reference_tags) == 0:
        for element in contiguous_elements_left:
            if isinstance(element, Tag) and has_css_class(element, DOCUMENT_REFERENCE_CLASS):
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
