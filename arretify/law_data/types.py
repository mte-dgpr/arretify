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
from typing import Union, Optional, cast
from dataclasses import dataclass
from enum import Enum

from bs4 import Tag

from arretify.types import SectionType, DataElementDataDict
from arretify.parsing_utils.dates import (
    parse_date_str,
    parse_year_str,
)
from arretify.utils.html import render_str_list_attribute, parse_str_list_attribute


class DocumentType(Enum):
    unknown = "unknown"

    self = "self"
    """Self reference"""

    unknown_arrete = "arrete"
    arrete_prefectoral = "arrete-prefectoral"
    arrete_ministeriel = "arrete-ministeriel"
    decret = "decret"
    circulaire = "circulaire"
    code = "code"
    """Code juridique (https://www.legifrance.gouv.fr/liste/code)"""

    eu_regulation = "eu-regulation"
    """
    EU regulation. (https://style-guide.europa.eu &
    https://style-guide.europa.eu/fr/content/-/isg/topic?identifier=1.2.1-classification-of-acts)
    """

    eu_directive = "eu-directive"
    """
    EU directive. (https://style-guide.europa.eu &
    https://style-guide.europa.eu/fr/content/-/isg/topic?identifier=1.2.1-classification-of-acts)
    """

    eu_decision = "eu-decision"
    """
    EU decision. (https://style-guide.europa.eu &
    https://style-guide.europa.eu/fr/content/-/isg/topic?identifier=1.2.1-classification-of-acts)
    """


@dataclass(frozen=True, kw_only=True)
class Document:
    type: DocumentType
    id: Optional[str] = None
    """External identifier of the document. For example, legifrance id or CELEX."""
    num: Optional[str] = None
    """
    Code, number, or other identifier of the document.
    For example, the number of a directive or arrete code.
    """
    date: Optional[str] = None
    """Date of the document. Format: YYYY-MM-DD or YYYY"""
    title: Optional[str] = None
    """Title of the document or guessed title from parsing the text."""

    def __post_init__(self):
        if self.date:
            if self.type in [
                DocumentType.eu_decision,
                DocumentType.eu_directive,
                DocumentType.eu_regulation,
            ]:
                try:
                    parse_year_str(self.date)
                except ValueError:
                    raise ValueError(f'Invalid year "{self.date}"')
            else:
                try:
                    parse_date_str(self.date)
                except ValueError:
                    raise ValueError(f'Invalid date "{self.date}"')

    def get_data_attributes(self) -> DataElementDataDict:
        """Returns a dictionary of data attributes for this document."""
        return {
            "type": self.type.value,
            "id": self.id,
            "num": self.num,
            "date": self.date,
            "title": self.title,
        }

    @classmethod
    def from_tag(cls, tag: Tag) -> "Document":
        return cls(
            type=DocumentType(tag["data-type"]),
            id=cast(str | None, tag.get("data-id", None)),
            num=cast(str | None, tag.get("data-num", None)),
            date=cast(str | None, tag.get("data-date", None)),
            title=cast(str | None, tag.get("data-title", None)),
        )


@dataclass(frozen=True, kw_only=True)
class Section:
    type: SectionType
    start_num: Union[str, None] = None
    end_num: Union[str, None] = None
    start_id: Union[str, None] = None
    end_id: Union[str, None] = None

    def get_data_attributes(self) -> DataElementDataDict:
        """Returns a dictionary of data attributes for this section."""
        id_attr = None
        if self.start_id or self.end_id:
            id_attr = render_str_list_attribute([self.start_id or "", self.end_id or ""])

        num_attr = None
        if self.start_num or self.end_num:
            num_attr = render_str_list_attribute([self.start_num or "", self.end_num or ""])

        return {
            "type": self.type.value,
            "id": id_attr,
            "num": num_attr,
        }

    @classmethod
    def from_tag(cls, tag: Tag) -> "Section":
        start_num, end_num = parse_str_list_attribute(cast(str, tag.get("data-num", ",")))
        start_id, end_id = parse_str_list_attribute(cast(str, tag.get("data-id", ",")))
        return cls(
            type=SectionType(tag["data-type"]),
            start_num=start_num or None,
            start_id=start_id or None,
            end_num=end_num or None,
            end_id=end_id or None,
        )
