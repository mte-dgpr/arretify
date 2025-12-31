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
from arretify.semantic_tag_specs import DocumentReferenceData, DocumentReferenceSpec
from arretify.utils.testing import BaseTestCaseHtml, assert_element_lists_equal

from .self_detection import parse_self_references


class TestParseSelfReferences(BaseTestCaseHtml):

    def test_simple(self):
        # Arrange
        elements = ["l'article 8 du présent arrêté remplace"]

        # Act
        actual = parse_self_references(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                "l'article 8 du ",
                self.make_semantic_tag(
                    DocumentReferenceSpec,
                    contents=["présent arrêté"],
                    data=DocumentReferenceData(
                        type="self",
                    ),
                ),
                " remplace",
            ],
        )
