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
from arretify.utils.html_semantic import (
    IntList,
    SemanticTagSpec,
    SemanticTagData,
    create_semantic_tag_spec_no_data,
)

SEGMENTATION_TAG_NAME = "arretify-segmentation"
"""
Name of the tag used for segmentation tags.
"""


TableSegmentationSpec = create_semantic_tag_spec_no_data(
    spec_name="segmentation:table",
    tag_name=SEGMENTATION_TAG_NAME,
)


TableDescriptionSegmentationSpec = create_semantic_tag_spec_no_data(
    spec_name="segmentation:table_description",
    tag_name=SEGMENTATION_TAG_NAME,
)


ListSegmentationSpec = create_semantic_tag_spec_no_data(
    spec_name="segmentation:list",
    tag_name=SEGMENTATION_TAG_NAME,
)


BlockquoteSegmentationSpec = create_semantic_tag_spec_no_data(
    spec_name="segmentation:blockquote",
    tag_name=SEGMENTATION_TAG_NAME,
)


ImageSegmentationSpec = create_semantic_tag_spec_no_data(
    spec_name="segmentation:image",
    tag_name=SEGMENTATION_TAG_NAME,
)


class TextSpanSegmentationData(SemanticTagData):
    """Data model for text_span segmentation tags."""

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
)


class SectionTitleSegmentationData(SemanticTagData):
    number: str | None = None
    type: str | None = None
    level: int | None = None
    title: str | None = None


SectionTitleSegmentationSpec: SemanticTagSpec[SectionTitleSegmentationData] = SemanticTagSpec(
    spec_name="segmentation:section_title",
    tag_name=SEGMENTATION_TAG_NAME,
    data_model=SectionTitleSegmentationData,
)


SectionSegmentationSpec = create_semantic_tag_spec_no_data(
    spec_name="segmentation:section",
    tag_name=SEGMENTATION_TAG_NAME,
)
