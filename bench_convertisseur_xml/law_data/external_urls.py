from typing import Union

from clients_api_droit.legifrance import authenticate, search_arrete, build_arrete_site_url, build_code_site_url, build_code_article_site_url

from bench_convertisseur_xml.law_data.types import Document, DocumentType, Section, SectionType
from bench_convertisseur_xml.types import ExternalURL

def resolve_external_url(
    document: Document,
    *sections: Section,
) -> ExternalURL | None:
    if document.type == DocumentType.arrete_ministeriel:
        if document.id is not None:
            return build_arrete_site_url(document.id)
    
    elif document.type == DocumentType.code:
        if document.id is None:
            return None

        elif (
            sections 
            and sections[0].type == SectionType.article 
            and sections[0].start_id is not None
        ):
            return build_code_article_site_url(sections[0].start_id)
        
        else:
            return build_code_site_url(document.id)
    
    return None