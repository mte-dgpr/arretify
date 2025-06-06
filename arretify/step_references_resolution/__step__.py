#
# Copyright (c) 2025 Direction générale de la prévention des risques (DGPR).
#
# This file is part of Arrêtify.
# See https://github.com/mte-dgpr/arretify for further info.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from arretify.types import DocumentContext
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
    document_context: DocumentContext,
) -> DocumentContext:
    # Resolve all document references
    resolve_document_references(
        document_context,
        DocumentType.arrete_ministeriel,
        resolve_arrete_ministeriel_legifrance_id,
    )
    resolve_document_references(document_context, DocumentType.decret, resolve_decret_legifrance_id)
    resolve_document_references(
        document_context,
        DocumentType.circulaire,
        resolve_circulaire_legifrance_id,
    )
    resolve_document_references(document_context, DocumentType.code, resolve_code_legifrance_id)

    # Resolve all section references
    add_referenced_document_DEPRECATED(document_context)
    resolve_section_references(
        document_context, DocumentType.code, resolve_code_article_legifrance_id
    )

    return document_context


def step_eurlex_references_resolution(document_context: DocumentContext) -> DocumentContext:
    resolve_document_references(
        document_context, DocumentType.eu_decision, resolve_eu_decision_eurlex_url
    )
    resolve_document_references(
        document_context,
        DocumentType.eu_regulation,
        resolve_eu_regulation_eurlex_url,
    )
    resolve_document_references(
        document_context,
        DocumentType.eu_directive,
        resolve_eu_directive_eurlex_url,
    )

    add_referenced_document_DEPRECATED(document_context)

    return document_context
