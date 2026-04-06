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
    PageSeparatorData,
    PageSeparatorSpec,
)

from .main_or_appendix import parse_alineas, parse_section_titles, parse_sections
from .semantic_tag_specs import (
    AlineaSegmentationSpec,
    SectionSegmentationSpec,
    SectionTitleSegmentationData,
    SectionTitleSegmentationSpec,
    TableDescriptionSegmentationSpec,
    TextSpanSegmentationData,
    TextSpanSegmentationSpec,
)
from .testing import BaseTestCaseSegmentation, assert_segmentation_element_lists_equal


class TestParseSectionTitles(BaseTestCaseSegmentation):

    def test_parse_section_titles(self):
        # Arrange
        elements = self.make_text_spans(
            "Titre I - Introduction",
            "1. Contexte",
            "bla bla bla",
            "2. Objectifs",
            "blo blo blo",
            "bli bli bli",
            "Titre II - Méthodologie",
            "blu blu blu",
            "ble ble ble",
        )

        # Act
        result = list(parse_section_titles(self.context, elements))

        # Assert
        assert_segmentation_element_lists_equal(
            result,
            [
                self.make_semantic_tag(
                    SectionTitleSegmentationSpec,
                    contents=self.make_text_spans("Titre I - Introduction"),
                    data=SectionTitleSegmentationData(
                        level=0,
                        number="I",
                        title="Introduction",
                        type="titre",
                    ),
                ),
                self.make_semantic_tag(
                    SectionTitleSegmentationSpec,
                    contents=self.make_text_spans("1. Contexte"),
                    data=SectionTitleSegmentationData(
                        level=1,
                        number="1",
                        title="Contexte",
                        type="unknown",
                    ),
                ),
                *self.make_text_spans("bla bla bla"),
                self.make_semantic_tag(
                    SectionTitleSegmentationSpec,
                    contents=self.make_text_spans("2. Objectifs"),
                    data=SectionTitleSegmentationData(
                        level=1,
                        number="2",
                        title="Objectifs",
                        type="unknown",
                    ),
                ),
                *self.make_text_spans(
                    "blo blo blo",
                    "bli bli bli",
                ),
                self.make_semantic_tag(
                    SectionTitleSegmentationSpec,
                    contents=self.make_text_spans("Titre II - Méthodologie"),
                    data=SectionTitleSegmentationData(
                        level=0,
                        number="II",
                        title="Méthodologie",
                        type="titre",
                    ),
                ),
                *self.make_text_spans(
                    "blu blu blu",
                    "ble ble ble",
                ),
            ],
        )

    def test_reject_text_span_starting_with_inline_tag(self):
        # Arrange
        elements = [
            *self.make_text_spans(
                "Titre I - Introduction",
            ),
            self.make_semantic_tag(
                TextSpanSegmentationSpec,
                contents=[
                    self.make_semantic_tag(
                        AddressSpec,
                        contents=["1 rue de l'avenir"],
                    )
                ],
                data=TextSpanSegmentationData(start=[0, 0, 0], end=[0, 0, 0]),
            ),
        ]

        # Act
        result = list(parse_section_titles(self.context, elements))

        # Assert
        assert_segmentation_element_lists_equal(
            result,
            [
                self.make_semantic_tag(
                    SectionTitleSegmentationSpec,
                    contents=self.make_text_spans("Titre I - Introduction"),
                    data=SectionTitleSegmentationData(
                        level=0,
                        number="I",
                        title="Introduction",
                        type="titre",
                    ),
                ),
                self.make_semantic_tag(
                    TextSpanSegmentationSpec,
                    contents=[
                        self.make_semantic_tag(
                            AddressSpec,
                            contents=["1 rue de l'avenir"],
                        )
                    ],
                    data=TextSpanSegmentationData(start=[0, 0, 0], end=[0, 0, 0]),
                ),
            ],
        )


class TestParseSections(BaseTestCaseSegmentation):

    def test_parse_sections(self):
        # Arrange
        elements = [
            *self.make_text_spans("bly bly bly"),
            self.make_semantic_tag(
                SectionTitleSegmentationSpec,
                contents=self.make_text_spans("Titre I - Introduction"),
                data=SectionTitleSegmentationData(level=1),
            ),
            self.make_semantic_tag(
                SectionTitleSegmentationSpec,
                contents=self.make_text_spans("1. Contexte"),
                data=SectionTitleSegmentationData(level=2),
            ),
            *self.make_text_spans("bla bla bla"),
            self.make_semantic_tag(
                SectionTitleSegmentationSpec,
                contents=self.make_text_spans("2. Objectifs"),
                data=SectionTitleSegmentationData(level=2),
            ),
            *self.make_text_spans(
                "blo blo blo",
                "bli bli bli",
            ),
            self.make_semantic_tag(
                SectionTitleSegmentationSpec,
                contents=self.make_text_spans("Titre II - Méthodologie"),
                data=SectionTitleSegmentationData(level=1),
            ),
            *self.make_text_spans(
                "blu blu blu",
                "ble ble ble",
            ),
        ]

        # Act
        result = parse_sections(self.context, elements, level=1)

        # Assert
        assert_segmentation_element_lists_equal(
            result,
            [
                self.make_semantic_tag(
                    AlineaSegmentationSpec,
                    contents=self.make_text_spans("bly bly bly"),
                    data=AlineaData(number="1"),
                ),
                self.make_semantic_tag(
                    SectionSegmentationSpec,
                    contents=[
                        self.make_semantic_tag(
                            SectionTitleSegmentationSpec,
                            contents=self.make_text_spans("Titre I - Introduction"),
                            data=SectionTitleSegmentationData(
                                level=1,
                            ),
                        ),
                        self.make_semantic_tag(
                            SectionSegmentationSpec,
                            contents=[
                                self.make_semantic_tag(
                                    SectionTitleSegmentationSpec,
                                    contents=self.make_text_spans("1. Contexte"),
                                    data=SectionTitleSegmentationData(
                                        level=2,
                                    ),
                                ),
                                self.make_semantic_tag(
                                    AlineaSegmentationSpec,
                                    contents=self.make_text_spans("bla bla bla"),
                                    data=AlineaData(number="1"),
                                ),
                            ],
                        ),
                        self.make_semantic_tag(
                            SectionSegmentationSpec,
                            contents=[
                                self.make_semantic_tag(
                                    SectionTitleSegmentationSpec,
                                    contents=self.make_text_spans("2. Objectifs"),
                                    data=SectionTitleSegmentationData(
                                        level=2,
                                    ),
                                ),
                                self.make_semantic_tag(
                                    AlineaSegmentationSpec,
                                    contents=self.make_text_spans("blo blo blo"),
                                    data=AlineaData(number="1"),
                                ),
                                self.make_semantic_tag(
                                    AlineaSegmentationSpec,
                                    contents=self.make_text_spans("bli bli bli"),
                                    data=AlineaData(number="2"),
                                ),
                            ],
                        ),
                    ],
                ),
                self.make_semantic_tag(
                    SectionSegmentationSpec,
                    contents=[
                        self.make_semantic_tag(
                            SectionTitleSegmentationSpec,
                            contents=self.make_text_spans("Titre II - Méthodologie"),
                            data=SectionTitleSegmentationData(
                                level=1,
                            ),
                        ),
                        self.make_semantic_tag(
                            AlineaSegmentationSpec,
                            contents=self.make_text_spans("blu blu blu"),
                            data=AlineaData(number="1"),
                        ),
                        self.make_semantic_tag(
                            AlineaSegmentationSpec,
                            contents=self.make_text_spans("ble ble ble"),
                            data=AlineaData(number="2"),
                        ),
                    ],
                ),
            ],
        )

    def test_parse_sections_contents(self):
        # Arrange
        elements = [
            self.make_semantic_tag(
                SectionTitleSegmentationSpec,
                contents=self.make_text_spans("1. Bla"),
                data=SectionTitleSegmentationData(level=0),
            ),
            *self.make_text_spans("bla bla bla"),
            self.make_semantic_tag(
                SectionTitleSegmentationSpec,
                contents=self.make_text_spans("1.1. Blabla"),
                data=SectionTitleSegmentationData(level=1),
            ),
            *self.make_text_spans("bli bli bli"),
        ]

        # Act
        result = parse_sections(self.context, elements, level=0)

        # Assert
        assert_segmentation_element_lists_equal(
            result,
            [
                self.make_semantic_tag(
                    SectionSegmentationSpec,
                    contents=[
                        self.make_semantic_tag(
                            SectionTitleSegmentationSpec,
                            contents=self.make_text_spans("1. Bla"),
                            data=SectionTitleSegmentationData(level=0),
                        ),
                        self.make_semantic_tag(
                            AlineaSegmentationSpec,
                            contents=self.make_text_spans("bla bla bla"),
                            data=AlineaData(number="1"),
                        ),
                        self.make_semantic_tag(
                            SectionSegmentationSpec,
                            contents=[
                                self.make_semantic_tag(
                                    SectionTitleSegmentationSpec,
                                    contents=self.make_text_spans("1.1. Blabla"),
                                    data=SectionTitleSegmentationData(level=1),
                                ),
                                self.make_semantic_tag(
                                    AlineaSegmentationSpec,
                                    contents=self.make_text_spans("bli bli bli"),
                                    data=AlineaData(number="1"),
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        )

    def test_parse_sections_missing_level(self):
        # Arrange
        elements = [
            self.make_semantic_tag(
                SectionTitleSegmentationSpec,
                contents=self.make_text_spans("1. Bla"),
                data=SectionTitleSegmentationData(level=0),
            ),
            self.make_semantic_tag(
                SectionTitleSegmentationSpec,
                contents=self.make_text_spans("1.1.1. Blabla"),
                data=SectionTitleSegmentationData(level=2),
            ),
        ]

        # Act
        result = parse_sections(self.context, elements, level=0)

        # Assert
        assert_segmentation_element_lists_equal(
            result,
            [
                self.make_semantic_tag(
                    SectionSegmentationSpec,
                    contents=[
                        self.make_semantic_tag(
                            SectionTitleSegmentationSpec,
                            contents=self.make_text_spans("1. Bla"),
                            data=SectionTitleSegmentationData(level=0),
                        ),
                        self.make_semantic_tag(
                            SectionSegmentationSpec,
                            contents=[
                                self.make_semantic_tag(
                                    SectionTitleSegmentationSpec,
                                    contents=self.make_text_spans("1.1.1. Blabla"),
                                    data=SectionTitleSegmentationData(level=2),
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        )

    def test_parse_missing_title_current_level(self):
        # Arrange
        elements = [
            self.make_semantic_tag(
                SectionTitleSegmentationSpec,
                contents=self.make_text_spans("1.1. bla"),
                data=SectionTitleSegmentationData(level=1),
            ),
            self.make_semantic_tag(
                SectionTitleSegmentationSpec,
                contents=self.make_text_spans("1.1.1. bla"),
                data=SectionTitleSegmentationData(level=2),
            ),
            self.make_semantic_tag(
                SectionTitleSegmentationSpec,
                contents=self.make_text_spans("1.2. bla"),
                data=SectionTitleSegmentationData(level=1),
            ),
            self.make_semantic_tag(
                SectionTitleSegmentationSpec,
                contents=self.make_text_spans("2. bla"),
                data=SectionTitleSegmentationData(level=0),
            ),
            self.make_semantic_tag(
                SectionTitleSegmentationSpec,
                contents=self.make_text_spans("2.1. bla"),
                data=SectionTitleSegmentationData(level=1),
            ),
        ]

        # Act
        result = parse_sections(self.context, elements, level=0)

        # Assert
        assert_segmentation_element_lists_equal(
            result,
            [
                self.make_semantic_tag(
                    SectionSegmentationSpec,
                    contents=[
                        self.make_semantic_tag(
                            SectionTitleSegmentationSpec,
                            contents=self.make_text_spans("1.1. bla"),
                            data=SectionTitleSegmentationData(level=1),
                        ),
                        self.make_semantic_tag(
                            SectionSegmentationSpec,
                            contents=[
                                self.make_semantic_tag(
                                    SectionTitleSegmentationSpec,
                                    contents=self.make_text_spans("1.1.1. bla"),
                                    data=SectionTitleSegmentationData(level=2),
                                ),
                            ],
                        ),
                    ],
                ),
                self.make_semantic_tag(
                    SectionSegmentationSpec,
                    contents=[
                        self.make_semantic_tag(
                            SectionTitleSegmentationSpec,
                            contents=self.make_text_spans("1.2. bla"),
                            data=SectionTitleSegmentationData(level=1),
                        ),
                    ],
                ),
                self.make_semantic_tag(
                    SectionSegmentationSpec,
                    contents=[
                        self.make_semantic_tag(
                            SectionTitleSegmentationSpec,
                            contents=self.make_text_spans("2. bla"),
                            data=SectionTitleSegmentationData(level=0),
                        ),
                        self.make_semantic_tag(
                            SectionSegmentationSpec,
                            contents=[
                                self.make_semantic_tag(
                                    SectionTitleSegmentationSpec,
                                    contents=self.make_text_spans("2.1. bla"),
                                    data=SectionTitleSegmentationData(level=1),
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        )


class TestParseAlineas(BaseTestCaseSegmentation):

    def test_merge_if_continuing_sentence_and_page_separator(self):
        # Arrange
        elements = [
            self.make_semantic_tag(
                TextSpanSegmentationSpec,
                contents=["This is a sentence that "],
                data=TextSpanSegmentationData(start=[0, 111, 0], end=[0, 111, 10]),
            ),
            self.make_semantic_tag(PageSeparatorSpec, data=PageSeparatorData(page_index=1)),
            self.make_semantic_tag(
                TextSpanSegmentationSpec,
                contents=["continues on the next page."],
                data=TextSpanSegmentationData(start=[1, 0, 0], end=[1, 0, 10]),
            ),
        ]

        # Act
        result = parse_alineas(self.context, elements)

        # Assert
        assert_segmentation_element_lists_equal(
            result,
            [
                self.make_semantic_tag(
                    AlineaSegmentationSpec,
                    contents=[
                        self.make_semantic_tag(
                            TextSpanSegmentationSpec,
                            contents=[
                                "This is a sentence that ",
                                self.make_semantic_tag(
                                    PageSeparatorSpec,
                                    data=PageSeparatorData(page_index=1),
                                ),
                                "continues on the next page.",
                            ],
                            data=TextSpanSegmentationData(start=[0, 111, 0], end=[1, 0, 10]),
                        )
                    ],
                    data=AlineaData(number=1),
                ),
            ],
        )

    def test_image_becomes_standalone_alinea(self):
        # Arrange
        img_tag = self.make_tag("img", attrs=dict(src="photo.png", alt="Photo"))
        elements = [
            *self.make_text_spans("bla bla bla"),
            img_tag,
            *self.make_text_spans("bli bli bli"),
        ]

        # Act
        result = parse_alineas(self.context, elements)

        # Assert
        assert_segmentation_element_lists_equal(
            result,
            [
                self.make_semantic_tag(
                    AlineaSegmentationSpec,
                    contents=self.make_text_spans("bla bla bla"),
                    data=AlineaData(number=1),
                ),
                self.make_semantic_tag(
                    AlineaSegmentationSpec,
                    contents=[img_tag],
                    data=AlineaData(number=2),
                ),
                self.make_semantic_tag(
                    AlineaSegmentationSpec,
                    contents=self.make_text_spans("bli bli bli"),
                    data=AlineaData(number=3),
                ),
            ],
        )

    def test_table_and_table_description_in_same_alinea(self):
        # Arrange
        elements = [
            self.make_tag("table"),
            *self.make_text_spans(
                "(*) Table description", "(**) More table description", "Some text"
            ),
        ]

        # Act
        result = parse_alineas(self.context, elements)

        # Assert
        assert_segmentation_element_lists_equal(
            result,
            [
                self.make_semantic_tag(
                    AlineaSegmentationSpec,
                    contents=[
                        self.make_tag("table"),
                        self.make_semantic_tag(
                            TableDescriptionSegmentationSpec,
                            contents=self.make_text_spans(
                                "(*) Table description",
                                "(**) More table description",
                            ),
                        ),
                    ],
                    data=AlineaData(number=1),
                ),
                self.make_semantic_tag(
                    AlineaSegmentationSpec,
                    contents=self.make_text_spans("Some text"),
                    data=AlineaData(number=2),
                ),
            ],
        )
