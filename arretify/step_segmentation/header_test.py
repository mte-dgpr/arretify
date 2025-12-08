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
from arretify.utils.html_create import wrap_in_tag
from arretify.utils.testing import assert_elements_equal

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
from .testing import BaseTestCaseSegmentation


class TestParseHeader(BaseTestCaseSegmentation):

    def test_unknown_elements(self):
        # Arrange
        unexpected_article = self.make_semantic_tag(
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
                self.make_semantic_tag(
                    ErrorSpec,
                    contents=[unexpected_article],
                    data=ErrorSpec.data_model(error_codes=[ErrorCodes.unknown_content]),
                ),
            ],
        )


class TestParseVisaAndMotifs(BaseTestCaseSegmentation):

    def test_variant_simple(self):
        # Arrange
        elements = self.make_text_spans(
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
                self.make_semantic_tag(
                    VisaSegmentationSpec,
                    contents=self.make_text_spans(
                        (
                            "Vu le code de l'environnement, et notamment ses titres "
                            "1er et 4 des parties réglementaires et législatives du livre V ;"
                        ),
                    ),
                ),
                self.make_semantic_tag(
                    VisaSegmentationSpec,
                    contents=self.make_text_spans(
                        (
                            "Vu la nomenclature des installations classées codifiée à l'annexe "
                            "de l'article R511-9 du code de l'environnement ;"
                        ),
                    ),
                ),
            ],
        )

    def test_variant_simple_interrupted_by_random_text(self):
        # Arrange
        elements = self.make_text_spans(
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
                self.make_semantic_tag(
                    VisaSegmentationSpec, contents=self.make_text_spans("Vu bla")
                ),
                *self.make_text_spans("Ceci est du texte aléatoire qui n'est pas un visa."),
                self.make_semantic_tag(
                    VisaSegmentationSpec, contents=self.make_text_spans("Vu blo")
                ),
            ],
        )

    def test_variant_simple_inside_list(self):
        # Arrange
        elements = [
            self.make_semantic_tag(
                ListSegmentationSpec,
                contents=self.make_text_spans(
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
                self.make_semantic_tag(
                    MotifSegmentationSpec,
                    contents=self.make_text_spans("- Considérant que blabla ;"),
                ),
                self.make_semantic_tag(
                    MotifSegmentationSpec,
                    contents=self.make_text_spans("- Considérant que bloblo ;"),
                ),
            ],
        )

    def test_variant_simple_page_separator_interrupting_sentence(self):
        # Arrange
        elements = [
            *self.make_text_spans(
                "Vu le code de l'environnement, et notamment ses titres 1er et 4"
            ),
            self.make_semantic_tag(PageSeparatorSpec, data=PageSeparatorData(page_index=0)),
            *self.make_text_spans("des parties réglementaires et législatives du livre V ;"),
        ]

        # Act
        result = parse_visa_and_motif_elements(self.context, elements)

        # Assert
        assert_elements_equal(
            result,
            [
                self.make_semantic_tag(
                    VisaSegmentationSpec,
                    contents=[
                        *self.make_text_spans(
                            "Vu le code de l'environnement, et notamment ses titres 1er et 4",
                        ),
                        self.make_semantic_tag(
                            PageSeparatorSpec, data=PageSeparatorData(page_index=0)
                        ),
                        *self.make_text_spans(
                            "des parties réglementaires et législatives du livre V ;"
                        ),
                    ],
                ),
            ],
        )

    def test_variant_implicit_list(self):
        # Arrange
        elements = self.make_text_spans(
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
                *self.make_text_spans("CONSIDÉRANT : "),
                self.make_semantic_tag(
                    MotifSegmentationSpec,
                    contents=self.make_text_spans("que blabla ;"),
                ),
                self.make_semantic_tag(
                    MotifSegmentationSpec,
                    contents=self.make_text_spans("que bloblo ;"),
                ),
                self.make_semantic_tag(
                    MotifSegmentationSpec,
                    contents=self.make_text_spans("qu'en application de blibli ;"),
                ),
            ],
        )

    def test_variant_implicit_list_interrupted_by_page_footer(self):
        # Arrange
        elements = [
            *self.make_text_spans(
                "Vu : ",
                (
                    "le code de l'environnement, et notamment ses titres "
                    "1er et 4 des parties réglementaires et législatives du livre V ;"
                ),
            ),
            self.make_semantic_tag(
                PageFooterSpec,
                contents=wrap_in_tag(self.soup, "div", ["page 1"]),
            ),
            *self.make_text_spans(
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
                *self.make_text_spans("Vu : "),
                self.make_semantic_tag(
                    VisaSegmentationSpec,
                    contents=self.make_text_spans(
                        "le code de l'environnement, et notamment ses titres "
                        "1er et 4 des parties réglementaires et législatives du livre V ;",
                    ),
                ),
                self.make_semantic_tag(
                    PageFooterSpec,
                    contents=wrap_in_tag(self.soup, "div", ["page 1"]),
                ),
                self.make_semantic_tag(
                    VisaSegmentationSpec,
                    contents=self.make_text_spans(
                        "la nomenclature des installations classées codifiée à l'annexe "
                        "de l'article R511-9 du code de l'environnement ;",
                    ),
                ),
            ],
        )

    def test_variant_implicit_list_with_extra_spaces_after_considerant(self):
        # Arrange
        elements = [
            *self.make_text_spans(
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
                *self.make_text_spans(
                    "CONSIDÉRANT  ",
                ),
                self.make_semantic_tag(
                    MotifSegmentationSpec,
                    contents=self.make_text_spans("que le site a évolué"),
                ),
                self.make_semantic_tag(
                    MotifSegmentationSpec,
                    contents=self.make_text_spans("que les mesures concernent :"),
                ),
            ],
        )

    def test_variant_explicit_list(self):
        # Arrange
        elements = [
            *self.make_text_spans("Vu : "),
            self.make_semantic_tag(
                ListSegmentationSpec,
                contents=self.make_text_spans(
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
                *self.make_text_spans("Vu : "),
                self.make_semantic_tag(
                    VisaSegmentationSpec,
                    contents=self.make_text_spans("- le code de l'environnement ;"),
                ),
                self.make_semantic_tag(
                    VisaSegmentationSpec,
                    contents=self.make_text_spans("- la nomenclature des installations classées ;"),
                ),
            ],
        )

    def test_variant_explicit_list_interrupted(self):
        # Arrange
        elements = [
            *self.make_text_spans("Vu : "),
            self.make_semantic_tag(
                ListSegmentationSpec,
                contents=self.make_text_spans("- le code de l'environnement ;"),
            ),
            *self.make_text_spans("Ceci est du texte aléatoire qui n'est pas un visa."),
            self.make_semantic_tag(
                ListSegmentationSpec,
                contents=self.make_text_spans("- la nomenclature des installations classées ;"),
            ),
        ]

        # Act
        result = parse_visa_and_motif_elements(self.context, elements)

        # Assert
        assert_elements_equal(
            result,
            [
                *self.make_text_spans("Vu : "),
                self.make_semantic_tag(
                    VisaSegmentationSpec,
                    contents=self.make_text_spans("- le code de l'environnement ;"),
                ),
                *self.make_text_spans("Ceci est du texte aléatoire qui n'est pas un visa."),
                self.make_semantic_tag(
                    VisaSegmentationSpec,
                    contents=self.make_text_spans("- la nomenclature des installations classées ;"),
                ),
            ],
        )

    def test_variant_explicit_list_vu_inside_list_element(self):
        # Arrange
        elements = [
            *self.make_text_spans("Vu : "),
            self.make_semantic_tag(
                ListSegmentationSpec,
                contents=self.make_text_spans(
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
                *self.make_text_spans("Vu : "),
                self.make_semantic_tag(
                    VisaSegmentationSpec,
                    contents=self.make_text_spans("- le code de l'environnement ;"),
                ),
                self.make_semantic_tag(
                    VisaSegmentationSpec,
                    contents=self.make_text_spans("- la nomenclature des installations classées ;"),
                ),
                self.make_semantic_tag(
                    VisaSegmentationSpec,
                    contents=self.make_text_spans("- vu la demande déposée par la société XYZ ;"),
                ),
            ],
        )

    def test_variant_simple_with_list_inside_and_interrupted_by_page_separator(self):
        # Arrange
        elements = [
            *self.make_text_spans(
                "Considérant que la demande de modification sollicitée "
                "le 19 juillet 2021 porte sur:",
            ),
            self.make_semantic_tag(PageSeparatorSpec, data=PageSeparatorData(page_index=1)),
            self.make_semantic_tag(
                ListSegmentationSpec,
                contents=self.make_text_spans(
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
                self.make_semantic_tag(
                    MotifSegmentationSpec,
                    contents=[
                        *self.make_text_spans(
                            "Considérant que la demande de modification sollicitée "
                            "le 19 juillet 2021 porte sur:",
                        ),
                        self.make_semantic_tag(
                            PageSeparatorSpec, data=PageSeparatorData(page_index=1)
                        ),
                        self.make_semantic_tag(
                            ListSegmentationSpec,
                            contents=self.make_text_spans(
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
        )


class TestRenderHeaderElement(BaseTestCaseSegmentation):

    def test_make_header_element_tag(self):
        # Arrange
        contents = self.make_text_spans("liberté égalité fraternité")

        # Act
        rendered = _make_header_element_tag(self.context, EmblemSpec, contents)

        # Assert
        assert [str(tag) for tag in rendered] == [
            "<div>liberté </div>",
            "<div>égalité </div>",
            "<div>fraternité</div>",
        ]


class TestParseArreteTitle(BaseTestCaseSegmentation):

    def test_simple(self):
        # Arrange
        contents = self.make_text_spans(
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
                self.make_semantic_tag(
                    ArreteTitleSpec,
                    contents=[
                        self.make_tag(
                            "h1",
                            contents=[
                                "Arrêté du ",
                                self.make_semantic_tag(DateSpec, contents=["1er janvier 2020"]),
                            ],
                        )
                    ],
                ),
                *self.make_text_spans("Vu le blabla"),
            ],
        )


class TestParseEmblemElement(BaseTestCaseSegmentation):

    def test_simple(self):
        # Arrange
        contents = self.make_text_spans("liberté égalité fraternité")

        # Act
        results = parse_emblem_element(self.context, contents)

        # Assert
        assert_elements_equal(
            results,
            [
                self.make_semantic_tag(
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
        )


class TestParseEntityElement(BaseTestCaseSegmentation):

    def test_simple(self):
        # Arrange
        contents = self.make_text_spans("Ministère de la Transition écologique")

        # Act
        results = parse_entity_element(self.context, contents)

        # Assert
        assert_elements_equal(
            results,
            [
                self.make_semantic_tag(
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
        )


class TestParseIdentificationElement(BaseTestCaseSegmentation):

    def test_simple(self):
        # Arrange
        contents = self.make_text_spans("Référence : 2020-1234")

        # Act
        results = parse_identification_element(self.context, contents)

        # Assert
        assert_elements_equal(
            results,
            [
                self.make_semantic_tag(
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
        )


class TestParseHonoraryElement(BaseTestCaseSegmentation):
    def test_simple(self):
        # Arrange
        contents = self.make_text_spans(
            "La Directrice Générale de l'Agence Régionale de Santé Grand Est"
        )

        # Act
        results = parse_honorary_element(self.context, contents)

        # Assert
        assert_elements_equal(
            results,
            [
                self.make_semantic_tag(
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
        )


class TestParseSupplementaryMotifInfo(BaseTestCaseSegmentation):

    def test_simple(self):
        # Arrange
        contents = self.make_text_spans(
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
                self.make_semantic_tag(
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
        )
