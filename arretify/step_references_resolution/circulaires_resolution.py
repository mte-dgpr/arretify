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

from arretify.errors import catch_and_log_arretify_error
from arretify.law_data.apis.legifrance import get_circulaire_legifrance_id
from arretify.semantic_tag_specs import DocumentReferenceSpec
from arretify.types import DocumentContext, ProtectedTag
from arretify.utils.dates import parse_date_str
from arretify.utils.html_semantic import get_semantic_tag_data

from .core import get_title_sample_next_sibling, update_document_reference_tag_href

_LOGGER = logging.getLogger(__name__)


@catch_and_log_arretify_error(_LOGGER)
def resolve_circulaire_legifrance_id(
    document_context: DocumentContext,
    document_reference_tag: ProtectedTag,
) -> None:
    document_reference = get_semantic_tag_data(DocumentReferenceSpec, document_reference_tag)

    if document_reference.date is None:
        _LOGGER.warning(f"Circulaire {document_reference} has no date")
        return

    title = get_title_sample_next_sibling(document_reference_tag)
    if title is None:
        _LOGGER.warning(f"Circulaire {document_reference} has no title")
        return

    date_object = parse_date_str(document_reference.date)
    circulaire_id = get_circulaire_legifrance_id(
        document_context,
        date_object,
        title,
    )
    if circulaire_id is None:
        _LOGGER.warning(
            f"Could not find legifrance circulaire id for " f'date {date_object} "{title}"'
        )
        return

    update_document_reference_tag_href(
        document_reference_tag,
        id=circulaire_id,
    )
