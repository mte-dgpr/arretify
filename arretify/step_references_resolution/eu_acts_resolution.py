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

from arretify.law_data.apis.eurlex import ActType, get_eu_act_url_with_year_and_num
from arretify.semantic_tag_specs import DocumentReferenceSpec
from arretify.types import DocumentContext, ProtectedTag
from arretify.utils.html_semantic import get_semantic_tag_data

from .core import update_document_reference_tag_href

_LOGGER = logging.getLogger(__name__)


def resolve_eu_decision_eurlex_url(
    document_context: DocumentContext,
    eu_act_reference_tag: ProtectedTag,
) -> None:
    return _resolve_eu_act_eurlex_url(document_context, "decision", eu_act_reference_tag)


def resolve_eu_regulation_eurlex_url(
    document_context: DocumentContext,
    eu_act_reference_tag: ProtectedTag,
) -> None:
    return _resolve_eu_act_eurlex_url(document_context, "regulation", eu_act_reference_tag)


def resolve_eu_directive_eurlex_url(
    document_context: DocumentContext,
    eu_act_reference_tag: ProtectedTag,
) -> None:
    return _resolve_eu_act_eurlex_url(document_context, "directive", eu_act_reference_tag)


def _resolve_eu_act_eurlex_url(
    document_context: DocumentContext,
    act_type: ActType,
    eu_act_reference_tag: ProtectedTag,
) -> None:
    document_reference = get_semantic_tag_data(DocumentReferenceSpec, eu_act_reference_tag)

    if document_reference.num is None or document_reference.date is None:
        raise ValueError(f"Could not find num or date for document {document_reference}")

    eurlex_url = get_eu_act_url_with_year_and_num(
        document_context, act_type, int(document_reference.date), int(document_reference.num)
    )
    if eurlex_url is None:
        _LOGGER.warning(
            f"Could not find eurlex url for {act_type} "
            f"{document_reference.date}/{document_reference.num}"
        )
        return

    update_document_reference_tag_href(
        eu_act_reference_tag,
        id=eurlex_url,
    )
