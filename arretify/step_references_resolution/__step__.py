from arretify.types import ParsingContext
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


def step_legifrance_references_resolution(
    parsing_context: ParsingContext,
) -> ParsingContext:
    # Resolve all document references
    resolve_document_references(
        parsing_context,
        DocumentType.arrete_ministeriel,
        resolve_arrete_ministeriel_legifrance_id,
    )
    resolve_document_references(parsing_context, DocumentType.decret, resolve_decret_legifrance_id)
    resolve_document_references(
        parsing_context,
        DocumentType.circulaire,
        resolve_circulaire_legifrance_id,
    )
    resolve_document_references(parsing_context, DocumentType.code, resolve_code_legifrance_id)

    # Resolve all section references
    add_referenced_document_DEPRECATED(parsing_context)
    resolve_section_references(
        parsing_context, DocumentType.code, resolve_code_article_legifrance_id
    )

    return parsing_context


def step_eurlex_references_resolution(parsing_context: ParsingContext) -> ParsingContext:
    resolve_document_references(
        parsing_context, DocumentType.eu_decision, resolve_eu_decision_eurlex_url
    )
    resolve_document_references(
        parsing_context,
        DocumentType.eu_regulation,
        resolve_eu_regulation_eurlex_url,
    )
    resolve_document_references(
        parsing_context,
        DocumentType.eu_directive,
        resolve_eu_directive_eurlex_url,
    )

    add_referenced_document_DEPRECATED(parsing_context)

    return parsing_context
