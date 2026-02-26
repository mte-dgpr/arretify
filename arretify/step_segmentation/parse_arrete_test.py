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
from arretify.semantic_tag_specs import (
    AddressSpec,
    AlineaData,
    ArreteTitleSpec,
    PageSeparatorData,
    PageSeparatorSpec,
)
from arretify.utils.html_create import wrap_in_tag

from .parse_arrete import parse_arrete
from .semantic_tag_specs import (
    AlineaSegmentationSpec,
    AppendixSegmentationSpec,
    HeaderSegmentationSpec,
    MainSegmentationSpec,
    SectionSegmentationSpec,
    SectionTitleSegmentationData,
    SectionTitleSegmentationSpec,
    TextSpanSegmentationSpec,
)
from .testing import (
    DEFAULT_TEXT_SPAN_DATA,
    BaseTestCaseSegmentation,
    assert_segmentation_element_lists_equal,
)


class TestParseArrete(BaseTestCaseSegmentation):

    def test_simple(self):
        # Arrange
        elements = [
            *self.make_text_spans(
                "Arrêté n° 123",
                "Article 1 : Disposition",
            ),
            self.make_semantic_tag(PageSeparatorSpec, data=PageSeparatorData(page_index=1)),
            *self.make_text_spans(
                "Bla bla bla ...",
                "Annexe 1 : Détails",
                "Bla bla bla ...",
            ),
        ]

        # Act
        elements = parse_arrete(self.context, elements)

        # Assert
        assert_segmentation_element_lists_equal(
            elements,
            [
                self.make_semantic_tag(
                    HeaderSegmentationSpec,
                    contents=[
                        self.make_semantic_tag(
                            ArreteTitleSpec,
                            contents=wrap_in_tag(self.soup, "h1", ["Arrêté n° 123"]),
                        ),
                    ],
                ),
                self.make_semantic_tag(
                    MainSegmentationSpec,
                    contents=[
                        self.make_semantic_tag(
                            SectionSegmentationSpec,
                            contents=[
                                self.make_semantic_tag(
                                    SectionTitleSegmentationSpec,
                                    contents=self.make_text_spans("Article 1 : Disposition"),
                                    data=SectionTitleSegmentationData(
                                        number="1",
                                        type="article",
                                        level=0,
                                        title="Disposition",
                                    ),
                                ),
                                self.make_semantic_tag(
                                    PageSeparatorSpec, data=PageSeparatorData(page_index=1)
                                ),
                                self.make_semantic_tag(
                                    AlineaSegmentationSpec,
                                    contents=self.make_text_spans("Bla bla bla ..."),
                                    data=AlineaData(number=1),
                                ),
                            ],
                        ),
                    ],
                ),
                self.make_semantic_tag(
                    AppendixSegmentationSpec,
                    contents=[
                        self.make_semantic_tag(
                            SectionSegmentationSpec,
                            contents=[
                                self.make_semantic_tag(
                                    SectionTitleSegmentationSpec,
                                    contents=self.make_text_spans("Annexe 1 : Détails"),
                                    data=SectionTitleSegmentationData(
                                        number="1",
                                        type="annexe",
                                        level=0,
                                        title="Détails",
                                    ),
                                ),
                                self.make_semantic_tag(
                                    AlineaSegmentationSpec,
                                    contents=self.make_text_spans("Bla bla bla ..."),
                                    data=AlineaData(number=1),
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        )

    def test_parse_text_span_inline_content_tags(self):
        # Arrange
        elements = self.make_text_spans(
            "Arrêté n° 123",
            "Article 1 : Disposition",
            # This address should be parsed as an address
            # tag inside a text_span
            "Bla bla, 123 rue de la Paix, bla ...",
        )

        # Act
        elements = parse_arrete(self.context, elements)

        # Assert
        assert_segmentation_element_lists_equal(
            elements,
            [
                self.make_semantic_tag(
                    HeaderSegmentationSpec,
                    contents=[
                        self.make_semantic_tag(
                            ArreteTitleSpec,
                            contents=wrap_in_tag(self.soup, "h1", ["Arrêté n° 123"]),
                        ),
                    ],
                ),
                self.make_semantic_tag(
                    MainSegmentationSpec,
                    contents=[
                        self.make_semantic_tag(
                            SectionSegmentationSpec,
                            contents=[
                                self.make_semantic_tag(
                                    SectionTitleSegmentationSpec,
                                    contents=self.make_text_spans("Article 1 : Disposition"),
                                    data=SectionTitleSegmentationData(
                                        number="1",
                                        type="article",
                                        level=0,
                                        title="Disposition",
                                    ),
                                ),
                                self.make_semantic_tag(
                                    AlineaSegmentationSpec,
                                    contents=[
                                        self.make_semantic_tag(
                                            TextSpanSegmentationSpec,
                                            contents=[
                                                "Bla bla, ",
                                                self.make_semantic_tag(
                                                    AddressSpec,
                                                    contents=["123 rue de la Paix"],
                                                ),
                                                ", bla ...",
                                            ],
                                            data=DEFAULT_TEXT_SPAN_DATA,
                                        )
                                    ],
                                    data=AlineaData(number=1),
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        )
