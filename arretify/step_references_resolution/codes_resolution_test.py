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
from arretify.semantic_tag_specs import (
    DocumentReferenceData,
    DocumentReferenceSpec,
    SectionReferenceData,
    SectionReferenceSpec,
)
from arretify.types import DocumentType, SectionType
from arretify.utils.testing import BaseTestCaseHtml, assert_elements_equal

from .codes_resolution import resolve_code_article_legifrance_id, resolve_code_legifrance_id


class TestResolveSectionsDocuments(BaseTestCaseHtml):
    def test_simple_article(self):
        # Arrange
        section_reference_tag = self.make_semantic_tag(
            SectionReferenceSpec,
            data=SectionReferenceData(
                type=SectionType.ARTICLE,
                start_num="R541-15",
            ),
            contents=["article R541-15"],
        )
        self.soup_extend([section_reference_tag])

        document = DocumentReferenceData(
            type=DocumentType.code,
            id="LEGITEXT000006074220",
        )
        sections = [
            SectionReferenceData(
                type=SectionType.ARTICLE,
                start_num="R541-15",
            ),
        ]

        # Act
        resolve_code_article_legifrance_id(self.context, section_reference_tag, document, sections)

        # Assert
        assert_elements_equal(
            section_reference_tag,
            self.make_semantic_tag(
                SectionReferenceSpec,
                data=SectionReferenceData(
                    type=SectionType.ARTICLE,
                    start_num="R541-15",
                    start_id="LEGIARTI000032728274",
                ),
                contents=["article R541-15"],
                attrs=dict(
                    href="https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000032728274"
                ),
            ),
        )

    def test_article_range(self):
        # Arrange
        section_reference_tag = self.make_semantic_tag(
            SectionReferenceSpec,
            data=SectionReferenceData(
                type=SectionType.ARTICLE,
                start_num="R541-15",
                end_num="R541-20",
            ),
            contents=["articles R541-15 à R541-20"],
        )
        self.soup_extend([section_reference_tag])

        document = DocumentReferenceData(
            type=DocumentType.code,
            id="LEGITEXT000006074220",
        )
        sections = [
            SectionReferenceData(
                type=SectionType.ARTICLE,
                start_num="R541-15",
                end_num="R541-20",
            ),
        ]

        # Act
        resolve_code_article_legifrance_id(self.context, section_reference_tag, document, sections)

        # Assert
        assert_elements_equal(
            section_reference_tag,
            self.make_semantic_tag(
                SectionReferenceSpec,
                data=SectionReferenceData(
                    type=SectionType.ARTICLE,
                    start_num="R541-15",
                    end_num="R541-20",
                    start_id="LEGIARTI000032728274",
                    end_id="LEGIARTI000028249688",
                ),
                contents=["articles R541-15 à R541-20"],
                attrs=dict(
                    href="https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000032728274"
                ),
            ),
        )


class TestResolveCodeDocuments(BaseTestCaseHtml):
    def test_resolve_code(self):
        # Arrange
        reference_tag = self.make_semantic_tag(
            DocumentReferenceSpec,
            data=DocumentReferenceData(type=DocumentType.code, title="Code de l'environnement"),
            contents=["code de l'environnemenent"],
        )
        self.soup_extend([reference_tag])

        # Act
        resolve_code_legifrance_id(self.context, reference_tag)

        # Assert
        assert_elements_equal(
            reference_tag,
            self.make_semantic_tag(
                DocumentReferenceSpec,
                data=DocumentReferenceData(
                    type=DocumentType.code,
                    title="Code de l'environnement",
                    id="LEGITEXT000006074220",
                ),
                contents=["code de l'environnemenent"],
                attrs=dict(
                    href="https://www.legifrance.gouv.fr/codes/texte_lc/LEGITEXT000006074220"
                ),
            ),
        )
