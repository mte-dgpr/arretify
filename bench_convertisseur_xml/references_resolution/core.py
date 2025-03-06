from typing import List, Iterable, cast, Type

from bs4 import Tag

from bench_convertisseur_xml.types import PageElementOrString
from bench_convertisseur_xml.html_schemas import SECTION_REFERENCE_SCHEMA, DOCUMENT_REFERENCE_SCHEMA
from bench_convertisseur_xml.law_data.types import Document
from bench_convertisseur_xml.utils.html import make_css_class


SECTION_REFERENCE_CSS_CLASS = make_css_class(SECTION_REFERENCE_SCHEMA)
DOCUMENT_REFERENCE_CSS_CLASS = make_css_class(DOCUMENT_REFERENCE_SCHEMA)


def filter_section_references(
    children: Iterable[PageElementOrString],
    document_type: Type[Document],
) -> List[Tag]:
    return [
        child for child in children
        if (
            isinstance(child, Tag) 
            and SECTION_REFERENCE_CSS_CLASS in child.get('class', [])
            and cast(str, child.get('data-uri', '')).startswith(document_type.scheme)
        )
    ]


def filter_document_references(
    children: Iterable[PageElementOrString],
    document_type: Type[Document],
) -> List[Tag]:
    return [
        child for child in children
        if (
            isinstance(child, Tag) 
            and DOCUMENT_REFERENCE_CSS_CLASS in child.get('class', [])
            and cast(str, child.get('data-uri', '')).startswith(document_type.scheme)
        )
    ]