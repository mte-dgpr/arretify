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
from dataclasses import replace as dataclass_replace
import logging

from bs4 import Tag

from arretify.parsing_utils.dates import parse_date_str
from arretify.types import DocumentContext
from arretify.law_data.apis.legifrance import (
    get_decret_legifrance_id,
)
from arretify.law_data.types import Document
from arretify.errors import catch_and_log_arretify_error
from .core import (
    update_document_reference_tag_href,
    get_title_sample_next_sibling,
)


_LOGGER = logging.getLogger(__name__)


@catch_and_log_arretify_error(_LOGGER)
def resolve_decret_legifrance_id(
    document_context: DocumentContext,
    document_reference_tag: Tag,
) -> None:
    document = Document.from_tag(document_reference_tag)

    if document.date is None:
        _LOGGER.warning(f"Decret {document} has no date")
        return

    title = get_title_sample_next_sibling(document_reference_tag)
    if title is None and document.num is None:
        _LOGGER.warning(f"Could not resolve decret {document_reference_tag}. No title or num")
        return

    date_object = parse_date_str(document.date)
    decret_id = get_decret_legifrance_id(
        document_context,
        date_object,
        title=title,
        num=document.num,
    )
    if decret_id is None:
        _LOGGER.warning(
            f"Could not find legifrance decret id for "
            f'date {date_object}{' n°' + document.num if document.num else ''} "{title}"'
        )
        return

    update_document_reference_tag_href(
        document_reference_tag,
        dataclass_replace(
            document,
            id=decret_id,
        ),
    )
