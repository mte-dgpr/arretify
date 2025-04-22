from arretify._vendor.clients_api_droit.clients_api_droit.legifrance import (
    build_jorf_url,
    build_code_site_url,
    build_code_article_site_url,
)

from arretify.law_data.types import (
    Document,
    DocumentType,
    Section,
    SectionType,
)
from arretify.types import ExternalURL


def resolve_external_url(
    document: Document,
    *sections: Section,
) -> ExternalURL | None:
    if document.type in [
        DocumentType.arrete_ministeriel,
        DocumentType.decret,
        DocumentType.circulaire,
    ]:
        if document.id is not None:
            return build_jorf_url(document.id)

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

    elif document.type in [
        DocumentType.eu_decision,
        DocumentType.eu_regulation,
        DocumentType.eu_directive,
    ]:
        return document.id

    return None
