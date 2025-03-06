from typing import List, Iterable, cast
from dataclasses import replace as dataclass_replace

from bs4 import BeautifulSoup

from bench_convertisseur_xml.types import PageElementOrString
from bench_convertisseur_xml.law_data.types import UnknownDocument, UnknownDocumentTypes, ArreteMinisterielDocument
from bench_convertisseur_xml.law_data.uri import parse_uri, render_uri
from bench_convertisseur_xml.law_data.legifrance import get_arrete_legifrance_id
from bench_convertisseur_xml.regex_utils import PatternProxy, safe_group
from bench_convertisseur_xml.parsing_utils.dates import parse_date_str
from bench_convertisseur_xml.settings import LOGGER
from .core import filter_document_references


ARRETE_MINISTERIEL_TITLE_PATTERN = PatternProxy(r'^\s*([^\.;\s]+\s+){3,15}([^\.;\s]+)')


def resolve_arretes_ministeriels_legifrance_ids(
    soup: BeautifulSoup,
    children: Iterable[PageElementOrString],
) -> List[PageElementOrString]:
    children = list(children)
    document_references = filter_document_references(children, UnknownDocument)
    for document_reference_tag in document_references:
        uri = cast(str, document_reference_tag.get('data-uri'))
        document, sections = parse_uri(uri)

        if isinstance(document, UnknownDocument) and document.type == UnknownDocumentTypes.am:
            arrete_title_element = document_reference_tag.next_sibling
            if arrete_title_element is None or not isinstance(arrete_title_element, str):
                continue

            arrete_title_match = ARRETE_MINISTERIEL_TITLE_PATTERN.match(arrete_title_element)
            if arrete_title_match is None:
                continue
            
            date_object = parse_date_str(document.date)
            title = safe_group(arrete_title_match, 0)
            arrete_id = get_arrete_legifrance_id(
                title=title,
                date=date_object
            )
            if arrete_id is None:
                LOGGER.warn(
                    f'Could not find legifrance arrete id for '
                    f'date {date_object} "{title}"'
                )
                continue

            document = ArreteMinisterielDocument(legifrance_id=arrete_id, date=document.date)
            updated_uri = render_uri(document, *sections)
            document_reference_tag['data-uri'] = updated_uri

    return children


# def resolve_unknown_arretes_uris(
#     soup: BeautifulSoup,
#     children: Iterable[PageElementOrString],
# ) -> List[PageElementOrString]:
#     return _resolve_single_section_unknown_uri(soup, children)