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

from arretify._vendor.clients_api_droit.clients_api_droit.legifrance import (
    build_code_article_site_url,
    build_code_site_url,
    build_jorf_url,
)
from arretify.regex_utils import PatternProxy, safe_group
from arretify.semantic_tag_specs import (
    DocumentReferenceData,
    DocumentReferenceSpec,
    SectionReferenceData,
    SectionReferenceSpec,
)
from arretify.types import DocumentType, ExternalURL, ProtectedTag, SectionType
from arretify.utils.html import set_attribute
from arretify.utils.html_semantic import set_semantic_tag_data, update_semantic_tag_data

# Regex for searching an act with its title.
# Simply picks the first 3 to 15 words following the document reference.
TITLE_SAMPLE_PATTERN = PatternProxy(r"^\s*([^\.;\s]+\s+){3,15}([^\.;\s]+)")


def resolve_external_url(
    document_reference: DocumentReferenceData,
    *section_references: SectionReferenceData,
) -> ExternalURL | None:
    if document_reference.type in [
        DocumentType.arrete_ministeriel,
        DocumentType.decret,
        DocumentType.circulaire,
    ]:
        if document_reference.id is not None:
            return build_jorf_url(document_reference.id)

    elif document_reference.type == DocumentType.code:
        if document_reference.id is None:
            return None

        elif (
            section_references
            and section_references[0].type == SectionType.ARTICLE
            and section_references[0].start_id is not None
        ):
            return build_code_article_site_url(section_references[0].start_id)

        else:
            return build_code_site_url(document_reference.id)

    elif document_reference.type in [
        DocumentType.eu_decision,
        DocumentType.eu_regulation,
        DocumentType.eu_directive,
    ]:
        return document_reference.id

    return None


def update_document_reference_tag_href(
    tag: ProtectedTag,
    id: str,
) -> None:
    document_reference = update_semantic_tag_data(DocumentReferenceSpec, tag, id=id)
    external_url = resolve_external_url(document_reference)
    if external_url is not None:
        set_attribute(tag, "href", external_url)


def update_section_reference_tag_href(
    tag: ProtectedTag,
    document_reference: DocumentReferenceData,
    *section_references: SectionReferenceData,
) -> None:
    set_semantic_tag_data(SectionReferenceSpec, tag, section_references[-1])
    external_url = resolve_external_url(document_reference, *section_references)
    if external_url is not None:
        set_attribute(tag, "href", external_url)


def get_title_sample_next_sibling(
    document_reference_tag: ProtectedTag,
) -> str | None:
    title_element = document_reference_tag.next_sibling
    if title_element is None or not isinstance(title_element, str):
        return None

    match = TITLE_SAMPLE_PATTERN.match(title_element)
    if match:
        return safe_group(match, 0)
    return None
