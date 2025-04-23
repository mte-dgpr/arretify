from bs4 import BeautifulSoup

from arretify.law_data.types import DocumentType

from .core import (
    resolve_document_references,
    resolve_section_references,
)
from .codes_resolution import (
    resolve_code_article_legifrance_id,
    resolve_code_legifrance_id,
)
from .arretes_resolution import (
    resolve_arrete_ministeriel_legifrance_id,
)
from .decrets_resolution import (
    resolve_decret_legifrance_id,
)
from .circulaires_resolution import (
    resolve_circulaire_legifrance_id,
)
from .eu_acts_resolution import (
    resolve_eu_decision_eurlex_url,
    resolve_eu_directive_eurlex_url,
    resolve_eu_regulation_eurlex_url,
)
from .add_referenced_document import add_referenced_document_DEPRECATED


def step_references_resolution(soup: BeautifulSoup) -> BeautifulSoup:
    # Resolve all document references
    resolve_document_references(
        soup,
        DocumentType.arrete_ministeriel,
        resolve_arrete_ministeriel_legifrance_id,
    )
    resolve_document_references(soup, DocumentType.decret, resolve_decret_legifrance_id)
    resolve_document_references(
        soup,
        DocumentType.circulaire,
        resolve_circulaire_legifrance_id,
    )
    resolve_document_references(soup, DocumentType.code, resolve_code_legifrance_id)
    resolve_document_references(soup, DocumentType.eu_decision, resolve_eu_decision_eurlex_url)
    resolve_document_references(
        soup,
        DocumentType.eu_regulation,
        resolve_eu_regulation_eurlex_url,
    )
    resolve_document_references(
        soup,
        DocumentType.eu_directive,
        resolve_eu_directive_eurlex_url,
    )

    add_referenced_document_DEPRECATED(soup)

    # Resolve all section references
    resolve_section_references(soup, DocumentType.code, resolve_code_article_legifrance_id)

    return soup
