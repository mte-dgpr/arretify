from typing import List, Iterable, cast, Type

from bs4 import Tag

from bench_convertisseur_xml.types import PageElementOrString
from bench_convertisseur_xml.html_schemas import SECTION_REFERENCE_SCHEMA, DOCUMENT_REFERENCE_SCHEMA
from bench_convertisseur_xml.law_data.types import Document, DocumentType, Section
from bench_convertisseur_xml.law_data.uri import is_uri_document_type, is_resolvable, render_uri
from bench_convertisseur_xml.law_data.external_urls import resolve_external_url
from bench_convertisseur_xml.utils.html import make_css_class, render_bool_attribute


SECTION_REFERENCE_CSS_CLASS = make_css_class(SECTION_REFERENCE_SCHEMA)
DOCUMENT_REFERENCE_CSS_CLASS = make_css_class(DOCUMENT_REFERENCE_SCHEMA)


def filter_section_references(
    children: Iterable[PageElementOrString],
    document_type: DocumentType,
) -> List[Tag]:
    return [
        child for child in children
        if (
            isinstance(child, Tag)
            and SECTION_REFERENCE_CSS_CLASS in child.get('class', [])
            and is_uri_document_type(cast(str, child.get('data-uri', '')), document_type)
        )
    ]


def filter_document_references(
    children: Iterable[PageElementOrString],
    document_type: DocumentType,
) -> List[Tag]:
    return [
        child for child in children
        if (
            isinstance(child, Tag) 
            and DOCUMENT_REFERENCE_CSS_CLASS in child.get('class', [])
            and is_uri_document_type(cast(str, child.get('data-uri', '')), document_type)
        )
    ]


def update_reference_tag_uri(tag: Tag, document: Document, *sections: Section) -> None:
    is_document_resolvable = is_resolvable(document, *sections)
    updated_uri = render_uri(document, *sections)
    tag['data-uri'] = updated_uri
    tag['data-is_resolvable'] = render_bool_attribute(is_document_resolvable)
    
    if is_document_resolvable:
        external_url = resolve_external_url(document, *sections)
        if external_url is None:
            raise ValueError(f'Could not resolve external url for {document}')
        tag['href'] = external_url