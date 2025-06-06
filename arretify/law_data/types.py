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
from typing import Union, Optional
from dataclasses import dataclass
from enum import Enum

from arretify.types import SectionType
from arretify.parsing_utils.dates import (
    parse_date_str,
    parse_year_str,
)


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


@dataclass(frozen=True)
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

    @property
    def is_resolvable(self) -> bool:
        if self.type == DocumentType.self:
            return True
        elif self.type in [
            DocumentType.unknown,
            DocumentType.unknown_arrete,
        ]:
            return False
        else:
            return self.id is not None

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


@dataclass(frozen=True)
class Section:
    type: SectionType
    start_id: Union[str, None] = None
    start_num: Union[str, None] = None
    end_id: Union[str, None] = None
    end_num: Union[str, None] = None

    @property
    def is_resolvable(self) -> bool:
        if self.type == SectionType.ARTICLE:
            if self.start_id is None:
                return False
            if self.end_num:
                return self.end_id is not None
            return True
        else:
            return True
