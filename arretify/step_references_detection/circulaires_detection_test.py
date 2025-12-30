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
from arretify.types import ProtectedTagOrStr
from arretify.utils.testing import BaseTestCaseHtml, assert_element_lists_equal

from .circulaires_detection import parse_circulaires_references


class TestParseCirculairesReferences(BaseTestCaseHtml):

    def test_only_date(self):
        # Arrange
        elements: list[ProtectedTagOrStr] = ["Bla bla circulaire du 30 mai 2005 relative à"]

        # Act
        actual = parse_circulaires_references(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                "Bla bla ",
                self.make_semantic_tag(
                    DocumentReferenceSpec,
                    contents=[
                        "circulaire du ",
                        self.make_semantic_tag(
                            DateSpec,
                            contents=["30 mai 2005"],
                            attrs=dict(datetime="2005-05-30"),
                        ),
                    ],
                    data=DocumentReferenceData(
                        type="circulaire",
                        date="2005-05-30",
                    ),
                ),
                " relative à",
            ],
        )

    def test_with_ministerielle(self):
        # Arrange
        elements: list[ProtectedTagOrStr] = [
            "Bla bla circulaire ministérielle du 30 mai 2005 relative à"
        ]

        # Act
        actual = parse_circulaires_references(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                "Bla bla ",
                self.make_semantic_tag(
                    DocumentReferenceSpec,
                    contents=[
                        "circulaire ministérielle du ",
                        self.make_semantic_tag(
                            DateSpec,
                            contents=["30 mai 2005"],
                            attrs=dict(datetime="2005-05-30"),
                        ),
                    ],
                    data=DocumentReferenceData(
                        type="circulaire",
                        date="2005-05-30",
                    ),
                ),
                " relative à",
            ],
        )

    def test_with_random_acronym(self):
        # Arrange
        elements: list[ProtectedTagOrStr] = ["Bla bla circulaire DPPR/DE du 30 mai 2005 relative à"]

        # Act
        actual = parse_circulaires_references(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                "Bla bla ",
                self.make_semantic_tag(
                    DocumentReferenceSpec,
                    contents=[
                        "circulaire DPPR/DE du ",
                        self.make_semantic_tag(
                            DateSpec,
                            contents=["30 mai 2005"],
                            attrs=dict(datetime="2005-05-30"),
                        ),
                    ],
                    data=DocumentReferenceData(
                        type="circulaire",
                        date="2005-05-30",
                    ),
                ),
                " relative à",
            ],
        )

    def test_with_identifier_and_date(self):
        # Arrange
        elements: list[ProtectedTagOrStr] = [
            "Bla bla circulaire n°2005-12 du 30 mai 2005 relative à"
        ]

        # Act
        actual = parse_circulaires_references(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                "Bla bla ",
                self.make_semantic_tag(
                    DocumentReferenceSpec,
                    contents=[
                        "circulaire n°2005-12 du ",
                        self.make_semantic_tag(
                            DateSpec,
                            contents=["30 mai 2005"],
                            attrs=dict(datetime="2005-05-30"),
                        ),
                    ],
                    data=DocumentReferenceData(
                        type="circulaire",
                        date="2005-05-30",
                        num="2005-12",
                    ),
                ),
                " relative à",
            ],
        )
