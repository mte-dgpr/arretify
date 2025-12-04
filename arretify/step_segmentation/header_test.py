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

from arretify.errors import ErrorCodes
from arretify.semantic_tag_specs import (
    ArreteTitleSpec,
    DateSpec,
    EmblemSpec,
    EntitySpec,
    ErrorSpec,
    HonorarySpec,
    IdentificationSpec,
    PageFooterSpec,
    PageSeparatorData,
    PageSeparatorSpec,
    SectionData,
    SectionSpec,
    SupplementaryMotifInfoSpec,
)
from arretify.step_segmentation.semantic_tag_specs import (
    ListSegmentationSpec,
    MotifSegmentationSpec,
    VisaSegmentationSpec,
)
from arretify.utils.html_create import make_semantic_tag, make_tag, wrap_in_tag
from arretify.utils.testing import create_document_context

from .header import (
    _make_header_element_tag,
    parse_arrete_title_element,
    parse_emblem_element,
    parse_entity_element,
    parse_header,
    parse_honorary_element,
    parse_identification_element,
    parse_supplementary_motif_info_element,
    parse_visa_and_motif_elements,
)
from .testing import assert_elements_equal, make_text_spans


class BaseTestCase(unittest.TestCase):
    def setUp(self):
        self.context = create_document_context()
        self.soup = self.context.protected_soup


class TestParseHeader(BaseTestCase):

    def test_unknown_elements(self):
        # Arrange
        unexpected_article = make_semantic_tag(
            self.soup,
            SectionSpec,
            contents=[],
            data=SectionData(
                title="Article 1",
                number="1",
                type="article",
            ),
        )
        contents = [unexpected_article]

        # Act
        results = parse_header(self.context, contents)

        # Assert
        assert_elements_equal(
            results,
            [
                make_semantic_tag(
                    self.soup,
                    ErrorSpec,
                    contents=[unexpected_article],
                    data=ErrorSpec.data_model(error_codes=[ErrorCodes.unknown_content]),
                ),
            ],
            ignore_text_span_data=True,
        )


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
                    VisaSegmentationSpec,
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
                    VisaSegmentationSpec,
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
                    self.soup, VisaSegmentationSpec, contents=make_text_spans(self.soup, "Vu bla")
                ),
                *make_text_spans(self.soup, "Ceci est du texte aléatoire qui n'est pas un visa."),
                make_semantic_tag(
                    self.soup, VisaSegmentationSpec, contents=make_text_spans(self.soup, "Vu blo")
                ),
            ],
            ignore_text_span_data=True,
        )

    def test_variant_simple_inside_list(self):
        # Arrange
        elements = [
            make_semantic_tag(
                self.soup,
                ListSegmentationSpec,
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
                    MotifSegmentationSpec,
                    contents=make_text_spans(self.soup, "- Considérant que blabla ;"),
                ),
                make_semantic_tag(
                    self.soup,
                    MotifSegmentationSpec,
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
                    VisaSegmentationSpec,
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
                    self.soup,
                    MotifSegmentationSpec,
                    contents=make_text_spans(self.soup, "que blabla ;"),
                ),
                make_semantic_tag(
                    self.soup,
                    MotifSegmentationSpec,
                    contents=make_text_spans(self.soup, "que bloblo ;"),
                ),
                make_semantic_tag(
                    self.soup,
                    MotifSegmentationSpec,
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
                self.soup,
                PageFooterSpec,
                contents=wrap_in_tag(self.soup, "div", ["page 1"]),
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
                    VisaSegmentationSpec,
                    contents=make_text_spans(
                        self.soup,
                        "le code de l'environnement, et notamment ses titres "
                        "1er et 4 des parties réglementaires et législatives du livre V ;",
                    ),
                ),
                make_semantic_tag(
                    self.soup,
                    PageFooterSpec,
                    contents=wrap_in_tag(self.soup, "div", ["page 1"]),
                ),
                make_semantic_tag(
                    self.soup,
                    VisaSegmentationSpec,
                    contents=make_text_spans(
                        self.soup,
                        "la nomenclature des installations classées codifiée à l'annexe "
                        "de l'article R511-9 du code de l'environnement ;",
                    ),
                ),
            ],
            ignore_text_span_data=True,
        )

    def test_variant_implicit_list_with_extra_spaces_after_considerant(self):
        # Arrange
        elements = [
            *make_text_spans(
                self.soup,
                "CONSIDÉRANT  ",
                "que le site a évolué",
                "que les mesures concernent :",
            ),
        ]

        # Act
        result = parse_visa_and_motif_elements(self.context, elements)

        # Assert
        assert_elements_equal(
            result,
            [
                *make_text_spans(
                    self.soup,
                    "CONSIDÉRANT  ",
                ),
                make_semantic_tag(
                    self.soup,
                    MotifSegmentationSpec,
                    contents=make_text_spans(self.soup, "que le site a évolué"),
                ),
                make_semantic_tag(
                    self.soup,
                    MotifSegmentationSpec,
                    contents=make_text_spans(self.soup, "que les mesures concernent :"),
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
                ListSegmentationSpec,
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
                    VisaSegmentationSpec,
                    contents=make_text_spans(self.soup, "- le code de l'environnement ;"),
                ),
                make_semantic_tag(
                    self.soup,
                    VisaSegmentationSpec,
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
                ListSegmentationSpec,
                contents=make_text_spans(self.soup, "- le code de l'environnement ;"),
            ),
            *make_text_spans(self.soup, "Ceci est du texte aléatoire qui n'est pas un visa."),
            make_semantic_tag(
                self.soup,
                ListSegmentationSpec,
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
                    VisaSegmentationSpec,
                    contents=make_text_spans(self.soup, "- le code de l'environnement ;"),
                ),
                *make_text_spans(self.soup, "Ceci est du texte aléatoire qui n'est pas un visa."),
                make_semantic_tag(
                    self.soup,
                    VisaSegmentationSpec,
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
                ListSegmentationSpec,
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
                    VisaSegmentationSpec,
                    contents=make_text_spans(self.soup, "- le code de l'environnement ;"),
                ),
                make_semantic_tag(
                    self.soup,
                    VisaSegmentationSpec,
                    contents=make_text_spans(
                        self.soup, "- la nomenclature des installations classées ;"
                    ),
                ),
                make_semantic_tag(
                    self.soup,
                    VisaSegmentationSpec,
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
                ListSegmentationSpec,
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
                    MotifSegmentationSpec,
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
                            ListSegmentationSpec,
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

    def test_make_header_element_tag(self):
        # Arrange
        contents = make_text_spans(self.soup, "liberté égalité fraternité")

        # Act
        rendered = _make_header_element_tag(self.context, EmblemSpec, contents)

        # Assert
        assert [str(tag) for tag in rendered] == [
            "<div>liberté </div>",
            "<div>égalité </div>",
            "<div>fraternité</div>",
        ]


class TestParseArreteTitle(BaseTestCase):

    def test_simple(self):
        # Arrange
        contents = make_text_spans(
            self.soup,
            # Fuzzy pattern, match until next header element
            "Arrêté du 1er janvier 2020",
            "Vu le blabla",
        )

        # Act
        results = parse_arrete_title_element(self.context, contents)

        # Assert
        assert_elements_equal(
            results,
            [
                make_semantic_tag(
                    self.soup,
                    ArreteTitleSpec,
                    contents=[
                        make_tag(
                            self.soup,
                            "h1",
                            contents=[
                                "Arrêté du ",
                                make_semantic_tag(
                                    self.soup, DateSpec, contents=["1er janvier 2020"]
                                ),
                            ],
                        )
                    ],
                ),
                *make_text_spans(self.soup, "Vu le blabla"),
            ],
            ignore_text_span_data=True,
        )


class TestParseEmblemElement(BaseTestCase):

    def test_simple(self):
        # Arrange
        contents = make_text_spans(self.soup, "liberté égalité fraternité")

        # Act
        results = parse_emblem_element(self.context, contents)

        # Assert
        assert_elements_equal(
            results,
            [
                make_semantic_tag(
                    self.soup,
                    EmblemSpec,
                    contents=wrap_in_tag(
                        self.soup,
                        "div",
                        [
                            "liberté ",
                            "égalité ",
                            "fraternité",
                        ],
                    ),
                ),
            ],
            ignore_text_span_data=True,
        )


class TestParseEntityElement(BaseTestCase):

    def test_simple(self):
        # Arrange
        contents = make_text_spans(self.soup, "Ministère de la Transition écologique")

        # Act
        results = parse_entity_element(self.context, contents)

        # Assert
        assert_elements_equal(
            results,
            [
                make_semantic_tag(
                    self.soup,
                    EntitySpec,
                    contents=wrap_in_tag(
                        self.soup,
                        "div",
                        [
                            "Ministère de la Transition écologique",
                        ],
                    ),
                ),
            ],
            ignore_text_span_data=True,
        )


class TestParseIdentificationElement(BaseTestCase):

    def test_simple(self):
        # Arrange
        contents = make_text_spans(self.soup, "Référence : 2020-1234")

        # Act
        results = parse_identification_element(self.context, contents)

        # Assert
        assert_elements_equal(
            results,
            [
                make_semantic_tag(
                    self.soup,
                    IdentificationSpec,
                    contents=wrap_in_tag(
                        self.soup,
                        "div",
                        [
                            "Référence : 2020-1234",
                        ],
                    ),
                ),
            ],
            ignore_text_span_data=True,
        )


class TestParseHonoraryElement(BaseTestCase):
    def test_simple(self):
        # Arrange
        contents = make_text_spans(
            self.soup, "La Directrice Générale de l'Agence Régionale de Santé Grand Est"
        )

        # Act
        results = parse_honorary_element(self.context, contents)

        # Assert
        assert_elements_equal(
            results,
            [
                make_semantic_tag(
                    self.soup,
                    HonorarySpec,
                    contents=wrap_in_tag(
                        self.soup,
                        "div",
                        [
                            "La Directrice Générale de l'Agence Régionale de Santé Grand Est",
                        ],
                    ),
                ),
            ],
            ignore_text_span_data=True,
        )


class TestParseSupplementaryMotifInfo(BaseTestCase):

    def test_simple(self):
        # Arrange
        contents = make_text_spans(
            self.soup,
            (
                "Sur proposition de M. le directeur régional de l'environnement,"
                " de l'aménagement et du logement des Hauts-de-France ;"
            ),
        )

        # Act
        results = parse_supplementary_motif_info_element(self.context, contents)

        # Assert
        assert_elements_equal(
            results,
            [
                make_semantic_tag(
                    self.soup,
                    SupplementaryMotifInfoSpec,
                    contents=wrap_in_tag(
                        self.soup,
                        "div",
                        [
                            "Sur proposition de M. le directeur régional de l'environnement,"
                            " de l'aménagement et du logement des Hauts-de-France ;",
                        ],
                    ),
                ),
            ],
            ignore_text_span_data=True,
        )
