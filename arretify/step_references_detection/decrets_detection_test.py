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

from .decrets_detection import parse_decrets_references


class TestParseDecretsReferences(BaseTestCaseHtml):

    def test_simple(self):
        # Arrange
        elements: list[ProtectedTagOrStr] = ["Bla bla décret n°2005-635 du 30 mai 2005 relatif à"]

        # Act
        actual = parse_decrets_references(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                "Bla bla ",
                self.make_semantic_tag(
                    DocumentReferenceSpec,
                    contents=[
                        "décret n°2005-635 du ",
                        self.make_semantic_tag(
                            DateSpec,
                            contents=["30 mai 2005"],
                            attrs=dict(datetime="2005-05-30"),
                        ),
                    ],
                    data=DocumentReferenceData(
                        type="decret",
                        date="2005-05-30",
                        num="2005-635",
                    ),
                ),
                " relatif à",
            ],
        )
