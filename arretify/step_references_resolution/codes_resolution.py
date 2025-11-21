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
import logging
from typing import Sequence

from arretify.law_data.legifrance_constants import (
    get_code_article_id_from_article_num,
    get_code_id_with_title,
)
from arretify.semantic_tag_specs import (
    DocumentReferenceData,
    DocumentReferenceSpec,
    SectionReferenceData,
)
from arretify.types import DocumentContext, ProtectedTag, SectionType
from arretify.utils.html_semantic import get_semantic_tag_data, update_data

from .core import update_document_reference_tag_href, update_section_reference_tag_href

_LOGGER = logging.getLogger(__name__)


def resolve_code_article_legifrance_id(
    _: DocumentContext,
    code_article_reference_tag: ProtectedTag,
    document_reference: DocumentReferenceData,
    section_references: Sequence[SectionReferenceData],
) -> None:
    if document_reference.id is None:
        return

    resolved_section_references: list[SectionReferenceData] = []
    for section in section_references:
        if section.type == SectionType.ARTICLE:
            for num_key, id_key in (
                ("start_num", "start_id"),
                ("end_num", "end_id"),
            ):
                if getattr(section, num_key) is not None:
                    article_id = get_code_article_id_from_article_num(
                        document_reference.id, getattr(section, num_key)
                    )
                    if article_id:
                        section = update_data(
                            section,
                            **{id_key: article_id},
                        )
                    else:
                        _LOGGER.warning(
                            f"Could not find legifrance article id for "
                            f"code {document_reference.id} article {getattr(section, num_key)}"
                        )

        resolved_section_references.append(section)

    update_section_reference_tag_href(
        code_article_reference_tag,
        document_reference,
        *resolved_section_references,
    )


def resolve_code_legifrance_id(
    _: DocumentContext,
    code_reference_tag: ProtectedTag,
) -> None:
    document_reference = get_semantic_tag_data(DocumentReferenceSpec, code_reference_tag)
    if document_reference.title is None:
        raise ValueError("Could not find code title")
    code_id = get_code_id_with_title(document_reference.title)
    if code_id is None:
        raise ValueError(f"Could not find code id for title {document_reference.title}")

    update_document_reference_tag_href(
        code_reference_tag,
        id=code_id,
    )
