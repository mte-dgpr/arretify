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
from arretify.semantic_tag_specs import DateSpec, DocumentReferenceData, DocumentReferenceSpec
from arretify.utils.testing import BaseTestCaseHtml, assert_element_lists_equal

from .arretes_detection import parse_arretes_references


class TestParseArreteReferences(BaseTestCaseHtml):

    def test_arrete_date1(self):
        # Arrange
        elements = ["Vu l'arrêté ministériel du 2 février 1998,"]

        # Act
        actual = parse_arretes_references(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                "Vu l'",
                self.make_semantic_tag(
                    DocumentReferenceSpec,
                    contents=[
                        "arrêté ministériel du ",
                        self.make_semantic_tag(
                            DateSpec,
                            contents=["2 février 1998"],
                            attrs=dict(datetime="1998-02-02"),
                        ),
                    ],
                    data=DocumentReferenceData(
                        type="arrete-ministeriel",
                        date="1998-02-02",
                    ),
                ),
                ",",
            ],
        )

    def test_arrete_date1_end_modifiant(self):
        # Arrange
        elements = [
            (
                "arrêté ministériel du 23 mai 2016 modifiant relatif aux installations de "
                "production de chaleur"
            )
        ]

        # Act
        actual = parse_arretes_references(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                self.make_semantic_tag(
                    DocumentReferenceSpec,
                    contents=[
                        "arrêté ministériel du ",
                        self.make_semantic_tag(
                            DateSpec,
                            contents=["23 mai 2016"],
                            attrs=dict(datetime="2016-05-23"),
                        ),
                        " modifiant",
                    ],
                    data=DocumentReferenceData(
                        type="arrete-ministeriel",
                        date="2016-05-23",
                    ),
                ),
                " relatif aux installations de production de chaleur",
            ],
        )

    def test_arrete_unknown(self):
        # Arrange
        elements = ["Vu l'arrêté du 2 février 1998,"]

        # Act
        actual = parse_arretes_references(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                "Vu l'",
                self.make_semantic_tag(
                    DocumentReferenceSpec,
                    contents=[
                        "arrêté du ",
                        self.make_semantic_tag(
                            DateSpec,
                            contents=["2 février 1998"],
                            attrs=dict(datetime="1998-02-02"),
                        ),
                    ],
                    data=DocumentReferenceData(
                        type="arrete",
                        date="1998-02-02",
                    ),
                ),
                ",",
            ],
        )

    def test_interrupted_inline_tag(self):
        # Arrange
        elements = [
            "Vu l'arrêté ministériel ",
            self.make_tag("br"),
            " du 2 février 1998,",
        ]

        # Act
        actual = parse_arretes_references(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                "Vu l'",
                self.make_semantic_tag(
                    DocumentReferenceSpec,
                    contents=[
                        "arrêté ministériel",
                        self.make_tag("br"),
                        " du ",
                        self.make_semantic_tag(
                            DateSpec,
                            contents=["2 février 1998"],
                            attrs=dict(datetime="1998-02-02"),
                        ),
                    ],
                    data=DocumentReferenceData(
                        type="arrete-ministeriel",
                        date="1998-02-02",
                    ),
                ),
                ",",
            ],
        )


class TestParseArretePluralReferences(BaseTestCaseHtml):

    def test_references_multiple(self):
        # Arrange
        elements = [
            "Les arrêtés préfectoraux n° 5213 du 28 octobre 1988 et n° 1636 du 24/03/95 blabla."
        ]

        # Act
        actual = parse_arretes_references(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                "Les ",
                "arrêtés préfectoraux ",
                self.make_semantic_tag(
                    DocumentReferenceSpec,
                    contents=[
                        "n° 5213 du ",
                        self.make_semantic_tag(
                            DateSpec,
                            contents=["28 octobre 1988"],
                            attrs=dict(datetime="1988-10-28"),
                        ),
                    ],
                    data=DocumentReferenceData(
                        type="arrete-prefectoral",
                        num="5213",
                        date="1988-10-28",
                    ),
                ),
                " et ",
                self.make_semantic_tag(
                    DocumentReferenceSpec,
                    contents=[
                        "n° 1636 du ",
                        self.make_semantic_tag(
                            DateSpec,
                            contents=["24/03/95"],
                            attrs=dict(datetime="1995-03-24"),
                        ),
                    ],
                    data=DocumentReferenceData(
                        type="arrete-prefectoral",
                        num="1636",
                        date="1995-03-24",
                    ),
                ),
                " blabla.",
            ],
        )


class TestParseArreteReferencesAll(BaseTestCaseHtml):

    def test_several_references(self):
        # Arrange
        elements = [
            (
                "Bla bla arrêté ministériel du 23 mai 2016 relatif aux installations de "
                "production de chaleur et arrêté préfectoral n° 1234-567/01."
            )
        ]

        # Act
        actual = parse_arretes_references(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                "Bla bla ",
                self.make_semantic_tag(
                    DocumentReferenceSpec,
                    contents=[
                        "arrêté ministériel du ",
                        self.make_semantic_tag(
                            DateSpec,
                            contents=["23 mai 2016"],
                            attrs=dict(datetime="2016-05-23"),
                        ),
                    ],
                    data=DocumentReferenceData(
                        type="arrete-ministeriel",
                        date="2016-05-23",
                    ),
                ),
                " relatif aux installations de production de chaleur et ",
                self.make_semantic_tag(
                    DocumentReferenceSpec,
                    contents=["arrêté préfectoral n° 1234-567/01."],
                    data=DocumentReferenceData(
                        type="arrete-prefectoral",
                        num="1234-567/01.",
                    ),
                ),
            ],
        )
