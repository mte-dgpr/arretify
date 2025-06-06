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
from typing import List, cast, Dict
from dataclasses import replace as dataclass_replace
import logging

from bs4 import Tag

from arretify.types import (
    DocumentContext,
    SectionType,
)
from arretify.law_data.types import Section
from arretify.law_data.uri import parse_uri
from arretify.law_data.legifrance_constants import (
    get_code_id_with_title,
    get_code_article_id_from_article_num,
)

from .core import update_reference_tag_uri


_LOGGER = logging.getLogger(__name__)


def resolve_code_article_legifrance_id(
    document_context: DocumentContext,
    code_article_reference_tag: Tag,
) -> None:
    document, sections = parse_uri(cast(str, code_article_reference_tag["data-uri"]))
    if not document.is_resolvable:
        return

    if document.id is None:
        raise RuntimeError("Code document id is None")

    resolved_sections: List[Section] = []
    for section in sections:
        if section.type == SectionType.ARTICLE:
            new_fields: Dict[str, str | None] = dict(
                start_id=None,
                end_id=None,
            )

            for num_key, id_key in (
                ("start_num", "start_id"),
                ("end_num", "end_id"),
            ):
                if getattr(section, num_key) is not None:
                    article_id = get_code_article_id_from_article_num(
                        document.id, getattr(section, num_key)
                    )
                    if article_id:
                        new_fields[id_key] = article_id
                    else:
                        _LOGGER.warning(
                            f"Could not find legifrance article id for "
                            f"code {document.id} article {getattr(section, num_key)}"
                        )

            section = dataclass_replace(
                section,
                start_id=new_fields["start_id"],
                end_id=new_fields["end_id"],
            )

        resolved_sections.append(section)

    update_reference_tag_uri(code_article_reference_tag, document, *resolved_sections)


def resolve_code_legifrance_id(
    document_context: DocumentContext,
    code_reference_tag: Tag,
) -> None:
    document, sections = parse_uri(cast(str, code_reference_tag["data-uri"]))

    if document.title is None:
        raise ValueError("Could not find code title")
    code_id = get_code_id_with_title(document.title)
    if code_id is None:
        raise ValueError(f"Could not find code id for title {document.title}")

    update_reference_tag_uri(
        code_reference_tag,
        dataclass_replace(document, id=code_id),
        *sections,
    )
