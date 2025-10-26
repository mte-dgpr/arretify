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

from arretify.utils.testing import create_document_context, normalized_html_str
from arretify.utils.html_semantic import make_semantic_tag
from arretify.semantic_tag_specs import (
    PageSeparatorData,
    VisaSpec,
    MotifSpec,
    PageSeparatorSpec,
    PageFooterSpec,
    EmblemSpec,
    EntitySpec,
    ArreteSpec,
)
from arretify.step_segmentation.semantic_tag_specs import ListSpec
from .header import (
    parse_visa_and_motif_elements,
    _parse_header_element,
    _parse_header_element_fuzzy,
    render_header_element,
    render_visa_motif,
    render_arrete_title,
)
from .testing import assert_elements_equal, make_text_spans


class BaseTestCase(unittest.TestCase):
    def setUp(self):
        self.context = create_document_context()
        self.soup = self.context.soup


class TestParseVisaAndMotifs(BaseTestCase):

    def test_variant_simple(self):
        # Arrange
        elements = make_text_spans(
            self.soup,
            (
                "Vu le code de l'environnement, et notamment ses titres "
                "1er et 4 des parties réglementaires et législatives du livre V ;"
            ),
            (
                "Vu la nomenclature des installations classées codifiée à l'annexe "
                "de l'article R511-9 du code de l'environnement ;"
            ),
        )

        # Act
        result = parse_visa_and_motif_elements(self.context, elements)

        # Assert
        assert_elements_equal(
            result,
            [
                make_semantic_tag(
                    self.soup,
                    VisaSpec,
                    contents=make_text_spans(
                        self.soup,
                        (
                            "Vu le code de l'environnement, et notamment ses titres "
                            "1er et 4 des parties réglementaires et législatives du livre V ;"
                        ),
                    ),
                ),
                make_semantic_tag(
                    self.soup,
                    VisaSpec,
                    contents=make_text_spans(
                        self.soup,
                        (
                            "Vu la nomenclature des installations classées codifiée à l'annexe "
                            "de l'article R511-9 du code de l'environnement ;"
                        ),
                    ),
                ),
            ],
            ignore_text_span_data=True,
        )

    def test_variant_simple_interrupted_by_random_text(self):
        # Arrange
        elements = make_text_spans(
            self.soup,
            "Vu bla",
            "Ceci est du texte aléatoire qui n'est pas un visa.",
            "Vu blo",
        )

        # Act
        result = parse_visa_and_motif_elements(self.context, elements)

        # Assert
        assert_elements_equal(
            result,
            [
                make_semantic_tag(
                    self.soup, VisaSpec, contents=make_text_spans(self.soup, "Vu bla")
                ),
                *make_text_spans(self.soup, "Ceci est du texte aléatoire qui n'est pas un visa."),
                make_semantic_tag(
                    self.soup, VisaSpec, contents=make_text_spans(self.soup, "Vu blo")
                ),
            ],
            ignore_text_span_data=True,
        )

    def test_variant_simple_inside_list(self):
        # Arrange
        elements = [
            make_semantic_tag(
                self.soup,
                ListSpec,
                contents=make_text_spans(
                    self.soup,
                    "- Considérant que blabla ;",
                    "- Considérant que bloblo ;",
                ),
            ),
        ]

        # Act
        result = parse_visa_and_motif_elements(self.context, elements)

        # Assert
        assert_elements_equal(
            result,
            [
                make_semantic_tag(
                    self.soup,
                    MotifSpec,
                    contents=make_text_spans(self.soup, "- Considérant que blabla ;"),
                ),
                make_semantic_tag(
                    self.soup,
                    MotifSpec,
                    contents=make_text_spans(self.soup, "- Considérant que bloblo ;"),
                ),
            ],
            ignore_text_span_data=True,
        )

    def test_variant_simple_page_separator_interrupting_sentence(self):
        # Arrange
        elements = [
            *make_text_spans(
                self.soup, "Vu le code de l'environnement, et notamment ses titres 1er et 4"
            ),
            make_semantic_tag(self.soup, PageSeparatorSpec, data=PageSeparatorData(page_index=0)),
            *make_text_spans(self.soup, "des parties réglementaires et législatives du livre V ;"),
        ]

        # Act
        result = parse_visa_and_motif_elements(self.context, elements)

        # Assert
        assert_elements_equal(
            result,
            [
                make_semantic_tag(
                    self.soup,
                    VisaSpec,
                    contents=[
                        *make_text_spans(
                            self.soup,
                            "Vu le code de l'environnement, et notamment ses titres 1er et 4",
                        ),
                        make_semantic_tag(
                            self.soup, PageSeparatorSpec, data=PageSeparatorData(page_index=0)
                        ),
                        *make_text_spans(
                            self.soup, "des parties réglementaires et législatives du livre V ;"
                        ),
                    ],
                ),
            ],
            ignore_text_span_data=True,
        )

    def test_variant_implicit_list(self):
        # Arrange
        elements = make_text_spans(
            self.soup,
            "CONSIDÉRANT : ",
            "que blabla ;",
            "que bloblo ;",
            "qu'en application de blibli ;",
        )

        # Act
        result = parse_visa_and_motif_elements(self.context, elements)

        # Assert
        assert_elements_equal(
            result,
            [
                *make_text_spans(self.soup, "CONSIDÉRANT : "),
                make_semantic_tag(
                    self.soup, MotifSpec, contents=make_text_spans(self.soup, "que blabla ;")
                ),
                make_semantic_tag(
                    self.soup, MotifSpec, contents=make_text_spans(self.soup, "que bloblo ;")
                ),
                make_semantic_tag(
                    self.soup,
                    MotifSpec,
                    contents=make_text_spans(self.soup, "qu'en application de blibli ;"),
                ),
            ],
            ignore_text_span_data=True,
        )

    def test_variant_implicit_list_interrupted_by_page_footer(self):
        # Arrange
        elements = [
            *make_text_spans(
                self.soup,
                "Vu : ",
                (
                    "le code de l'environnement, et notamment ses titres "
                    "1er et 4 des parties réglementaires et législatives du livre V ;"
                ),
            ),
            make_semantic_tag(
                self.soup, PageFooterSpec, contents=make_text_spans(self.soup, "page 1")
            ),
            *make_text_spans(
                self.soup,
                (
                    "la nomenclature des installations classées codifiée à l'annexe "
                    "de l'article R511-9 du code de l'environnement ;"
                ),
            ),
        ]

        # Act
        result = parse_visa_and_motif_elements(self.context, elements)

        # Assert
        assert_elements_equal(
            result,
            [
                *make_text_spans(self.soup, "Vu : "),
                make_semantic_tag(
                    self.soup,
                    VisaSpec,
                    contents=make_text_spans(
                        self.soup,
                        "le code de l'environnement, et notamment ses titres "
                        "1er et 4 des parties réglementaires et législatives du livre V ;",
                    ),
                ),
                make_semantic_tag(
                    self.soup, PageFooterSpec, contents=make_text_spans(self.soup, "page 1")
                ),
                make_semantic_tag(
                    self.soup,
                    VisaSpec,
                    contents=make_text_spans(
                        self.soup,
                        "la nomenclature des installations classées codifiée à l'annexe "
                        "de l'article R511-9 du code de l'environnement ;",
                    ),
                ),
            ],
            ignore_text_span_data=True,
        )

    def test_variant_explicit_list(self):
        # Arrange
        elements = [
            *make_text_spans(self.soup, "Vu : "),
            make_semantic_tag(
                self.soup,
                ListSpec,
                contents=make_text_spans(
                    self.soup,
                    "- le code de l'environnement ;",
                    "- la nomenclature des installations classées ;",
                ),
            ),
        ]

        # Act
        result = parse_visa_and_motif_elements(self.context, elements)

        # Assert
        assert_elements_equal(
            result,
            [
                *make_text_spans(self.soup, "Vu : "),
                make_semantic_tag(
                    self.soup,
                    VisaSpec,
                    contents=make_text_spans(self.soup, "- le code de l'environnement ;"),
                ),
                make_semantic_tag(
                    self.soup,
                    VisaSpec,
                    contents=make_text_spans(
                        self.soup, "- la nomenclature des installations classées ;"
                    ),
                ),
            ],
            ignore_text_span_data=True,
        )

    def test_variant_explicit_list_interrupted(self):
        # Arrange
        elements = [
            *make_text_spans(self.soup, "Vu : "),
            make_semantic_tag(
                self.soup,
                ListSpec,
                contents=make_text_spans(self.soup, "- le code de l'environnement ;"),
            ),
            *make_text_spans(self.soup, "Ceci est du texte aléatoire qui n'est pas un visa."),
            make_semantic_tag(
                self.soup,
                ListSpec,
                contents=make_text_spans(
                    self.soup, "- la nomenclature des installations classées ;"
                ),
            ),
        ]

        # Act
        result = parse_visa_and_motif_elements(self.context, elements)

        # Assert
        assert_elements_equal(
            result,
            [
                *make_text_spans(self.soup, "Vu : "),
                make_semantic_tag(
                    self.soup,
                    VisaSpec,
                    contents=make_text_spans(self.soup, "- le code de l'environnement ;"),
                ),
                *make_text_spans(self.soup, "Ceci est du texte aléatoire qui n'est pas un visa."),
                make_semantic_tag(
                    self.soup,
                    VisaSpec,
                    contents=make_text_spans(
                        self.soup, "- la nomenclature des installations classées ;"
                    ),
                ),
            ],
            ignore_text_span_data=True,
        )

    def test_variant_explicit_list_vu_inside_list_element(self):
        # Arrange
        elements = [
            *make_text_spans(self.soup, "Vu : "),
            make_semantic_tag(
                self.soup,
                ListSpec,
                contents=make_text_spans(
                    self.soup,
                    "- le code de l'environnement ;",
                    "- la nomenclature des installations classées ;",
                    "- vu la demande déposée par la société XYZ ;",
                ),
            ),
        ]

        # Act
        result = parse_visa_and_motif_elements(self.context, elements)

        # Assert
        assert_elements_equal(
            result,
            [
                *make_text_spans(self.soup, "Vu : "),
                make_semantic_tag(
                    self.soup,
                    VisaSpec,
                    contents=make_text_spans(self.soup, "- le code de l'environnement ;"),
                ),
                make_semantic_tag(
                    self.soup,
                    VisaSpec,
                    contents=make_text_spans(
                        self.soup, "- la nomenclature des installations classées ;"
                    ),
                ),
                make_semantic_tag(
                    self.soup,
                    VisaSpec,
                    contents=make_text_spans(
                        self.soup, "- vu la demande déposée par la société XYZ ;"
                    ),
                ),
            ],
            ignore_text_span_data=True,
        )

    def test_variant_simple_with_list_inside_and_interrupted_by_page_separator(self):
        # Arrange
        elements = [
            *make_text_spans(
                self.soup,
                "Considérant que la demande de modification sollicitée "
                "le 19 juillet 2021 porte sur:",
            ),
            make_semantic_tag(self.soup, PageSeparatorSpec, data=PageSeparatorData(page_index=1)),
            make_semantic_tag(
                self.soup,
                ListSpec,
                contents=make_text_spans(
                    self.soup,
                    "- la modification de l'installation de stockage de déchets non dangereux ;",
                    "- la mise en conformité avec les exigences réglementaires ;",
                ),
            ),
        ]

        # Act
        result = parse_visa_and_motif_elements(self.context, elements)

        # Assert
        assert_elements_equal(
            result,
            [
                make_semantic_tag(
                    self.soup,
                    MotifSpec,
                    contents=[
                        *make_text_spans(
                            self.soup,
                            "Considérant que la demande de modification sollicitée "
                            "le 19 juillet 2021 porte sur:",
                        ),
                        make_semantic_tag(
                            self.soup, PageSeparatorSpec, data=PageSeparatorData(page_index=1)
                        ),
                        make_semantic_tag(
                            self.soup,
                            ListSpec,
                            contents=make_text_spans(
                                self.soup,
                                (
                                    "- la modification de l'installation de stockage de déchets"
                                    " non dangereux ;"
                                ),
                                "- la mise en conformité avec les exigences réglementaires ;",
                            ),
                        ),
                    ],
                ),
            ],
            ignore_text_span_data=True,
        )


class TestRenderHeaderElement(BaseTestCase):

    def test_render_header_element(self):
        # Arrange
        tag = make_semantic_tag(
            self.soup,
            EmblemSpec,
            contents=make_text_spans(self.soup, "liberté égalité fraternité"),
        )

        # Act
        rendered = render_header_element(self.context, tag)

        # Assert
        assert normalized_html_str(str(rendered)) == normalized_html_str(
            """
            <div data-spec="emblem">
                <div>liberté</div>
                <div>égalité</div>
                <div>fraternité</div>
            </div>
            """
        )


class TestParseHeaderElement(BaseTestCase):

    def test_parse_header_element(self):
        # Arrange
        elements = make_text_spans(
            self.soup,
            "liberte",
            "égalité",
            "fraternité",
        )

        # Act
        elements = _parse_header_element(self.context, elements, EmblemSpec)

        # Assert
        assert_elements_equal(
            elements,
            [
                make_semantic_tag(
                    self.soup,
                    EmblemSpec,
                    contents=make_text_spans(
                        self.soup,
                        "liberte",
                        "égalité",
                        "fraternité",
                    ),
                ),
            ],
            ignore_text_span_data=True,
        )

    def test_parse_header_element_fuzzy(self):
        # Arrange
        elements = make_text_spans(
            self.soup,
            "prefecture de la région",
            "basée à Naboo",
            # Arrete title : should not be included in the entity
            "Arrêté du 1er janvier 2020",
        )

        # Act
        elements = _parse_header_element_fuzzy(self.context, elements, EntitySpec)

        # Assert
        assert_elements_equal(
            elements,
            [
                make_semantic_tag(
                    self.soup,
                    EntitySpec,
                    contents=make_text_spans(
                        self.soup,
                        "prefecture de la région",
                        "basée à Naboo",
                    ),
                ),
                *make_text_spans(
                    self.soup,
                    "Arrêté du 1er janvier 2020",
                ),
            ],
            ignore_text_span_data=True,
        )


class TestRenderVisaMotif(BaseTestCase):

    def test_render_simple(self):
        # Arrange
        tag = make_semantic_tag(
            self.soup,
            VisaSpec,
            contents=make_text_spans(
                self.soup,
                "Vu le code de l'environnement, et notamment ses titres "
                "1er et 4 des parties réglementaires et législatives du livre V ;",
            ),
        )

        # Act
        rendered = render_visa_motif(self.context, tag)

        # Assert
        assert normalized_html_str(str(rendered)) == normalized_html_str(
            """
            <div data-spec="visa">
                Vu le code de l'environnement, et notamment ses titres
                1er et 4 des parties réglementaires et législatives du livre V ;
            </div>
            """
        )


class TestRenderArreteTitle(BaseTestCase):

    def test_render_arrete_title(self):
        # Arrange
        tag = make_semantic_tag(
            self.soup,
            ArreteSpec,
            contents=make_text_spans(
                self.soup,
                "Arrêté du 1er janvier 2020",
            ),
        )

        # Act
        rendered = render_arrete_title(self.context, tag)

        # Assert
        assert normalized_html_str(str(rendered)) == normalized_html_str(
            """
            <div data-spec="arrete_title">
                <h1>Arrêté du
                    <time data-spec="date" datetime="2020-01-01">
                        1er janvier 2020
                    </time>
                </h1>
            </div>
            """
        )
