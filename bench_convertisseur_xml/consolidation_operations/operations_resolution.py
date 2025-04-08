from typing import List, cast

from bs4 import Tag, PageElement

from bench_convertisseur_xml.settings import LOGGER
from bench_convertisseur_xml.types import ElementId
from bench_convertisseur_xml.html_schemas import SECTIONS_AND_DOCUMENT_REFERENCES, SECTION_REFERENCE_SCHEMA
from bench_convertisseur_xml.utils.html import make_css_class, has_css_class, assign_element_id, parse_str_list_attribute, render_str_list_attribute, parse_bool_attribute
from bench_convertisseur_xml.utils.html_tree_navigation import closest_common_ancestor, is_parent
from bench_convertisseur_xml.utils.element_ranges import get_contiguous_elements_left, get_contiguous_elements_right
from bench_convertisseur_xml.law_data.uri import parse_uri, is_resolvable


SECTION_REFERENCE_CLASS = make_css_class(SECTION_REFERENCE_SCHEMA)
SECTIONS_AND_DOCUMENT_REFERENCES_CLASS = make_css_class(SECTIONS_AND_DOCUMENT_REFERENCES)


def resolve_references_and_operands(operation_tag: Tag) -> None:
    if operation_tag['data-direction'] != 'rtl':
        raise ValueError('Only right-to-left is supported so far')
    _resolve_rtl_references(operation_tag)
    has_operand = parse_bool_attribute(cast(str, operation_tag['data-has_operand']))
    if has_operand:
        _resolve_rtl_operand(operation_tag)


def _resolve_rtl_references(operation_tag: Tag) -> None:
    references_container_tag: Tag | None = None
    for element in get_contiguous_elements_left(operation_tag):
        if (
            isinstance(element, Tag)
            and has_css_class(element, SECTIONS_AND_DOCUMENT_REFERENCES_CLASS)
        ):
            references_container_tag = element
            break

    if references_container_tag is None:
        LOGGER.warning('No references container found in operation')
        return

    section_reference_tags = references_container_tag.select(f'.{SECTION_REFERENCE_CLASS}')
    if len(section_reference_tags) == 0:
        raise ValueError('No section reference found in operation')

    reference_ids: List[ElementId] = [
        assign_element_id(tag) for tag in section_reference_tags
    ]

    if reference_ids:
        operation_tag['data-references'] = render_str_list_attribute(reference_ids)


def _resolve_rtl_operand(operation_tag: Tag) -> None:    
    operand_tag: Tag | None = None
    for element in get_contiguous_elements_right(operation_tag):
        if (
            isinstance(element, Tag) 
            and element.name in ['blockquote', 'q', 'table']
        ):
            operand_tag = element
            break

    if operand_tag is None:
        LOGGER.warning('No right operand found for operation')
        return 
    
    element_id = assign_element_id(operand_tag)
    operation_tag['data-operand'] = element_id

