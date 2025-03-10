from typing import Union

from clients_api_droit.legifrance import authenticate, search_arrete, build_arrete_site_url, build_code_site_url

from .legifrance import find_code_id_with_title
from bench_convertisseur_xml.law_data.types import Document, Section, ArreteMinisterielDocument, CodeDocument
from bench_convertisseur_xml.types import ExternalURL

def resolve_external_url(
    document: Union[Document, None],
    *sections: Section,
) -> ExternalURL | None:
    if isinstance(document, ArreteMinisterielDocument):
        return build_arrete_site_url(document.legifrance_id)
    elif isinstance(document, CodeDocument):
        code_id = find_code_id_with_title(document.title)
        if code_id is not None and len(sections) == 0:
            return build_code_site_url(code_id)
    return None

    