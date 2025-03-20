from typing import Dict, List, Iterable, cast, Tuple
from dataclasses import dataclass, replace as dataclass_replace

from bs4 import BeautifulSoup, Tag

from bench_convertisseur_xml.settings import LOGGER
from bench_convertisseur_xml.law_data.types import DocumentType, SectionType, Section
from bench_convertisseur_xml.law_data.uri import parse_uri, render_uri, is_resolvable
from bench_convertisseur_xml.law_data.eurlex import get_eu_act_url_with_year_and_num, ActType
from bench_convertisseur_xml.types import PageElementOrString
from bench_convertisseur_xml.utils.html import render_bool_attribute
from .core import filter_document_references

def resolve_eu_acts_eurlex_urls(
    soup: BeautifulSoup,
    children: Iterable[PageElementOrString],
) -> List[PageElementOrString]:
    new_children = list(children)
    eu_decisions_references: List[Tuple[ActType, Tag]] = [('decision', tag) for tag in filter_document_references(children, DocumentType.eu_decision)]
    eu_regulations_references: List[Tuple[ActType, Tag]] = [('regulation', tag) for tag in filter_document_references(children, DocumentType.eu_regulation)]
    eu_directives_references: List[Tuple[ActType, Tag]] = [('directive', tag) for tag in filter_document_references(children, DocumentType.eu_directive)]

    for act_type, code_reference_tag in eu_decisions_references + eu_regulations_references + eu_directives_references:
        document, sections = parse_uri(cast(str, code_reference_tag['data-uri']))

        if document.num is None or document.date is None:
            raise ValueError(f'Could not find num or date for document {document}')

        eurlex_url = get_eu_act_url_with_year_and_num(act_type, int(document.date), int(document.num))
        if eurlex_url is None:
            LOGGER.warn(f'Could not find eurlex url for {act_type} {document.date}/{document.num}')
            continue

        document = dataclass_replace(document, id=eurlex_url)
        code_reference_tag['data-uri'] = render_uri(document, *sections)
        code_reference_tag['data-is_resolvable'] = render_bool_attribute(
            is_resolvable(document, *sections))
        code_reference_tag['href'] = eurlex_url
    return new_children