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
import unittest

from arretify.semantic_tag_specs import (
    AddressSpec,
    AlineaData,
    ArreteTitleSpec,
    PageSeparatorData,
    PageSeparatorSpec,
)
from arretify.utils.html_create import make_semantic_tag, wrap_in_tag
from arretify.utils.testing import create_document_context

from .parse_arrete import initialize_document_structure, parse_arrete
from .semantic_tag_specs import (
    AlineaSegmentationSpec,
    AppendixSegmentationSpec,
    HeaderSegmentationSpec,
    MainSegmentationSpec,
    SectionSegmentationSpec,
    SectionTitleSegmentationData,
    SectionTitleSegmentationSpec,
    TextSpanSegmentationData,
    TextSpanSegmentationSpec,
)
from .testing import assert_elements_equal, make_text_spans


class BaseTestCase(unittest.TestCase):
    def setUp(self):
        self.context = create_document_context()
        self.soup = self.context.protected_soup


class TestParseArrete(BaseTestCase):

    def test_simple(self):
        # Arrange
        pages = [
            (
                "Arrêté n° 123\n"
                "Article 1 : Disposition\n"
                "Bla bla bla ...\n"
                "Annexe 1 : Détails\n"
                "Bla bla bla ...\n"
            )
        ]

        # Act
        elements = parse_arrete(self.context, pages)

        # Assert
        assert_elements_equal(
            elements,
            [
                make_semantic_tag(
                    self.soup,
                    HeaderSegmentationSpec,
                    contents=[
                        make_semantic_tag(
                            self.soup, PageSeparatorSpec, data=PageSeparatorData(page_index=0)
                        ),
                        make_semantic_tag(
                            self.soup,
                            ArreteTitleSpec,
                            contents=wrap_in_tag(self.soup, "h1", ["Arrêté n° 123"]),
                        ),
                    ],
                ),
                make_semantic_tag(
                    self.soup,
                    MainSegmentationSpec,
                    contents=[
                        make_semantic_tag(
                            self.soup,
                            SectionSegmentationSpec,
                            contents=[
                                make_semantic_tag(
                                    self.soup,
                                    SectionTitleSegmentationSpec,
                                    contents=make_text_spans(self.soup, "Article 1 : Disposition"),
                                    data=SectionTitleSegmentationData(
                                        number="1",
                                        type="article",
                                        level=0,
                                        title="Disposition",
                                    ),
                                ),
                                make_semantic_tag(
                                    self.soup,
                                    AlineaSegmentationSpec,
                                    contents=make_text_spans(self.soup, "Bla bla bla ..."),
                                    data=AlineaData(number=1),
                                ),
                            ],
                        ),
                    ],
                ),
                make_semantic_tag(
                    self.soup,
                    AppendixSegmentationSpec,
                    contents=[
                        make_semantic_tag(
                            self.soup,
                            SectionSegmentationSpec,
                            contents=[
                                make_semantic_tag(
                                    self.soup,
                                    SectionTitleSegmentationSpec,
                                    contents=make_text_spans(self.soup, "Annexe 1 : Détails"),
                                    data=SectionTitleSegmentationData(
                                        number="1",
                                        type="annexe",
                                        level=0,
                                        title="Détails",
                                    ),
                                ),
                                make_semantic_tag(
                                    self.soup,
                                    AlineaSegmentationSpec,
                                    contents=make_text_spans(self.soup, "Bla bla bla ..."),
                                    data=AlineaData(number=1),
                                ),
                            ],
                        ),
                    ],
                ),
            ],
            ignore_data_if_omitted=True,
            ignore_text_span_data=True,
        )

    def test_parse_text_span_inline_content_tags(self):
        # Arrange
        pages = [
            (
                "Arrêté n° 123\n"
                "Article 1 : Disposition\n"
                # This address should be parsed as an address
                # tag inside a text_span
                "Bla bla, 123 rue de la Paix, bla ..."
            )
        ]

        # Act
        elements = parse_arrete(self.context, pages)

        # Assert
        assert_elements_equal(
            elements,
            [
                make_semantic_tag(
                    self.soup,
                    HeaderSegmentationSpec,
                    contents=[
                        make_semantic_tag(
                            self.soup, PageSeparatorSpec, data=PageSeparatorData(page_index=0)
                        ),
                        make_semantic_tag(
                            self.soup,
                            ArreteTitleSpec,
                            contents=wrap_in_tag(self.soup, "h1", ["Arrêté n° 123"]),
                        ),
                    ],
                ),
                make_semantic_tag(
                    self.soup,
                    MainSegmentationSpec,
                    contents=[
                        make_semantic_tag(
                            self.soup,
                            SectionSegmentationSpec,
                            contents=[
                                make_semantic_tag(
                                    self.soup,
                                    SectionTitleSegmentationSpec,
                                    contents=make_text_spans(self.soup, "Article 1 : Disposition"),
                                    data=SectionTitleSegmentationData(
                                        number="1",
                                        type="article",
                                        level=0,
                                        title="Disposition",
                                    ),
                                ),
                                make_semantic_tag(
                                    self.soup,
                                    AlineaSegmentationSpec,
                                    contents=[
                                        make_semantic_tag(
                                            self.soup,
                                            TextSpanSegmentationSpec,
                                            contents=[
                                                "Bla bla, ",
                                                make_semantic_tag(
                                                    self.soup,
                                                    AddressSpec,
                                                    contents=["123 rue de la Paix"],
                                                ),
                                                ", bla ...",
                                            ],
                                            data=TextSpanSegmentationData(
                                                start=[0, 0, 0],
                                                end=[0, 0, 0],
                                            ),
                                        )
                                    ],
                                    data=AlineaData(number=1),
                                ),
                            ],
                        ),
                    ],
                ),
            ],
            ignore_data_if_omitted=True,
            ignore_text_span_data=True,
        )


class TestInitializeDocumentStructure(unittest.TestCase):

    def setUp(self):
        self.context = create_document_context()
        self.soup = self.context.protected_soup

    def test_page_separators_inserted_and_text_spans_created(self):
        # Arrange
        pages = [
            "Line 1\nLine 2\nLine 3",
            "Line 4\nLine 5",
            "Line 6",
        ]

        # Act
        result = initialize_document_structure(self.context, pages)

        # Assert
        assert_elements_equal(
            result,
            [
                make_semantic_tag(
                    self.soup, PageSeparatorSpec, data=PageSeparatorData(page_index=0)
                ),
                make_semantic_tag(
                    self.soup,
                    TextSpanSegmentationSpec,
                    contents=["Line 1"],
                    data=TextSpanSegmentationData(start=[0, 0, 0], end=[0, 0, 5]),
                ),
                make_semantic_tag(
                    self.soup,
                    TextSpanSegmentationSpec,
                    contents=["Line 2"],
                    data=TextSpanSegmentationData(start=[0, 1, 0], end=[0, 1, 5]),
                ),
                make_semantic_tag(
                    self.soup,
                    TextSpanSegmentationSpec,
                    contents=["Line 3"],
                    data=TextSpanSegmentationData(start=[0, 2, 0], end=[0, 2, 5]),
                ),
                make_semantic_tag(
                    self.soup, PageSeparatorSpec, data=PageSeparatorData(page_index=1)
                ),
                make_semantic_tag(
                    self.soup,
                    TextSpanSegmentationSpec,
                    contents=["Line 4"],
                    data=TextSpanSegmentationData(start=[1, 0, 0], end=[1, 0, 5]),
                ),
                make_semantic_tag(
                    self.soup,
                    TextSpanSegmentationSpec,
                    contents=["Line 5"],
                    data=TextSpanSegmentationData(start=[1, 1, 0], end=[1, 1, 5]),
                ),
                make_semantic_tag(
                    self.soup, PageSeparatorSpec, data=PageSeparatorData(page_index=2)
                ),
                make_semantic_tag(
                    self.soup,
                    TextSpanSegmentationSpec,
                    contents=["Line 6"],
                    data=TextSpanSegmentationData(start=[2, 0, 0], end=[2, 0, 5]),
                ),
            ],
        )
