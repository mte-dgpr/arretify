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

from arretify.utils.html_create import make_segmentation_tag
from arretify.utils.testing import create_document_context
from .parse_arrete import parse_arrete
from .testing import make_text_spans, assert_elements_equal


class BaseTestCase(unittest.TestCase):
    def setUp(self):
        self.context = create_document_context()
        self.soup = self.context.soup


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
                make_segmentation_tag(
                    self.soup,
                    "header",
                    contents=[
                        make_segmentation_tag(self.soup, "page_separator"),
                        make_segmentation_tag(
                            self.soup,
                            "arrete_title",
                            contents=make_text_spans(self.soup, "Arrêté n° 123"),
                        ),
                    ],
                ),
                make_segmentation_tag(
                    self.soup,
                    "main",
                    contents=[
                        make_segmentation_tag(
                            self.soup,
                            "section",
                            contents=[
                                make_segmentation_tag(
                                    self.soup,
                                    "section_title",
                                    contents=make_text_spans(self.soup, "Article 1 : Disposition"),
                                ),
                                make_segmentation_tag(
                                    self.soup,
                                    "alinea",
                                    contents=make_text_spans(self.soup, "Bla bla bla ..."),
                                ),
                            ],
                        ),
                    ],
                ),
                make_segmentation_tag(
                    self.soup,
                    "appendix",
                    contents=[
                        make_segmentation_tag(
                            self.soup,
                            "section",
                            contents=[
                                make_segmentation_tag(
                                    self.soup,
                                    "section_title",
                                    contents=make_text_spans(self.soup, "Annexe 1 : Détails"),
                                ),
                                make_segmentation_tag(
                                    self.soup,
                                    "alinea",
                                    contents=make_text_spans(self.soup, "Bla bla bla ..."),
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
                make_segmentation_tag(
                    self.soup,
                    "header",
                    contents=[
                        make_segmentation_tag(self.soup, "page_separator"),
                        make_segmentation_tag(
                            self.soup,
                            "arrete_title",
                            contents=make_text_spans(self.soup, "Arrêté n° 123"),
                        ),
                    ],
                ),
                make_segmentation_tag(
                    self.soup,
                    "main",
                    contents=[
                        make_segmentation_tag(
                            self.soup,
                            "section",
                            contents=[
                                make_segmentation_tag(
                                    self.soup,
                                    "section_title",
                                    contents=make_text_spans(self.soup, "Article 1 : Disposition"),
                                ),
                                make_segmentation_tag(
                                    self.soup,
                                    "alinea",
                                    contents=[
                                        make_segmentation_tag(
                                            self.soup,
                                            "text_span",
                                            contents=[
                                                "Bla bla, ",
                                                make_segmentation_tag(
                                                    self.soup,
                                                    "address",
                                                    contents=["123 rue de la Paix"],
                                                ),
                                                ", bla ...",
                                            ],
                                        )
                                    ],
                                ),
                            ],
                        ),
                    ],
                ),
            ],
            ignore_data_if_omitted=True,
            ignore_text_span_data=True,
        )
