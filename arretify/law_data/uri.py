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
from typing import (
    Union,
    List,
)
import urllib.parse

from arretify.types import URI, SectionType
from .types import Section, Document, DocumentType


_SEPARATOR = "_"
URI_SCHEME = "dsr"


def render_uri(
    document: Document,
    *sections: Section,
) -> URI:
    _validate_sections(list(sections))

    # dsr://<type>_<id>_<num>_<date>_<title>
    document_part = _join_tokens(
        document.type.value,
        document.id,
        document.num,
        document.date,
        document.title,
    )

    # Format for articles and alineas part : /<type>_<start_id>_<start_num>_<end_id>_<end_num>
    path = ""
    for section in sections:
        section_part = _join_tokens(
            section.type.value,
            section.start_id,
            section.start_num,
            section.end_id,
            section.end_num,
        )
        path += f"/{section_part}"

    return f"{URI_SCHEME}://{document_part}{path}"


def parse_uri(uri: URI) -> tuple[Document, List[Section]]:
    scheme_part, rest = uri.split("://", 1)
    if scheme_part != URI_SCHEME:
        raise ValueError(f'Unsupported URI scheme "{scheme_part}"')

    document: Union[Document, None] = None
    document_part, *section_parts = rest.split("/")
    tokens = _split_tokens(document_part)
    if len(tokens) != 5:
        raise ValueError(f'Invalid document part "{document_part}"')
    document_type_value, id, num, date, title = tokens
    document = Document(
        type=DocumentType(document_type_value),
        id=id,
        num=num,
        date=date,
        title=title,
    )

    sections: List[Section] = []
    for section_part in section_parts:
        tokens = _split_tokens(section_part)
        if len(tokens) != 5:
            raise ValueError(f'Invalid section part "{section_part}"')
        section_type, start_id, start_num, end_id, end_num = tokens
        sections.append(
            Section(
                type=SectionType(section_type),
                start_id=start_id,
                start_num=start_num,
                end_id=end_id,
                end_num=end_num,
            )
        )

    _validate_sections(list(sections))
    return document, sections


def is_uri_document_type(uri: URI, document_type: DocumentType) -> bool:
    return uri.startswith(f"{URI_SCHEME}://{document_type.value}")


def _validate_sections(sections: List[Section]) -> None:
    allowed_section_types = list(SectionType)
    for i, section in enumerate(sections):
        if i < len(sections) - 1:
            if section.end_id is not None or section.end_num is not None:
                raise ValueError("End is allowed only for last section")

        # Unknown section type is allowed at any position
        if i > 0 and section.type != SectionType.UNKNOWN:
            previous_section = sections[i - 1]
            previous_section_type_index = allowed_section_types.index(previous_section.type)
            section_type_index = allowed_section_types.index(section.type)
            if section_type_index < previous_section_type_index:
                raise ValueError(
                    f'Section type "{section.type}" is not allowed after "{previous_section.type}"'
                )


def _join_tokens(*tokens: Union[str, None]) -> str:
    return _SEPARATOR.join([_encode(token) if token else "" for token in tokens])


def _split_tokens(part: str) -> List[Union[str, None]]:
    return [_decode(token) or None for token in part.split(_SEPARATOR)]


def _decode(part: str) -> str:
    return urllib.parse.unquote(part)


def _encode(part: str) -> str:
    _assert_allowed_chars(part)
    return urllib.parse.quote(part, safe="")


def _assert_allowed_chars(raw_part: str) -> None:
    if _SEPARATOR in raw_part:
        raise ValueError(f'"{_SEPARATOR}" is not allowed in the part')
