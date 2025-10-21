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

from pydantic import model_validator
from typing import Annotated, Literal

from arretify.utils.dates import (
    parse_date_str,
    parse_year_str,
)
from arretify.types import DocumentType
from arretify.utils.html_semantic import (
    SemanticTagSpec,
    SemanticTagData,
    Bool,
    StrList,
    enum_serializer,
)
from arretify.types import OperationType, SectionType


# -------------------- Parts -------------------- #


HeaderSpec = SemanticTagSpec(
    spec_name="header",
    tag_name="header",
)

MainSpec = SemanticTagSpec(
    spec_name="main",
    tag_name="main",
)

AppendixSpec = SemanticTagSpec(
    spec_name="appendix",
    tag_name="footer",
)


# -------------------- Document -------------------- #


PageFooterSpec = SemanticTagSpec(
    spec_name="page_footer",
    tag_name="div",
)


class PageSeparatorData(SemanticTagData):
    page_index: int


PageSeparatorSpec = SemanticTagSpec(
    spec_name="page_separator",
    tag_name="a",
    data_model=PageSeparatorData,
)

TableOfContentsSpec = SemanticTagSpec(
    spec_name="table_of_contents",
    tag_name="div",
)


# -------------------- Header -------------------- #


EmblemSpec = SemanticTagSpec(
    spec_name="emblem",
    tag_name="div",
)

EntitySpec = SemanticTagSpec(
    spec_name="entity",
    tag_name="div",
)

IdentificationSpec = SemanticTagSpec(
    spec_name="identification",
    tag_name="div",
)

ArreteSpec = SemanticTagSpec(
    spec_name="arrete_title",
    tag_name="div",
)

HonorarySpec = SemanticTagSpec(
    spec_name="honorary",
    tag_name="div",
)

VisaSpec = SemanticTagSpec(
    spec_name="visa",
    tag_name="div",
)

MotifSpec = SemanticTagSpec(
    spec_name="motifs",
    tag_name="div",
)

SupplementaryMotifInfoSpec = SemanticTagSpec(
    spec_name="supplementary_motif_info",
    tag_name="div",
)


# -------------------- Main and appendix -------------------- #


class SectionData(SemanticTagData):
    title: str | None
    number: str
    type: str


SectionSpec = SemanticTagSpec(
    spec_name="section",
    tag_name="section",
    data_model=SectionData,
)

SectionTitle1Spec = SemanticTagSpec(
    spec_name="section_title",
    tag_name="h2",
)

SectionTitle2Spec = SemanticTagSpec(
    spec_name="section_title",
    tag_name="h3",
)

SectionTitle3Spec = SemanticTagSpec(
    spec_name="section_title",
    tag_name="h4",
)

SectionTitle4Spec = SemanticTagSpec(
    spec_name="section_title",
    tag_name="h5",
)

SectionTitle5Spec = SemanticTagSpec(
    spec_name="section_title",
    tag_name="h6",
)

SectionTitle6Spec = SemanticTagSpec(
    spec_name="section_title",
    tag_name="h7",
)

SectionTitle7Spec = SemanticTagSpec(
    spec_name="section_title",
    tag_name="h8",
)


SectionTitleSpecs = [
    SectionTitle1Spec,
    SectionTitle2Spec,
    SectionTitle3Spec,
    SectionTitle4Spec,
    SectionTitle5Spec,
    SectionTitle6Spec,
    SectionTitle7Spec,
]


class AlineaData(SemanticTagData):
    number: str


AlineaSpec = SemanticTagSpec(
    spec_name="alinea",
    tag_name="div",
    data_model=AlineaData,
)


# -------------------- References -------------------- #


class DocumentReferenceData(SemanticTagData):
    type: Annotated[DocumentType, enum_serializer]
    id: str | None = None
    """External identifier of the document. For example, legifrance id or CELEX."""
    num: str | None = None
    """
    Code, number, or other identifier of the document.
    For example, the number of a directive or arrete code.
    """
    date: str | None = None
    """Date of the document. Format: YYYY-MM-DD or YYYY"""
    title: str | None = None
    """Title of the document or guessed title from parsing the text."""

    @model_validator(mode="after")
    def validate_date_and_type(self):
        date = self.date
        type_ = self.type
        if date is None:
            return self
        if type_ in [
            DocumentType.eu_decision,
            DocumentType.eu_directive,
            DocumentType.eu_regulation,
        ]:
            try:
                parse_year_str(date)
            except ValueError:
                raise ValueError(f'Invalid year "{date}"')
        else:
            try:
                parse_date_str(date)
            except ValueError:
                raise ValueError(f'Invalid date "{date}"')
        return self


DocumentReferenceSpec = SemanticTagSpec(
    spec_name="document_reference",
    tag_name="a",
    data_model=DocumentReferenceData,
)


class SectionReferenceData(SemanticTagData):
    type: Annotated[SectionType, enum_serializer] | None = None  # TODO:BETTER-TESTS
    parent_reference: str | None = None
    start_num: str | None = None  # TODO:BETTER-TESTS
    start_id: str | None = None
    end_id: str | None = None
    end_num: str | None = None


SectionReferenceSpec = SemanticTagSpec(
    spec_name="section_reference",
    tag_name="a",
    data_model=SectionReferenceData,
)

DateSpec = SemanticTagSpec(
    spec_name="date",
    tag_name="time",
)


# -------------------- Operations -------------------- #


class OperationData(SemanticTagData):
    operation_type: Annotated[OperationType, enum_serializer]
    direction: Literal["ltr", "rtl"]
    references: StrList | None = None
    keyword: str
    has_operand: Bool = False
    operand: str | None = None


OperationSpec = SemanticTagSpec(
    spec_name="operation",
    tag_name="span",
    data_model=OperationData,
)


# -------------------- Errors -------------------- #


ErrorSpec = SemanticTagSpec(
    spec_name="error",
    tag_name="span",
)
