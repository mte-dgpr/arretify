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

from arretify.semantic_tag_specs import DocumentReferenceSpec
from arretify.types import DocumentContext, DocumentType
from arretify.utils.html_semantic import css_selector, get_semantic_tag_data
from arretify.utils.references import build_and_traverse_reference_tree

from .arretes_resolution import resolve_arrete_ministeriel_legifrance_id
from .circulaires_resolution import resolve_circulaire_legifrance_id
from .codes_resolution import resolve_code_article_legifrance_id, resolve_code_legifrance_id
from .decrets_resolution import resolve_decret_legifrance_id
from .eu_acts_resolution import (
    resolve_eu_decision_eurlex_url,
    resolve_eu_directive_eurlex_url,
    resolve_eu_regulation_eurlex_url,
)


def step_legifrance_references_resolution(
    document_context: DocumentContext,
) -> DocumentContext:
    for document_reference_tag in document_context.protected_soup.select(
        css_selector(DocumentReferenceSpec)
    ):
        document_reference = get_semantic_tag_data(DocumentReferenceSpec, document_reference_tag)
        if document_reference.type is DocumentType.arrete_ministeriel:
            resolve_arrete_ministeriel_legifrance_id(document_context, document_reference_tag)
        elif document_reference.type is DocumentType.decret:
            resolve_decret_legifrance_id(document_context, document_reference_tag)
        elif document_reference.type is DocumentType.circulaire:
            resolve_circulaire_legifrance_id(document_context, document_reference_tag)
        elif document_reference.type is DocumentType.code:
            resolve_code_legifrance_id(document_context, document_reference_tag)
            for (
                section_reference_tag,
                resolved_document,
                sections,
            ) in build_and_traverse_reference_tree(document_reference_tag):
                # We assume document is not None here, since built the tree from
                # a document reference tag.
                assert resolved_document is not None
                if sections:
                    resolve_code_article_legifrance_id(
                        document_context, section_reference_tag, resolved_document, sections
                    )
        else:
            continue
    return document_context


def step_eurlex_references_resolution(document_context: DocumentContext) -> DocumentContext:
    for document_reference_tag in document_context.protected_soup.select(
        css_selector(DocumentReferenceSpec)
    ):
        document = get_semantic_tag_data(DocumentReferenceSpec, document_reference_tag)
        if document.type is DocumentType.eu_decision:
            resolve_eu_decision_eurlex_url(document_context, document_reference_tag)
        elif document.type is DocumentType.eu_regulation:
            resolve_eu_regulation_eurlex_url(document_context, document_reference_tag)
        elif document.type is DocumentType.eu_directive:
            resolve_eu_directive_eurlex_url(document_context, document_reference_tag)
        else:
            continue
    return document_context
