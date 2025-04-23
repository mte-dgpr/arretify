from typing import List, Iterable

from bs4 import BeautifulSoup, Tag, PageElement

from arretify.types import PageElementOrString
from arretify.utils.element_ranges import (
    iter_collapsed_range_right,
    ElementRange,
)
from arretify.utils.html import (
    make_css_class,
    make_data_tag,
    assign_element_id,
)
from arretify.html_schemas import (
    SECTION_REFERENCE_SCHEMA,
    SECTION_REFERENCE_MULTIPLE_SCHEMA,
    DOCUMENT_REFERENCE_SCHEMA,
    SECTIONS_AND_DOCUMENT_REFERENCES,
)
from arretify.regex_utils import regex_tree
from .core import filter_section_references

SECTION_REFERENCE_CSS_CLASS = make_css_class(SECTION_REFERENCE_SCHEMA)
SECTION_REFERENCE_MULTIPLE_CSS_CLASS = make_css_class(SECTION_REFERENCE_MULTIPLE_SCHEMA)
DOCUMENT_REFERENCE_CSS_CLASS = make_css_class(DOCUMENT_REFERENCE_SCHEMA)


CONNECTOR_SECTION_DOCUMENT_NODE = regex_tree.Group(
    regex_tree.Sequence(
        [
            # Allows a maximum of 3 random words before the connector
            r"^(\s*[^\.\s]+){0,3}\s*",
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
    group_name="__connector_section_document",
)


def match_sections_with_documents(
    soup: BeautifulSoup,
    children: Iterable[PageElementOrString],
) -> List[PageElementOrString]:
    # We must first match the multiple section references,
    # as they may contain single section references.
    new_children = _match_multiple_sections_with_document(soup, children)
    return _match_single_section_with_document(soup, new_children)


def _match_single_section_with_document(
    soup: BeautifulSoup,
    children: Iterable[PageElementOrString],
) -> List[PageElementOrString]:
    children = list(children)
    section_references = filter_section_references(children)
    element_ranges: List[ElementRange] = []

    for section_reference_tag in section_references:
        element_range = _find_section_document_range(section_reference_tag)
        if element_range is None:
            continue
        element_ranges.append(element_range)
        _add_element_ids(section_reference_tag, element_range[-1])

    for element_range in element_ranges:
        children = _wrap_sections_and_document_references(soup, children, element_range)

    return children


def _match_multiple_sections_with_document(
    soup: BeautifulSoup,
    children: Iterable[PageElementOrString],
) -> List[PageElementOrString]:
    children = list(children)
    section_multiple_references = [
        child
        for child in children
        if (
            isinstance(child, Tag)
            and SECTION_REFERENCE_MULTIPLE_CSS_CLASS in child.get("class", [])
        )
    ]
    element_ranges: List[ElementRange] = []

    for section_multiple_reference_tag in section_multiple_references:
        element_range = _find_section_document_range(section_multiple_reference_tag)
        if element_range is None:
            continue

        element_ranges.append(element_range)
        section_reference_tags = section_multiple_reference_tag.select(
            f".{SECTION_REFERENCE_CSS_CLASS}"
        )
        for section_reference_tag in section_reference_tags:
            _add_element_ids(section_reference_tag, element_range[-1])

    for element_range in element_ranges:
        children = _wrap_sections_and_document_references(soup, children, element_range)
    return children


def _find_section_document_range(
    section_reference_tag: Tag,
) -> ElementRange | None:
    for element_range in iter_collapsed_range_right(section_reference_tag):
        # Make sure all elements in the range are contiguous.
        if element_range[-1].parent != section_reference_tag.parent:
            return None

        if len(element_range) > 3:
            return None

        elif (
            len(element_range) == 3
            and isinstance(element_range[2], Tag)
            and DOCUMENT_REFERENCE_CSS_CLASS in element_range[2].get("class", [])
            and isinstance(element_range[1], str)
        ):
            if bool(regex_tree.match(CONNECTOR_SECTION_DOCUMENT_NODE, element_range[1])):
                return element_range
            else:
                return None

        else:
            continue
    return None


def _add_element_ids(section_reference_tag: Tag, document_reference_tag: PageElement) -> None:
    if not isinstance(
        document_reference_tag, Tag
    ) or DOCUMENT_REFERENCE_CSS_CLASS not in document_reference_tag.get("class", []):
        raise RuntimeError("Expected a document reference tag with a data-uri attribute")

    document_element_id = assign_element_id(document_reference_tag)
    section_reference_tag["data-document_reference"] = document_element_id


def _wrap_sections_and_document_references(
    soup: BeautifulSoup,
    children: Iterable[PageElementOrString],
    element_range: ElementRange,
) -> List[PageElementOrString]:
    children = list(children)
    start_index = children.index(element_range[0])
    end_index = children.index(element_range[-1])
    children[start_index : end_index + 1] = [
        make_data_tag(
            soup,
            SECTIONS_AND_DOCUMENT_REFERENCES,
            contents=children[start_index : end_index + 1],
        )
    ]
    return children
