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

from typing import Annotated, Literal

from pydantic import model_validator

from arretify.types import DocumentType, OperationType, ProtectedSoup, ProtectedTag, SectionType
from arretify.utils.dates import parse_date_str, parse_year_str
from arretify.utils.html_create import make_tag
from arretify.utils.html_semantic import (
    Bool,
    Contents,
    SemanticTagData,
    SemanticTagSpec,
    StrList,
    create_semantic_tag_spec_no_data,
    enum_serializer,
)

# -------------------- Page structure -------------------- #


PageFooterSpec = create_semantic_tag_spec_no_data(
    spec_name="page_footer",
    tag_name="div",
    allowed_contents=(Contents.Tag("div"),),
    is_allowed_anywhere=True,
)


class PageSeparatorData(SemanticTagData):
    page_index: int


PageSeparatorSpec: SemanticTagSpec[PageSeparatorData] = SemanticTagSpec(
    spec_name="page_separator",
    tag_name="a",
    data_model=PageSeparatorData,
    is_allowed_anywhere=True,
)


# -------------------- Generic elements -------------------- #


DateSpec = create_semantic_tag_spec_no_data(
    spec_name="date",
    tag_name="time",
    allowed_contents=(Contents.Str(),),
    is_allowed_anywhere=True,
)


AddressSpec = create_semantic_tag_spec_no_data(
    spec_name="address",
    tag_name="address",
    allowed_contents=(Contents.Str(),),
    is_allowed_anywhere=True,
)


TableOfContentsSpec = create_semantic_tag_spec_no_data(
    spec_name="table_of_contents",
    tag_name="div",
    allowed_contents=(Contents.Tag("div"),),
)


ErrorSpec = create_semantic_tag_spec_no_data(
    spec_name="error",
    tag_name="div",
    is_allowed_anywhere=True,
    allowed_contents=None,  # Any content is allowed
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


DocumentReferenceSpec: SemanticTagSpec[DocumentReferenceData] = SemanticTagSpec(
    spec_name="document_reference",
    tag_name="a",
    data_model=DocumentReferenceData,
    allowed_contents=(Contents.Str(),),
    is_allowed_anywhere=True,
)


class SectionReferenceData(SemanticTagData):
    type: Annotated[SectionType, enum_serializer] | None = None
    parent_reference: str | None = None
    start_num: str | None = None
    start_id: str | None = None
    end_id: str | None = None
    end_num: str | None = None


SectionReferenceSpec: SemanticTagSpec[SectionReferenceData] = SemanticTagSpec(
    spec_name="section_reference",
    tag_name="a",
    data_model=SectionReferenceData,
    allowed_contents=(Contents.Str(),),
    is_allowed_anywhere=True,
)


# -------------------- Operations -------------------- #


class OperationData(SemanticTagData):
    operation_type: Annotated[OperationType, enum_serializer]
    direction: Literal["ltr", "rtl"]
    references: StrList | None = None
    keyword: str
    has_operand: Bool = False
    operand: str | None = None


OperationSpec: SemanticTagSpec[OperationData] = SemanticTagSpec(
    spec_name="operation",
    tag_name="span",
    data_model=OperationData,
    allowed_contents=(Contents.Str(),),
    is_allowed_anywhere=True,
)

# -------------------- Header -------------------- #


EmblemSpec = create_semantic_tag_spec_no_data(
    spec_name="emblem",
    tag_name="div",
    allowed_contents=(Contents.Tag("div"),),
)

EntitySpec = create_semantic_tag_spec_no_data(
    spec_name="entity",
    tag_name="div",
    allowed_contents=(Contents.Tag("div"),),
)

IdentificationSpec = create_semantic_tag_spec_no_data(
    spec_name="identification",
    tag_name="div",
    allowed_contents=(Contents.Tag("div"),),
)

ArreteTitleSpec = create_semantic_tag_spec_no_data(
    spec_name="arrete_title",
    tag_name="div",
    allowed_contents=(Contents.Tag("h1"),),
)

HonorarySpec = create_semantic_tag_spec_no_data(
    spec_name="honorary",
    tag_name="div",
    allowed_contents=(Contents.Tag("div"),),
)

VisaSpec = create_semantic_tag_spec_no_data(
    spec_name="visa",
    tag_name="div",
    allowed_contents=(
        Contents.Str(),
        Contents.Tag("ul"),
    ),
)

MotifSpec = create_semantic_tag_spec_no_data(
    spec_name="motifs",
    tag_name="div",
    allowed_contents=(
        Contents.Str(),
        Contents.Tag("ul"),
    ),
)

SupplementaryMotifInfoSpec = create_semantic_tag_spec_no_data(
    spec_name="supplementary_motif_info",
    tag_name="div",
    allowed_contents=(Contents.Tag("div"),),
)

HeaderSpec = create_semantic_tag_spec_no_data(
    spec_name="header",
    tag_name="header",
    allowed_contents=(
        Contents.SemanticTag(EmblemSpec.spec_name),
        Contents.SemanticTag(EntitySpec.spec_name),
        Contents.SemanticTag(IdentificationSpec.spec_name),
        Contents.SemanticTag(ArreteTitleSpec.spec_name),
        Contents.SemanticTag(HonorarySpec.spec_name),
        Contents.SemanticTag(VisaSpec.spec_name),
        Contents.SemanticTag(MotifSpec.spec_name),
        Contents.SemanticTag(SupplementaryMotifInfoSpec.spec_name),
        Contents.SemanticTag(TableOfContentsSpec.spec_name),
        # For lines in the header that havent been recognized as a particular element
        Contents.Tag("div"),
        Contents.Tag("img"),
    ),
)


# -------------------- Main + appendix structure -------------------- #


class SectionTitleData(SemanticTagData):
    level: int


# Starts at h2, because h1 is used for the main title of the arrete.
# For level > h6, we use div with aria-level attribute.
def _make_section_title_tag(soup: ProtectedSoup, data: SectionTitleData) -> ProtectedTag:
    document_level = data.level + 2
    if data.level <= 4:
        return make_tag(soup, f"h{document_level}")
    else:
        tag = make_tag(soup, "div", attrs={"aria-level": str(document_level), "role": "heading"})
        return tag


SectionTitleSpec: SemanticTagSpec[SectionTitleData] = SemanticTagSpec(
    spec_name="section_title",
    tag_name=_make_section_title_tag,
    data_model=SectionTitleData,
    allowed_contents=(Contents.Str(),),
)


class AlineaData(SemanticTagData):
    number: int


AlineaSpec: SemanticTagSpec[AlineaData] = SemanticTagSpec(
    spec_name="alinea",
    tag_name="div",
    data_model=AlineaData,
    allowed_contents=(
        Contents.Str(),
        Contents.Tag("ul"),
        Contents.Tag("table"),
        Contents.Tag("blockquote"),
        Contents.Tag("q"),
        Contents.Tag("img"),
    ),
)


class SectionData(SemanticTagData):
    title: str | None
    number: str
    type: str


SectionSpec: SemanticTagSpec[SectionData] = SemanticTagSpec(
    spec_name="section",
    tag_name="section",
    data_model=SectionData,
    allowed_contents=(
        Contents.SemanticTag("section_title"),
        Contents.SemanticTag(AlineaSpec.spec_name),
        Contents.SemanticTag("section"),
        # Table of contents can be included in appendix sections
        Contents.SemanticTag(TableOfContentsSpec.spec_name),
    ),
)

MainSpec = create_semantic_tag_spec_no_data(
    spec_name="main",
    tag_name="main",
    allowed_contents=(Contents.SemanticTag(SectionSpec.spec_name),),
)

AppendixSpec = create_semantic_tag_spec_no_data(
    spec_name="appendix",
    tag_name="footer",
    allowed_contents=(Contents.SemanticTag(SectionSpec.spec_name),),
)


# -------------------- Arrete -------------------- #
class ArreteData(SemanticTagData):
    input_name: str | None = None
    arretify_version: str


ArreteSpec: SemanticTagSpec[ArreteData] = SemanticTagSpec(
    spec_name="arrete",
    tag_name="body",
    data_model=ArreteData,
    allowed_contents=(
        Contents.SemanticTag(HeaderSpec.spec_name),
        Contents.SemanticTag(MainSpec.spec_name),
        Contents.SemanticTag(AppendixSpec.spec_name),
    ),
)
