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
from pydantic import field_validator

from arretify.semantic_tag_specs import (
    AlineaData,
    ArreteTitleSpec,
    EmblemSpec,
    EntitySpec,
    HonorarySpec,
    IdentificationSpec,
    SupplementaryMotifInfoSpec,
    TableOfContentsSpec,
)
from arretify.utils.html_semantic import (
    Contents,
    IntList,
    SemanticTagData,
    SemanticTagSpec,
    create_semantic_tag_spec_no_data,
)

SEGMENTATION_TAG_NAME = "arretify-segmentation"
"""
Name of the tag used for segmentation tags.
"""


# -------------------- Basic elements -------------------- #


class TextSpanSegmentationData(SemanticTagData):
    start: IntList
    end: IntList

    @field_validator("start", "end")
    @classmethod
    def validate_3_elements(cls, value: IntList) -> IntList:
        if len(value) != 3:
            raise ValueError(
                f"Fields 'start' and 'end' must have exactly 3 elements (got {len(value)})"
            )
        return value


TextSpanSegmentationSpec: SemanticTagSpec[TextSpanSegmentationData] = SemanticTagSpec(
    spec_name="segmentation:text_span",
    tag_name=SEGMENTATION_TAG_NAME,
    data_model=TextSpanSegmentationData,
    allowed_contents=(Contents.Str(),),
)


TableSegmentationSpec = create_semantic_tag_spec_no_data(
    spec_name="segmentation:table",
    tag_name=SEGMENTATION_TAG_NAME,
    allowed_contents=(Contents.SemanticTag(TextSpanSegmentationSpec.spec_name),),
)


TableDescriptionSegmentationSpec = create_semantic_tag_spec_no_data(
    spec_name="segmentation:table_description",
    tag_name=SEGMENTATION_TAG_NAME,
    allowed_contents=(Contents.SemanticTag(TextSpanSegmentationSpec.spec_name),),
)


ListSegmentationSpec = create_semantic_tag_spec_no_data(
    spec_name="segmentation:list",
    tag_name=SEGMENTATION_TAG_NAME,
    allowed_contents=(
        Contents.SemanticTag(TextSpanSegmentationSpec.spec_name),
        Contents.SemanticTag("segmentation:list"),
    ),
)


BlockquoteSegmentationSpec = create_semantic_tag_spec_no_data(
    spec_name="segmentation:blockquote",
    tag_name=SEGMENTATION_TAG_NAME,
    allowed_contents=(
        Contents.SemanticTag(TextSpanSegmentationSpec.spec_name),
        Contents.SemanticTag(ListSegmentationSpec.spec_name),
        Contents.SemanticTag(TableSegmentationSpec.spec_name),
        Contents.SemanticTag(TableDescriptionSegmentationSpec.spec_name),
        Contents.Tag("img"),
    ),
)

# -------------------- Header -------------------- #

VisaSegmentationSpec = create_semantic_tag_spec_no_data(
    spec_name="segmentation:visa",
    tag_name=SEGMENTATION_TAG_NAME,
    allowed_contents=(
        Contents.SemanticTag(TextSpanSegmentationSpec.spec_name),
        Contents.SemanticTag(ListSegmentationSpec.spec_name),
    ),
)


MotifSegmentationSpec = create_semantic_tag_spec_no_data(
    spec_name="segmentation:motifs",
    tag_name=SEGMENTATION_TAG_NAME,
    allowed_contents=(
        Contents.SemanticTag(TextSpanSegmentationSpec.spec_name),
        Contents.SemanticTag(ListSegmentationSpec.spec_name),
    ),
)


HeaderSegmentationSpec = create_semantic_tag_spec_no_data(
    spec_name="segmentation:header",
    tag_name=SEGMENTATION_TAG_NAME,
    allowed_contents=(
        Contents.SemanticTag(EmblemSpec.spec_name),
        Contents.SemanticTag(EntitySpec.spec_name),
        Contents.SemanticTag(IdentificationSpec.spec_name),
        Contents.SemanticTag(ArreteTitleSpec.spec_name),
        Contents.SemanticTag(HonorarySpec.spec_name),
        Contents.SemanticTag(VisaSegmentationSpec.spec_name),
        Contents.SemanticTag(MotifSegmentationSpec.spec_name),
        Contents.SemanticTag(SupplementaryMotifInfoSpec.spec_name),
        # For lines in the header that havent been recognized as a particular element
        Contents.SemanticTag(TextSpanSegmentationSpec.spec_name),
        Contents.SemanticTag(TableOfContentsSpec.spec_name),
        Contents.Tag("img"),
    ),
)


# -------------------- Main + appendix structure -------------------- #


class SectionTitleSegmentationData(SemanticTagData):
    number: str | None = None
    type: str | None = None
    level: int | None = None
    title: str | None = None


SectionTitleSegmentationSpec: SemanticTagSpec[SectionTitleSegmentationData] = SemanticTagSpec(
    spec_name="segmentation:section_title",
    tag_name=SEGMENTATION_TAG_NAME,
    data_model=SectionTitleSegmentationData,
    allowed_contents=(Contents.SemanticTag(TextSpanSegmentationSpec.spec_name),),
)


AlineaSegmentationSpec: SemanticTagSpec[AlineaData] = SemanticTagSpec(
    spec_name="segmentation:alinea",
    tag_name=SEGMENTATION_TAG_NAME,
    data_model=AlineaData,
    allowed_contents=(
        Contents.SemanticTag(TextSpanSegmentationSpec.spec_name),
        Contents.SemanticTag(ListSegmentationSpec.spec_name),
        Contents.SemanticTag(TableSegmentationSpec.spec_name),
        Contents.SemanticTag(TableDescriptionSegmentationSpec.spec_name),
        Contents.SemanticTag(BlockquoteSegmentationSpec.spec_name),
        Contents.Tag("img"),
    ),
)


SectionSegmentationSpec = create_semantic_tag_spec_no_data(
    spec_name="segmentation:section",
    tag_name=SEGMENTATION_TAG_NAME,
    allowed_contents=(
        Contents.SemanticTag(SectionTitleSegmentationSpec.spec_name),
        Contents.SemanticTag(AlineaSegmentationSpec.spec_name),
        Contents.SemanticTag("segmentation:section"),
        # Table of contents can be included in appendix sections
        Contents.SemanticTag(TableOfContentsSpec.spec_name),
    ),
)


MainSegmentationSpec = create_semantic_tag_spec_no_data(
    spec_name="segmentation:main",
    tag_name=SEGMENTATION_TAG_NAME,
    allowed_contents=(Contents.SemanticTag(SectionSegmentationSpec.spec_name),),
)


AppendixSegmentationSpec = create_semantic_tag_spec_no_data(
    spec_name="segmentation:appendix",
    tag_name=SEGMENTATION_TAG_NAME,
    allowed_contents=(Contents.SemanticTag(SectionSegmentationSpec.spec_name),),
)
