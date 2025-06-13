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
from typing import Iterator, Tuple, List

from bs4 import Tag

from arretify.types import DocumentContext
from arretify.law_data.types import DocumentType, Section, Document
from arretify.utils.html import make_css_class, is_tag_and_matches
from arretify.html_schemas import DOCUMENT_REFERENCE_SCHEMA, SECTION_REFERENCE_SCHEMA
from arretify.step_references_detection.match_sections_with_documents import (
    build_reference_tree,
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


DOCUMENT_REFERENCE_CSS_CLASS = make_css_class(DOCUMENT_REFERENCE_SCHEMA)
SECTION_REFERENCE_CSS_CLASS = make_css_class(SECTION_REFERENCE_SCHEMA)


def step_legifrance_references_resolution(
    document_context: DocumentContext,
) -> DocumentContext:
    for document_reference_tag in iter_document_references(document_context):
        document = Document.from_tag(document_reference_tag)
        if document.type is DocumentType.arrete_ministeriel:
            resolve_arrete_ministeriel_legifrance_id(document_context, document_reference_tag)
        elif document.type is DocumentType.decret:
            resolve_decret_legifrance_id(document_context, document_reference_tag)
        elif document.type is DocumentType.circulaire:
            resolve_circulaire_legifrance_id(document_context, document_reference_tag)
        elif document.type is DocumentType.code:
            resolve_code_legifrance_id(document_context, document_reference_tag)
            for section_reference_tag, document, sections in iter_section_references(
                document_reference_tag
            ):
                resolve_code_article_legifrance_id(
                    document_context, section_reference_tag, document, sections
                )
        else:
            continue
    return document_context


def step_eurlex_references_resolution(document_context: DocumentContext) -> DocumentContext:
    for document_reference_tag in iter_document_references(document_context):
        document = Document.from_tag(document_reference_tag)
        if document.type is DocumentType.eu_decision:
            resolve_eu_decision_eurlex_url(document_context, document_reference_tag)
        elif document.type is DocumentType.eu_regulation:
            resolve_eu_regulation_eurlex_url(document_context, document_reference_tag)
        elif document.type is DocumentType.eu_directive:
            resolve_eu_directive_eurlex_url(document_context, document_reference_tag)
        else:
            continue
    return document_context


def iter_document_references(
    document_context: DocumentContext,
) -> Iterator[Tag]:
    for document_reference_tag in document_context.soup.select(f".{DOCUMENT_REFERENCE_CSS_CLASS}"):
        assert isinstance(document_reference_tag, Tag) is True
        yield document_reference_tag


def iter_section_references(
    document_reference_tag: Tag,
) -> Iterator[Tuple[Tag, Document, List[Section]]]:
    document = Document.from_tag(document_reference_tag)
    reference_branches = build_reference_tree(document_reference_tag)
    seen: List[Tag] = []
    for branch in reference_branches:
        sections: list[Section] = []
        for section_reference_tag in branch[1:]:
            if not is_tag_and_matches(
                section_reference_tag, css_classes_in=[SECTION_REFERENCE_CSS_CLASS]
            ):
                raise ValueError(f"Unexpected tag in reference branch: {section_reference_tag}")

            # Avoid handling the same section multiple times
            if any([section_reference_tag is other_tag for other_tag in seen]):
                sections.append(Section.from_tag(section_reference_tag))
                continue

            seen.append(section_reference_tag)
            sections.append(Section.from_tag(section_reference_tag))
            yield section_reference_tag, document, sections
