from typing import List, Iterable, cast
from dataclasses import replace as dataclass_replace

from bs4 import BeautifulSoup

from bench_convertisseur_xml.types import PageElementOrString
from bench_convertisseur_xml.law_data.types import Document, DocumentType
from bench_convertisseur_xml.law_data.uri import parse_uri, render_uri, is_resolvable
from bench_convertisseur_xml.law_data.legifrance import get_arrete_legifrance_id
from bench_convertisseur_xml.law_data.external_urls import resolve_external_url
from bench_convertisseur_xml.regex_utils import PatternProxy, safe_group
from bench_convertisseur_xml.utils.html import render_bool_attribute
from bench_convertisseur_xml.parsing_utils.dates import parse_date_str
from bench_convertisseur_xml.settings import LOGGER
from .core import filter_document_references


ARRETE_MINISTERIEL_TITLE_PATTERN = PatternProxy(r'^\s*([^\.;\s]+\s+){3,15}([^\.;\s]+)')


def resolve_arretes_ministeriels_legifrance_ids(
    soup: BeautifulSoup,
    children: Iterable[PageElementOrString],
) -> List[PageElementOrString]:
    children = list(children)
    document_references = filter_document_references(children, DocumentType.arrete_ministeriel)
    for document_reference_tag in document_references:
        uri = cast(str, document_reference_tag.get('data-uri'))
        document, sections = parse_uri(uri)

        arrete_title_element = document_reference_tag.next_sibling
        if arrete_title_element is None or not isinstance(arrete_title_element, str):
            continue

        arrete_title_match = ARRETE_MINISTERIEL_TITLE_PATTERN.match(arrete_title_element)
        if arrete_title_match is None:
            continue
        
        if document.date is None:
            raise ValueError(f'Arrete ministeriel document {document} has no date')

        date_object = parse_date_str(document.date)
        title = safe_group(arrete_title_match, 0)
        arrete_id = get_arrete_legifrance_id(
            title,
            date_object,
        )
        if arrete_id is None:
            LOGGER.warning(
                f'Could not find legifrance arrete id for '
                f'date {date_object} "{title}"'
            )
            continue

        document = dataclass_replace(
            document,
            id=arrete_id,
        )
        is_document_resolvable = is_resolvable(document)
        updated_uri = render_uri(document, *sections)
        document_reference_tag['data-uri'] = updated_uri
        document_reference_tag['is_resolvable'] = render_bool_attribute(is_document_resolvable)
        
        if is_document_resolvable:
            external_url = resolve_external_url(document)
            if external_url is None:
                raise ValueError(f'Could not resolve external url for {document}')
            document_reference_tag['href'] = external_url

    return children