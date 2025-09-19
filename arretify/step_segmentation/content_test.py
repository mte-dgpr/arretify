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
from arretify.utils.testing import create_document_context, normalized_html_str
from .content import (
    parse_section_titles,
    parse_sections,
    parse_alineas,
    render_alinea,
    render_section_title,
    render_section,
)
from .testing import (
    assert_elements_equal,
    make_text_spans,
)


class BaseTestCase(unittest.TestCase):
    def setUp(self):
        self.context = create_document_context()
        self.soup = self.context.soup


class TestParseSectionTitles(BaseTestCase):

    def test_parse_section_titles(self):
        # Arrange
        elements = make_text_spans(
            self.soup,
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
        assert_elements_equal(
            result,
            [
                make_segmentation_tag(
                    self.soup,
                    "section_title",
                    contents=make_text_spans(self.soup, "Titre I - Introduction"),
                    data=dict(
                        level=0,
                        number="I",
                        title="Introduction",
                        type="titre",
                    ),
                ),
                make_segmentation_tag(
                    self.soup,
                    "section_title",
                    contents=make_text_spans(self.soup, "1. Contexte"),
                    data=dict(
                        level=1,
                        number="1",
                        title="Contexte",
                        type="unknown",
                    ),
                ),
                *make_text_spans(self.soup, "bla bla bla"),
                make_segmentation_tag(
                    self.soup,
                    "section_title",
                    contents=make_text_spans(self.soup, "2. Objectifs"),
                    data=dict(
                        level=1,
                        number="2",
                        title="Objectifs",
                        type="unknown",
                    ),
                ),
                *make_text_spans(
                    self.soup,
                    "blo blo blo",
                    "bli bli bli",
                ),
                make_segmentation_tag(
                    self.soup,
                    "section_title",
                    contents=make_text_spans(self.soup, "Titre II - Méthodologie"),
                    data=dict(
                        level=0,
                        number="II",
                        title="Méthodologie",
                        type="titre",
                    ),
                ),
                *make_text_spans(
                    self.soup,
                    "blu blu blu",
                    "ble ble ble",
                ),
            ],
            ignore_text_span_data=True,
        )

    def test_reject_text_span_starting_with_inline_tag(self):
        # Arrange
        elements = [
            *make_text_spans(
                self.soup,
                "Titre I - Introduction",
            ),
            make_segmentation_tag(
                self.soup,
                "text_span",
                contents=[
                    make_segmentation_tag(
                        self.soup,
                        "address",
                        contents=make_text_spans(self.soup, "1 rue de l'avenir"),
                    )
                ],
            ),
        ]

        # Act
        result = list(parse_section_titles(self.context, elements))

        # Assert
        assert_elements_equal(
            result,
            [
                make_segmentation_tag(
                    self.soup,
                    "section_title",
                    contents=make_text_spans(self.soup, "Titre I - Introduction"),
                    data=dict(
                        level=0,
                        number="I",
                        title="Introduction",
                        type="titre",
                    ),
                ),
                make_segmentation_tag(
                    self.soup,
                    "text_span",
                    contents=[
                        make_segmentation_tag(
                            self.soup,
                            "address",
                            contents=make_text_spans(self.soup, "1 rue de l'avenir"),
                        )
                    ],
                ),
            ],
            ignore_text_span_data=True,
        )


class TestParseSections(BaseTestCase):

    def test_parse_sections(self):
        # Arrange
        elements = [
            *make_text_spans(self.soup, "bly bly bly"),
            make_segmentation_tag(
                self.soup,
                "section_title",
                contents=make_text_spans(self.soup, "Titre I - Introduction"),
                data=dict(level=1),
            ),
            make_segmentation_tag(
                self.soup,
                "section_title",
                contents=make_text_spans(self.soup, "1. Contexte"),
                data=dict(level=2),
            ),
            *make_text_spans(self.soup, "bla bla bla"),
            make_segmentation_tag(
                self.soup,
                "section_title",
                contents=make_text_spans(self.soup, "2. Objectifs"),
                data=dict(level=2),
            ),
            *make_text_spans(
                self.soup,
                "blo blo blo",
                "bli bli bli",
            ),
            make_segmentation_tag(
                self.soup,
                "section_title",
                contents=make_text_spans(self.soup, "Titre II - Méthodologie"),
                data=dict(level=1),
            ),
            *make_text_spans(
                self.soup,
                "blu blu blu",
                "ble ble ble",
            ),
        ]

        # Act
        result = parse_sections(self.context, elements, level=1)

        # Assert
        assert_elements_equal(
            result,
            [
                make_segmentation_tag(
                    self.soup,
                    "alinea",
                    contents=make_text_spans(self.soup, "bly bly bly"),
                    data=dict(number="1"),
                ),
                make_segmentation_tag(
                    self.soup,
                    "section",
                    contents=[
                        make_segmentation_tag(
                            self.soup,
                            "section_title",
                            contents=make_text_spans(self.soup, "Titre I - Introduction"),
                        ),
                        make_segmentation_tag(
                            self.soup,
                            "section",
                            contents=[
                                make_segmentation_tag(
                                    self.soup,
                                    "section_title",
                                    contents=make_text_spans(self.soup, "1. Contexte"),
                                ),
                                make_segmentation_tag(
                                    self.soup,
                                    "alinea",
                                    contents=make_text_spans(self.soup, "bla bla bla"),
                                    data=dict(number="1"),
                                ),
                            ],
                        ),
                        make_segmentation_tag(
                            self.soup,
                            "section",
                            contents=[
                                make_segmentation_tag(
                                    self.soup,
                                    "section_title",
                                    contents=make_text_spans(self.soup, "2. Objectifs"),
                                ),
                                make_segmentation_tag(
                                    self.soup,
                                    "alinea",
                                    contents=make_text_spans(self.soup, "blo blo blo"),
                                    data=dict(number="1"),
                                ),
                                make_segmentation_tag(
                                    self.soup,
                                    "alinea",
                                    contents=make_text_spans(self.soup, "bli bli bli"),
                                    data=dict(number="2"),
                                ),
                            ],
                        ),
                    ],
                ),
                make_segmentation_tag(
                    self.soup,
                    "section",
                    contents=[
                        make_segmentation_tag(
                            self.soup,
                            "section_title",
                            contents=make_text_spans(self.soup, "Titre II - Méthodologie"),
                        ),
                        make_segmentation_tag(
                            self.soup,
                            "alinea",
                            contents=make_text_spans(self.soup, "blu blu blu"),
                            data=dict(number="1"),
                        ),
                        make_segmentation_tag(
                            self.soup,
                            "alinea",
                            contents=make_text_spans(self.soup, "ble ble ble"),
                            data=dict(number="2"),
                        ),
                    ],
                ),
            ],
            ignore_data_if_omitted=True,
            ignore_text_span_data=True,
        )

    def test_parse_sections_contents(self):
        # Arrange
        elements = [
            make_segmentation_tag(
                self.soup,
                "section_title",
                contents=["1. Bla"],
                data=dict(level=0),
            ),
            "bla bla bla",
            make_segmentation_tag(
                self.soup,
                "section_title",
                contents=["1.1. Blabla"],
                data=dict(level=1),
            ),
            "bli bli bli",
        ]

        # Act
        result = parse_sections(self.context, elements, level=0)

        # Assert
        assert_elements_equal(
            result,
            [
                make_segmentation_tag(
                    self.soup,
                    "section",
                    contents=[
                        make_segmentation_tag(
                            self.soup,
                            "section_title",
                            contents=["1. Bla"],
                        ),
                        make_segmentation_tag(
                            self.soup,
                            "alinea",
                            contents=["bla bla bla"],
                            data=dict(number="1"),
                        ),
                        make_segmentation_tag(
                            self.soup,
                            "section",
                            contents=[
                                make_segmentation_tag(
                                    self.soup,
                                    "section_title",
                                    contents=["1.1. Blabla"],
                                ),
                                make_segmentation_tag(
                                    self.soup,
                                    "alinea",
                                    contents=["bli bli bli"],
                                    data=dict(number="1"),
                                ),
                            ],
                        ),
                    ],
                ),
            ],
            ignore_data_if_omitted=True,
            ignore_text_span_data=True,
        )

    def test_parse_sections_missing_level(self):
        # Arrange
        elements = [
            make_segmentation_tag(
                self.soup,
                "section_title",
                contents=["1. Bla"],
                data=dict(level=0),
            ),
            make_segmentation_tag(
                self.soup,
                "section_title",
                contents=["1.1.1. Blabla"],
                data=dict(level=2),
            ),
        ]

        # Act
        result = parse_sections(self.context, elements, level=0)

        # Assert
        assert_elements_equal(
            result,
            [
                make_segmentation_tag(
                    self.soup,
                    "section",
                    contents=[
                        make_segmentation_tag(
                            self.soup,
                            "section_title",
                            contents=["1. Bla"],
                        ),
                        make_segmentation_tag(
                            self.soup,
                            "section",
                            contents=[
                                make_segmentation_tag(
                                    self.soup,
                                    "section_title",
                                    contents=["1.1.1. Blabla"],
                                ),
                            ],
                        ),
                    ],
                ),
            ],
            ignore_data_if_omitted=True,
            ignore_text_span_data=True,
        )

    def test_parse_missing_title_current_level(self):
        # Arrange
        elements = [
            make_segmentation_tag(
                self.soup,
                "section_title",
                contents=["1.1. bla"],
                data=dict(level=1),
            ),
            make_segmentation_tag(
                self.soup,
                "section_title",
                contents=["1.1.1. bla"],
                data=dict(level=2),
            ),
            make_segmentation_tag(
                self.soup,
                "section_title",
                contents=["1.2. bla"],
                data=dict(level=1),
            ),
            make_segmentation_tag(
                self.soup,
                "section_title",
                contents=["2. bla"],
                data=dict(level=0),
            ),
            make_segmentation_tag(
                self.soup,
                "section_title",
                contents=["2.1. bla"],
                data=dict(level=1),
            ),
        ]

        # Act
        result = parse_sections(self.context, elements, level=0)

        # Assert
        assert_elements_equal(
            result,
            [
                make_segmentation_tag(
                    self.soup,
                    "section",
                    contents=[
                        make_segmentation_tag(
                            self.soup,
                            "section_title",
                            contents=["1.1. bla"],
                        ),
                        make_segmentation_tag(
                            self.soup,
                            "section",
                            contents=[
                                make_segmentation_tag(
                                    self.soup,
                                    "section_title",
                                    contents=["1.1.1. bla"],
                                ),
                            ],
                        ),
                    ],
                ),
                make_segmentation_tag(
                    self.soup,
                    "section",
                    contents=[
                        make_segmentation_tag(
                            self.soup,
                            "section_title",
                            contents=["1.2. bla"],
                        ),
                    ],
                ),
                make_segmentation_tag(
                    self.soup,
                    "section",
                    contents=[
                        make_segmentation_tag(
                            self.soup,
                            "section_title",
                            contents=["2. bla"],
                        ),
                        make_segmentation_tag(
                            self.soup,
                            "section",
                            contents=[
                                make_segmentation_tag(
                                    self.soup,
                                    "section_title",
                                    contents=["2.1. bla"],
                                ),
                            ],
                        ),
                    ],
                ),
            ],
            ignore_data_if_omitted=True,
            ignore_text_span_data=True,
        )


class TestParseAlineas(BaseTestCase):

    def test_merge_if_continuing_sentence_and_page_separator(self):
        # Arrange
        elements = [
            *make_text_spans(self.soup, "This is a sentence that "),
            make_segmentation_tag(self.soup, "page_separator", data=dict(page_index=1)),
            *make_text_spans(self.soup, "continues on the next page."),
        ]

        # Act
        result = parse_alineas(self.context, elements)

        # Assert
        assert_elements_equal(
            result,
            [
                make_segmentation_tag(
                    self.soup,
                    "alinea",
                    contents=[
                        make_segmentation_tag(
                            self.soup,
                            "text_span",
                            contents=[
                                "This is a sentence that ",
                                make_segmentation_tag(
                                    self.soup, "page_separator", data=dict(page_index=1)
                                ),
                                "continues on the next page.",
                            ],
                        )
                    ],
                    data=dict(number="1"),
                ),
            ],
            ignore_text_span_data=True,
            ignore_data_if_omitted=True,
        )


class TestRenderAlinea(BaseTestCase):

    def test_simple(self):
        # Arrange
        alinea = make_segmentation_tag(
            self.soup,
            "alinea",
            contents=make_text_spans(self.soup, "This is an alinea."),
            data=dict(number="1"),
        )

        # Act
        result = render_alinea(self.context, alinea)

        # Assert
        assert normalized_html_str(str(result)) == normalized_html_str(
            """
            <div class="arretify-alinea" data-number="1">
                This is an alinea.
            </div>
            """
        )


class TestRenderSection(BaseTestCase):

    def test_simple(self):
        # Arrange
        tag = make_segmentation_tag(
            self.soup,
            "section",
            contents=[
                make_segmentation_tag(
                    self.soup,
                    "section_title",
                    contents=make_text_spans(self.soup, "Article 1 : Disposition"),
                    data=dict(
                        level=0,
                        number="1",
                        title="Disposition",
                        type="article",
                    ),
                ),
                make_segmentation_tag(
                    self.soup,
                    "alinea",
                    contents=make_text_spans(self.soup, "Bla bla bla ..."),
                    data=dict(number="1"),
                ),
            ],
        )

        # Act
        result = render_section(self.context, tag)

        # Assert
        assert normalized_html_str(str(result)) == normalized_html_str(
            """
            <section class="arretify-section" data-number="1" data-title="Disposition" data-type="article">
                <h2 class="arretify-section_title">
                    Article 1 : Disposition
                </h2>
                <div class="arretify-alinea" data-number="1">
                    Bla bla bla ...
                </div>
            </section>
            """  # noqa: E501
        )


class TestRenderSectionTitle(BaseTestCase):

    def test_simple(self):
        # Arrange
        section_title = make_segmentation_tag(
            self.soup,
            "section_title",
            contents=make_text_spans(self.soup, "Titre I - Introduction"),
            data=dict(
                level=0,
                number="I",
                title="Introduction",
                type="titre",
            ),
        )

        # Act
        result = render_section_title(self.context, section_title)

        # Assert
        assert normalized_html_str(str(result)) == normalized_html_str(
            """
            <h2 class="arretify-section_title">
                Titre I - Introduction
            </h2>
            """
        )
