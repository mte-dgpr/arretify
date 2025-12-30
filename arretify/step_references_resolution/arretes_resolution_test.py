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
from arretify.types import DocumentType
from arretify.utils.testing import BaseTestCaseHtml, assert_elements_equal

from .arretes_resolution import resolve_arrete_ministeriel_legifrance_id


class TestResolveArreteMinisterielLegifranceId(BaseTestCaseHtml):
    def test_resolve_simple(self):
        # Arrange
        date_tag = self.make_semantic_tag(
            DateSpec, contents=["2 février 1998"], attrs=dict(datetime="1998-02-02")
        )
        reference_tag = self.make_semantic_tag(
            DocumentReferenceSpec,
            data=DocumentReferenceData(type=DocumentType.arrete_ministeriel, date="1998-02-02"),
            contents=["arrêté ministériel du ", date_tag],
        )
        self.soup_extend(
            [
                reference_tag,
                (
                    " relatif aux prélèvements et à la consommation d'eau ainsi"
                    " qu'aux émissions de toute nature des installations classées"
                    " pour la protection de l'environnement soumises à autorisation"
                ),
            ]
        )

        # Act
        resolve_arrete_ministeriel_legifrance_id(self.context, reference_tag)

        # Assert
        assert_elements_equal(
            reference_tag,
            self.make_semantic_tag(
                DocumentReferenceSpec,
                data=DocumentReferenceData(
                    type=DocumentType.arrete_ministeriel,
                    date="1998-02-02",
                    id="JORFTEXT000000204891",
                ),
                contents=["arrêté ministériel du ", date_tag],
                attrs=dict(href="https://www.legifrance.gouv.fr/jorf/id/JORFTEXT000000204891"),
            ),
        )
