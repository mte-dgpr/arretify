from typing import List, Iterable, cast
from dataclasses import replace as dataclass_replace

from bs4 import Tag

from bench_convertisseur_xml.types import PageElementOrString
from bench_convertisseur_xml.law_data.types import Document, DocumentType
from bench_convertisseur_xml.law_data.uri import parse_uri, render_uri, is_resolvable
from bench_convertisseur_xml.law_data.legifrance import get_arrete_legifrance_id
from bench_convertisseur_xml.law_data.external_urls import resolve_external_url
from bench_convertisseur_xml.regex_utils import PatternProxy, safe_group
from bench_convertisseur_xml.utils.html import render_bool_attribute
from bench_convertisseur_xml.parsing_utils.dates import parse_date_str
from bench_convertisseur_xml.settings import LOGGER
from .core import update_reference_tag_uri


# Regex for searching an arrete ministeriel with its title.
# Simply picks the first 3 to 15 words following the document reference.
ARRETE_MINISTERIEL_TITLE_PATTERN = PatternProxy(r'^\s*([^\.;\s]+\s+){3,15}([^\.;\s]+)')


def resolve_arrete_ministeriel_legifrance_id(
    document_reference_tag: Tag,
) -> None:
    uri = cast(str, document_reference_tag.get('data-uri'))
    document, sections = parse_uri(uri)

    arrete_title_element = document_reference_tag.next_sibling
    if arrete_title_element is None or not isinstance(arrete_title_element, str):
        return

    arrete_title_match = ARRETE_MINISTERIEL_TITLE_PATTERN.match(arrete_title_element)
    if arrete_title_match is None:
        return
    
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
        return

    update_reference_tag_uri(document_reference_tag, dataclass_replace(
        document,
        id=arrete_id,
    ), *sections)