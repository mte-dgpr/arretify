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
    PageSeparatorData,
    PageSeparatorSpec,
    AlineaSpec,
    AlineaData,
)
from arretify.utils.testing import create_document_context, normalized_html_str
from arretify.utils.html_semantic import make_semantic_tag
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
from .semantic_tag_specs import (
    SectionSegmentationSpec,
    SectionTitleSegmentationData,
    SectionTitleSegmentationSpec,
    TextSpanSegmentationData,
    TextSpanSegmentationSpec,
)


class BaseTestCase(unittest.TestCase):
    def setUp(self):
        self.context = create_document_context()
        self.soup = self.context.protected_soup


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
                make_semantic_tag(
                    self.soup,
                    SectionTitleSegmentationSpec,
                    contents=make_text_spans(self.soup, "Titre I - Introduction"),
                    data=SectionTitleSegmentationData(
                        level=0,
                        number="I",
                        title="Introduction",
                        type="titre",
                    ),
                ),
                make_semantic_tag(
                    self.soup,
                    SectionTitleSegmentationSpec,
                    contents=make_text_spans(self.soup, "1. Contexte"),
                    data=SectionTitleSegmentationData(
                        level=1,
                        number="1",
                        title="Contexte",
                        type="unknown",
                    ),
                ),
                *make_text_spans(self.soup, "bla bla bla"),
                make_semantic_tag(
                    self.soup,
                    SectionTitleSegmentationSpec,
                    contents=make_text_spans(self.soup, "2. Objectifs"),
                    data=SectionTitleSegmentationData(
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
                make_semantic_tag(
                    self.soup,
                    SectionTitleSegmentationSpec,
                    contents=make_text_spans(self.soup, "Titre II - Méthodologie"),
                    data=SectionTitleSegmentationData(
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
            make_semantic_tag(
                self.soup,
                TextSpanSegmentationSpec,
                contents=[
                    make_semantic_tag(
                        self.soup,
                        AddressSpec,
                        contents=make_text_spans(self.soup, "1 rue de l'avenir"),
                    )
                ],
                data=TextSpanSegmentationData(start=[0, 0, 0], end=[0, 0, 0]),
            ),
        ]

        # Act
        result = list(parse_section_titles(self.context, elements))

        # Assert
        assert_elements_equal(
            result,
            [
                make_semantic_tag(
                    self.soup,
                    SectionTitleSegmentationSpec,
                    contents=make_text_spans(self.soup, "Titre I - Introduction"),
                    data=SectionTitleSegmentationData(
                        level=0,
                        number="I",
                        title="Introduction",
                        type="titre",
                    ),
                ),
                make_semantic_tag(
                    self.soup,
                    TextSpanSegmentationSpec,
                    contents=[
                        make_semantic_tag(
                            self.soup,
                            AddressSpec,
                            contents=make_text_spans(self.soup, "1 rue de l'avenir"),
                        )
                    ],
                    data=TextSpanSegmentationData(start=[0, 0, 0], end=[0, 0, 0]),
                ),
            ],
            ignore_text_span_data=True,
        )


class TestParseSections(BaseTestCase):

    def test_parse_sections(self):
        # Arrange
        elements = [
            *make_text_spans(self.soup, "bly bly bly"),
            make_semantic_tag(
                self.soup,
                SectionTitleSegmentationSpec,
                contents=make_text_spans(self.soup, "Titre I - Introduction"),
                data=SectionTitleSegmentationData(level=1),
            ),
            make_semantic_tag(
                self.soup,
                SectionTitleSegmentationSpec,
                contents=make_text_spans(self.soup, "1. Contexte"),
                data=SectionTitleSegmentationData(level=2),
            ),
            *make_text_spans(self.soup, "bla bla bla"),
            make_semantic_tag(
                self.soup,
                SectionTitleSegmentationSpec,
                contents=make_text_spans(self.soup, "2. Objectifs"),
                data=SectionTitleSegmentationData(level=2),
            ),
            *make_text_spans(
                self.soup,
                "blo blo blo",
                "bli bli bli",
            ),
            make_semantic_tag(
                self.soup,
                SectionTitleSegmentationSpec,
                contents=make_text_spans(self.soup, "Titre II - Méthodologie"),
                data=SectionTitleSegmentationData(level=1),
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
                make_semantic_tag(
                    self.soup,
                    AlineaSpec,
                    contents=make_text_spans(self.soup, "bly bly bly"),
                    data=AlineaData(number="1"),
                ),
                make_semantic_tag(
                    self.soup,
                    SectionSegmentationSpec,
                    contents=[
                        make_semantic_tag(
                            self.soup,
                            SectionTitleSegmentationSpec,
                            contents=make_text_spans(self.soup, "Titre I - Introduction"),
                            data=SectionTitleSegmentationData(
                                level=1,
                            ),
                        ),
                        make_semantic_tag(
                            self.soup,
                            SectionSegmentationSpec,
                            contents=[
                                make_semantic_tag(
                                    self.soup,
                                    SectionTitleSegmentationSpec,
                                    contents=make_text_spans(self.soup, "1. Contexte"),
                                    data=SectionTitleSegmentationData(
                                        level=2,
                                    ),
                                ),
                                make_semantic_tag(
                                    self.soup,
                                    AlineaSpec,
                                    contents=make_text_spans(self.soup, "bla bla bla"),
                                    data=AlineaData(number="1"),
                                ),
                            ],
                        ),
                        make_semantic_tag(
                            self.soup,
                            SectionSegmentationSpec,
                            contents=[
                                make_semantic_tag(
                                    self.soup,
                                    SectionTitleSegmentationSpec,
                                    contents=make_text_spans(self.soup, "2. Objectifs"),
                                    data=SectionTitleSegmentationData(
                                        level=2,
                                    ),
                                ),
                                make_semantic_tag(
                                    self.soup,
                                    AlineaSpec,
                                    contents=make_text_spans(self.soup, "blo blo blo"),
                                    data=AlineaData(number="1"),
                                ),
                                make_semantic_tag(
                                    self.soup,
                                    AlineaSpec,
                                    contents=make_text_spans(self.soup, "bli bli bli"),
                                    data=AlineaData(number="2"),
                                ),
                            ],
                        ),
                    ],
                ),
                make_semantic_tag(
                    self.soup,
                    SectionSegmentationSpec,
                    contents=[
                        make_semantic_tag(
                            self.soup,
                            SectionTitleSegmentationSpec,
                            contents=make_text_spans(self.soup, "Titre II - Méthodologie"),
                            data=SectionTitleSegmentationData(
                                level=1,
                            ),
                        ),
                        make_semantic_tag(
                            self.soup,
                            AlineaSpec,
                            contents=make_text_spans(self.soup, "blu blu blu"),
                            data=AlineaData(number="1"),
                        ),
                        make_semantic_tag(
                            self.soup,
                            AlineaSpec,
                            contents=make_text_spans(self.soup, "ble ble ble"),
                            data=AlineaData(number="2"),
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
            make_semantic_tag(
                self.soup,
                SectionTitleSegmentationSpec,
                contents=["1. Bla"],
                data=SectionTitleSegmentationData(level=0),
            ),
            "bla bla bla",
            make_semantic_tag(
                self.soup,
                SectionTitleSegmentationSpec,
                contents=["1.1. Blabla"],
                data=SectionTitleSegmentationData(level=1),
            ),
            "bli bli bli",
        ]

        # Act
        result = parse_sections(self.context, elements, level=0)

        # Assert
        assert_elements_equal(
            result,
            [
                make_semantic_tag(
                    self.soup,
                    SectionSegmentationSpec,
                    contents=[
                        make_semantic_tag(
                            self.soup,
                            SectionTitleSegmentationSpec,
                            contents=["1. Bla"],
                            data=SectionTitleSegmentationData(level=0),
                        ),
                        make_semantic_tag(
                            self.soup,
                            AlineaSpec,
                            contents=["bla bla bla"],
                            data=AlineaData(number="1"),
                        ),
                        make_semantic_tag(
                            self.soup,
                            SectionSegmentationSpec,
                            contents=[
                                make_semantic_tag(
                                    self.soup,
                                    SectionTitleSegmentationSpec,
                                    contents=["1.1. Blabla"],
                                    data=SectionTitleSegmentationData(level=1),
                                ),
                                make_semantic_tag(
                                    self.soup,
                                    AlineaSpec,
                                    contents=["bli bli bli"],
                                    data=AlineaData(number="1"),
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
            make_semantic_tag(
                self.soup,
                SectionTitleSegmentationSpec,
                contents=["1. Bla"],
                data=SectionTitleSegmentationData(level=0),
            ),
            make_semantic_tag(
                self.soup,
                SectionTitleSegmentationSpec,
                contents=["1.1.1. Blabla"],
                data=SectionTitleSegmentationData(level=2),
            ),
        ]

        # Act
        result = parse_sections(self.context, elements, level=0)

        # Assert
        assert_elements_equal(
            result,
            [
                make_semantic_tag(
                    self.soup,
                    SectionSegmentationSpec,
                    contents=[
                        make_semantic_tag(
                            self.soup,
                            SectionTitleSegmentationSpec,
                            contents=["1. Bla"],
                            data=SectionTitleSegmentationData(level=0),
                        ),
                        make_semantic_tag(
                            self.soup,
                            SectionSegmentationSpec,
                            contents=[
                                make_semantic_tag(
                                    self.soup,
                                    SectionTitleSegmentationSpec,
                                    contents=["1.1.1. Blabla"],
                                    data=SectionTitleSegmentationData(level=2),
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
            make_semantic_tag(
                self.soup,
                SectionTitleSegmentationSpec,
                contents=["1.1. bla"],
                data=SectionTitleSegmentationData(level=1),
            ),
            make_semantic_tag(
                self.soup,
                SectionTitleSegmentationSpec,
                contents=["1.1.1. bla"],
                data=SectionTitleSegmentationData(level=2),
            ),
            make_semantic_tag(
                self.soup,
                SectionTitleSegmentationSpec,
                contents=["1.2. bla"],
                data=SectionTitleSegmentationData(level=1),
            ),
            make_semantic_tag(
                self.soup,
                SectionTitleSegmentationSpec,
                contents=["2. bla"],
                data=SectionTitleSegmentationData(level=0),
            ),
            make_semantic_tag(
                self.soup,
                SectionTitleSegmentationSpec,
                contents=["2.1. bla"],
                data=SectionTitleSegmentationData(level=1),
            ),
        ]

        # Act
        result = parse_sections(self.context, elements, level=0)

        # Assert
        assert_elements_equal(
            result,
            [
                make_semantic_tag(
                    self.soup,
                    SectionSegmentationSpec,
                    contents=[
                        make_semantic_tag(
                            self.soup,
                            SectionTitleSegmentationSpec,
                            contents=["1.1. bla"],
                            data=SectionTitleSegmentationData(level=1),
                        ),
                        make_semantic_tag(
                            self.soup,
                            SectionSegmentationSpec,
                            contents=[
                                make_semantic_tag(
                                    self.soup,
                                    SectionTitleSegmentationSpec,
                                    contents=["1.1.1. bla"],
                                    data=SectionTitleSegmentationData(level=2),
                                ),
                            ],
                        ),
                    ],
                ),
                make_semantic_tag(
                    self.soup,
                    SectionSegmentationSpec,
                    contents=[
                        make_semantic_tag(
                            self.soup,
                            SectionTitleSegmentationSpec,
                            contents=["1.2. bla"],
                            data=SectionTitleSegmentationData(level=1),
                        ),
                    ],
                ),
                make_semantic_tag(
                    self.soup,
                    SectionSegmentationSpec,
                    contents=[
                        make_semantic_tag(
                            self.soup,
                            SectionTitleSegmentationSpec,
                            contents=["2. bla"],
                            data=SectionTitleSegmentationData(level=0),
                        ),
                        make_semantic_tag(
                            self.soup,
                            SectionSegmentationSpec,
                            contents=[
                                make_semantic_tag(
                                    self.soup,
                                    SectionTitleSegmentationSpec,
                                    contents=["2.1. bla"],
                                    data=SectionTitleSegmentationData(level=1),
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
            make_semantic_tag(self.soup, PageSeparatorSpec, data=PageSeparatorData(page_index=1)),
            *make_text_spans(self.soup, "continues on the next page."),
        ]

        # Act
        result = parse_alineas(self.context, elements)

        # Assert
        assert_elements_equal(
            result,
            [
                make_semantic_tag(
                    self.soup,
                    AlineaSpec,
                    contents=[
                        make_semantic_tag(
                            self.soup,
                            TextSpanSegmentationSpec,
                            contents=[
                                "This is a sentence that ",
                                make_semantic_tag(
                                    self.soup,
                                    PageSeparatorSpec,
                                    data=PageSeparatorData(page_index=1),
                                ),
                                "continues on the next page.",
                            ],
                            data=TextSpanSegmentationData(start=[0, 0, 0], end=[0, 0, 0]),
                        )
                    ],
                    data=AlineaData(number=1),
                ),
            ],
            ignore_text_span_data=True,
            ignore_data_if_omitted=True,
        )


class TestRenderAlinea(BaseTestCase):

    def test_simple(self):
        # Arrange
        alinea = make_semantic_tag(
            self.soup,
            AlineaSpec,
            contents=make_text_spans(self.soup, "This is an alinea."),
            data=AlineaData(number="1"),
        )

        # Act
        result = render_alinea(self.context, alinea)

        # Assert
        assert normalized_html_str(str(result)) == normalized_html_str(
            """
            <div data-spec="alinea" data-number="1">
                This is an alinea.
            </div>
            """
        )


class TestRenderSection(BaseTestCase):

    def test_simple(self):
        # Arrange
        tag = make_semantic_tag(
            self.soup,
            SectionSegmentationSpec,
            contents=[
                make_semantic_tag(
                    self.soup,
                    SectionTitleSegmentationSpec,
                    contents=make_text_spans(self.soup, "Article 1 : Disposition"),
                    data=SectionTitleSegmentationData(
                        level=0,
                        number="1",
                        title="Disposition",
                        type="article",
                    ),
                ),
                make_semantic_tag(
                    self.soup,
                    AlineaSpec,
                    contents=make_text_spans(self.soup, "Bla bla bla ..."),
                    data=AlineaData(number="1"),
                ),
            ],
        )

        # Act
        result = render_section(self.context, tag)

        # Assert
        assert normalized_html_str(str(result)) == normalized_html_str(
            """
            <section data-spec="section" data-number="1" data-title="Disposition" data-type="article">
                <h2 data-spec="section_title">
                    Article 1 : Disposition
                </h2>
                <div data-spec="alinea" data-number="1">
                    Bla bla bla ...
                </div>
            </section>
            """  # noqa: E501
        )


class TestRenderSectionTitle(BaseTestCase):

    def test_simple(self):
        # Arrange
        section_title = make_semantic_tag(
            self.soup,
            SectionTitleSegmentationSpec,
            contents=make_text_spans(self.soup, "Titre I - Introduction"),
            data=SectionTitleSegmentationData(
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
            <h2 data-spec="section_title">
                Titre I - Introduction
            </h2>
            """
        )
