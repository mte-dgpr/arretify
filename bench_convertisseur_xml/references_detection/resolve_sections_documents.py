from typing import List, Iterable, cast

from bs4 import BeautifulSoup, Tag, PageElement

from bench_convertisseur_xml.types import PageElementOrString
from bench_convertisseur_xml.utils.element_ranges import find_element_range
from bench_convertisseur_xml.utils.html import make_css_class
from bench_convertisseur_xml.html_schemas import SECTION_REFERENCE_SCHEMA, DOCUMENT_REFERENCE_SCHEMA
from bench_convertisseur_xml.uri import UnknownDocument, parse_uri, render_uri
from bench_convertisseur_xml.regex_utils import regex_tree

DOCUMENT_REFERENCE_CSS_CLASS = make_css_class(DOCUMENT_REFERENCE_SCHEMA)
SECTION_REFERENCE_CSS_CLASS = make_css_class(SECTION_REFERENCE_SCHEMA)


CONNECTOR_SECTION_DOCUMENT_NODE = regex_tree.Group(
    regex_tree.Branching([
        r'^\s*du\s*$',
        r'^\s*de\s+l\'\s*$',
        r'^\s*de\s+la\s*$',
        r'^\s*des\s*$',
    ]),
    group_name='__connector_section_document',
)


def resolve_sections_documents(
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
        element_range = find_element_range(
            section_reference_tag,
            _is_matching_document,
        )
        if element_range is None:
            continue
        document_reference_tag = element_range[-1]
        if (
            not isinstance(document_reference_tag, Tag) 
            or not DOCUMENT_REFERENCE_CSS_CLASS in document_reference_tag.get('class', [])
        ):
            raise RuntimeError("Expected a document reference tag with a data-uri attribute")

        _, section_list = parse_uri(cast(str, section_reference_tag['data-uri']))
        document, _ = parse_uri(cast(str, document_reference_tag['data-uri']))
        section_reference_tag['data-uri'] = render_uri(document, *section_list)

    return children


def _is_matching_document(current: PageElement, element_range: List[PageElement]) -> bool | None:
    if (len(element_range) > 2):
        return None

    if (
        len(element_range) == 2
        and isinstance(current, Tag)
        and DOCUMENT_REFERENCE_CSS_CLASS in current.get('class', [])
        and isinstance(element_range[1], str)
    ):
        return bool(
            regex_tree.match(
                CONNECTOR_SECTION_DOCUMENT_NODE, 
                element_range[1]
            )
        )

    return False
