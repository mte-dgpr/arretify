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

from arretify.utils.testing import create_document_context
from arretify.utils.html_semantic import make_semantic_tag
from arretify.semantic_tag_specs import (
    AlineaData,
    HeaderSpec,
    MainSpec,
    AppendixSpec,
    PageSeparatorData,
    PageSeparatorSpec,
    ArreteSpec,
    AlineaSpec,
    AddressSpec,
)
from .semantic_tag_specs import (
    SectionSegmentationSpec,
    SectionTitleSegmentationData,
    SectionTitleSegmentationSpec,
    TextSpanSegmentationData,
    TextSpanSegmentationSpec,
)
from .parse_arrete import parse_arrete
from .testing import make_text_spans, assert_elements_equal


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
                    HeaderSpec,
                    contents=[
                        make_semantic_tag(
                            self.soup, PageSeparatorSpec, data=PageSeparatorData(page_index=0)
                        ),
                        make_semantic_tag(
                            self.soup,
                            ArreteSpec,
                            contents=make_text_spans(self.soup, "Arrêté n° 123"),
                        ),
                    ],
                ),
                make_semantic_tag(
                    self.soup,
                    MainSpec,
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
                                    AlineaSpec,
                                    contents=make_text_spans(self.soup, "Bla bla bla ..."),
                                    data=AlineaData(number=1),
                                ),
                            ],
                        ),
                    ],
                ),
                make_semantic_tag(
                    self.soup,
                    AppendixSpec,
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
                                    AlineaSpec,
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
                    HeaderSpec,
                    contents=[
                        make_semantic_tag(
                            self.soup, PageSeparatorSpec, data=PageSeparatorData(page_index=0)
                        ),
                        make_semantic_tag(
                            self.soup,
                            ArreteSpec,
                            contents=make_text_spans(self.soup, "Arrêté n° 123"),
                        ),
                    ],
                ),
                make_semantic_tag(
                    self.soup,
                    MainSpec,
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
                                    AlineaSpec,
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
