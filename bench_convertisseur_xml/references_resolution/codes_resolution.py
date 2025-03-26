from typing import Iterable, List, cast, Dict
from dataclasses import replace as dataclass_replace

from bs4 import BeautifulSoup, Tag

from bench_convertisseur_xml.settings import LOGGER
from bench_convertisseur_xml.law_data.types import DocumentType, SectionType, Section
from bench_convertisseur_xml.law_data.uri import parse_uri, render_uri, is_resolvable
from bench_convertisseur_xml.law_data.legifrance import get_code_article_id_from_article_num
from bench_convertisseur_xml.types import PageElementOrString
from bench_convertisseur_xml.law_data.external_urls import resolve_external_url
from bench_convertisseur_xml.utils.html import render_bool_attribute
from bench_convertisseur_xml.law_data.legifrance import get_code_id_with_title
from .core import filter_section_references, filter_document_references, update_reference_tag_uri


def resolve_code_articles_legifrance_ids(
    soup: BeautifulSoup,
    children: Iterable[PageElementOrString],
) -> List[PageElementOrString]:
    new_children = list(children)
    code_articles_references = filter_section_references(children, DocumentType.code)
    for code_article_reference_tag in code_articles_references:
        document, sections = parse_uri(cast(str, code_article_reference_tag['data-uri']))
        if not document.is_resolvable:
            continue

        if document.id is None:
            raise RuntimeError('Code document id is None')

        resolved_sections: List[Section] = []        
        for section in sections:
            if section.type == SectionType.article:
                new_fields: Dict[str, str | None] = dict(
                    start_id=None,
                    end_id=None,
                )

                for num_key, id_key in (('start_num', 'start_id'), ('end_num', 'end_id')):
                    if getattr(section, num_key) is not None:
                        article_id = get_code_article_id_from_article_num(
                            document.id, 
                            getattr(section, num_key)
                        )
                        if article_id:
                            new_fields[id_key] = article_id
                        else:
                            LOGGER.warning(
                                f'Could not find legifrance article id for '
                                f'code {document.id} article {getattr(section, num_key)}'
                            )
                
                section = dataclass_replace(section, 
                    start_id=new_fields['start_id'],
                    end_id=new_fields['end_id'],
                )
                
            resolved_sections.append(section)

        update_reference_tag_uri(code_article_reference_tag, document, *resolved_sections)

    return new_children


def resolve_code_legifrance_ids(
    soup: BeautifulSoup,
    children: Iterable[PageElementOrString],
) -> List[PageElementOrString]:
    new_children = list(children)
    code_references = filter_document_references(children, DocumentType.code)
    for code_reference_tag in code_references:
        document, sections = parse_uri(cast(str, code_reference_tag['data-uri']))

        if document.title is None:
            raise ValueError('Could not find code title')
        code_id = get_code_id_with_title(document.title)
        if code_id is None:
            raise ValueError(f'Could not find code id for title {document.title}')
        
        update_reference_tag_uri(code_reference_tag, dataclass_replace(document, id=code_id), *sections)

    return new_children