from typing import List, Iterable, cast

from bs4 import BeautifulSoup, Tag, PageElement

from bench_convertisseur_xml.types import PageElementOrString
from bench_convertisseur_xml.utils.element_ranges import iter_collapsed_range_right, iter_collapsed_range_left, ElementRange
from bench_convertisseur_xml.utils.html import make_css_class
from bench_convertisseur_xml.html_schemas import SECTION_REFERENCE_SCHEMA, SECTION_REFERENCE_MULTIPLE_SCHEMA, DOCUMENT_REFERENCE_SCHEMA
from bench_convertisseur_xml.uri import UnknownDocument, parse_uri, render_uri
from bench_convertisseur_xml.regex_utils import regex_tree

SECTION_REFERENCE_CSS_CLASS = make_css_class(SECTION_REFERENCE_SCHEMA)
SECTION_REFERENCE_MULTIPLE_CSS_CLASS = make_css_class(SECTION_REFERENCE_MULTIPLE_SCHEMA)
DOCUMENT_REFERENCE_CSS_CLASS = make_css_class(DOCUMENT_REFERENCE_SCHEMA)


CONNECTOR_SECTION_DOCUMENT_NODE = regex_tree.Group(
    regex_tree.Sequence([
        # Allows a maximum of 3 random words before the connector
        r'^(\s*[^\.\s]+){0,3}\s*',
        regex_tree.Branching([
            r'du',
            r'de\s+l\'',
            r'de\s+la',
            r'des',
        ]),
        r'\s*$',
    ]),
    group_name='__connector_section_document',
)


def resolve_sections_unknown_uris(
    soup: BeautifulSoup,
    children: Iterable[PageElementOrString],
) -> List[PageElementOrString]:
    # We must first resolve the multiple section references, 
    # as they may contain single section references.
    new_children = _resolve_multiple_section_unknown_uris(soup, children)
    return _resolve_single_section_unknown_uri(soup, new_children)


def _resolve_single_section_unknown_uri(
    soup: BeautifulSoup,
    children: Iterable[PageElementOrString],
) -> List[PageElementOrString]:
    children = list(children)
    section_references = [
        child for child in children
        if (
            isinstance(child, Tag) 
            and SECTION_REFERENCE_CSS_CLASS in child.get('class', []) 
            and cast(str, child.get('data-uri', '')).startswith(UnknownDocument.scheme)
        )
    ]

    for section_reference_tag in section_references:
        element_range = _find_section_document_range(section_reference_tag)
        if element_range is None:
            continue
        _update_section_reference_uri(section_reference_tag, element_range[-1])

    return children


def _resolve_multiple_section_unknown_uris(
    soup: BeautifulSoup,
    children: Iterable[PageElementOrString],
) -> List[PageElementOrString]:
    children = list(children)
    section_multiple_references = [
        child for child in children
        if (
            isinstance(child, Tag) 
            and SECTION_REFERENCE_MULTIPLE_CSS_CLASS in child.get('class', [])
        )
    ]

    for section_multiple_reference_tag in section_multiple_references:
        element_range = _find_section_document_range(section_multiple_reference_tag)
        if element_range is None:
            continue
        section_reference_tags = section_multiple_reference_tag.select(f'.{SECTION_REFERENCE_CSS_CLASS}')
        for section_reference_tag in section_reference_tags:
            _update_section_reference_uri(section_reference_tag, element_range[-1])
    return children


def _find_section_document_range(section_reference_tag: Tag) -> ElementRange | None:
    for element_range in iter_collapsed_range_right(section_reference_tag):
        if (len(element_range) > 3):
            return None

        elif (
            len(element_range) == 3
            and isinstance(element_range[2], Tag)
            and DOCUMENT_REFERENCE_CSS_CLASS in element_range[2].get('class', [])
            and isinstance(element_range[1], str)
        ):
            if bool(
                regex_tree.match(
                    CONNECTOR_SECTION_DOCUMENT_NODE, 
                    element_range[1]
                )
            ):
                return element_range
            else:
                return None

        else:
            continue
    return None


def _update_section_reference_uri(section_reference_tag: Tag, document_reference_tag: PageElement) -> None:
    if (
        not isinstance(document_reference_tag, Tag) 
        or not DOCUMENT_REFERENCE_CSS_CLASS in document_reference_tag.get('class', [])
    ):
        raise RuntimeError("Expected a document reference tag with a data-uri attribute")

    _, section_list = parse_uri(cast(str, section_reference_tag['data-uri']))
    document, _ = parse_uri(cast(str, document_reference_tag['data-uri']))
    section_reference_tag['data-uri'] = render_uri(document, *section_list)