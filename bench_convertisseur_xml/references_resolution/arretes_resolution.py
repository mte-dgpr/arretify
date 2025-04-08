from typing import List, Iterable, cast
from dataclasses import replace as dataclass_replace

from bs4 import Tag

from bench_convertisseur_xml.law_data.uri import parse_uri
from bench_convertisseur_xml.law_data.legifrance import get_arrete_legifrance_id
from bench_convertisseur_xml.parsing_utils.dates import parse_date_str
from bench_convertisseur_xml.settings import LOGGER
from .core import update_reference_tag_uri, get_title_sample_next_sibling


def resolve_arrete_ministeriel_legifrance_id(
    document_reference_tag: Tag,
) -> None:
    uri = cast(str, document_reference_tag.get('data-uri'))
    document, sections = parse_uri(uri)
    
    if document.date is None:
        raise ValueError(f'Arrete ministeriel document {document} has no date')

    title = get_title_sample_next_sibling(document_reference_tag)
    if title is None:
        return

    date_object = parse_date_str(document.date)
    arrete_id = get_arrete_legifrance_id(
        date_object,
        title,
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