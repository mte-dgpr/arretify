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

from arretify.semantic_tag_specs import DocumentReferenceData, SectionReferenceData
from arretify.types import DocumentType, SectionType
from arretify.utils.testing import (
    create_document_context,
    make_testing_function_for_single_tag,
    normalized_html_str,
)

from .codes_resolution import resolve_code_article_legifrance_id, resolve_code_legifrance_id

process_code_document_reference = make_testing_function_for_single_tag(resolve_code_legifrance_id)


class TestResolveSectionsDocuments(unittest.TestCase):
    def test_simple_article(self):
        # Arrange
        document_context = create_document_context(
            """
            <a
                data-spec="section_reference"
                data-start_num="R541-15"
                data-type="article"
            >
                article R541-15
            </a>
        """
        )
        section_reference_tag = document_context.protected_soup.select_one(
            "[data-spec='section_reference']"
        )
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
        resolve_code_article_legifrance_id(
            document_context, section_reference_tag, document, sections
        )

        # Assert
        assert normalized_html_str(str(document_context.protected_soup)) == normalized_html_str(
            """
                <a
                    data-spec="section_reference"
                    data-start_id="LEGIARTI000032728274"
                    data-start_num="R541-15"
                    data-type="article"
                    href="https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000032728274"
                >
                    article R541-15
                </a>
            """
        )

    def test_article_range(self):
        # Arrange
        document_context = create_document_context(
            """
            <a
                data-spec="section_reference"
                data-end_num="R541-20"
                data-start_num="R541-15"
                data-type="article"
            >
                articles R541-15 à R541-20
            </a>
        """
        )
        section_reference_tag = document_context.protected_soup.select_one(
            "[data-spec='section_reference']"
        )
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
        resolve_code_article_legifrance_id(
            document_context, section_reference_tag, document, sections
        )

        # Assert
        assert normalized_html_str(str(document_context.protected_soup)) == normalized_html_str(
            """
            <a
                data-spec="section_reference"
                data-end_id="LEGIARTI000028249688"
                data-end_num="R541-20"
                data-start_id="LEGIARTI000032728274"
                data-start_num="R541-15"
                data-type="article"
                href="https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000032728274"
            >
                articles R541-15 à R541-20
            </a>
            """
        )


class TestResolveCodeDocuments(unittest.TestCase):
    def test_resolve_code(self):
        assert (
            process_code_document_reference(
                """
            <a
                data-spec="document_reference"
                data-title="Code de l'environnement"
                data-type="code"
            >
                code de l'environnemenent
            </a>
            """
            )
            == normalized_html_str(
                """
            <a
                data-spec="document_reference"
                data-id="LEGITEXT000006074220"
                data-title="Code de l'environnement"
                data-type="code"
                href="https://www.legifrance.gouv.fr/codes/texte_lc/LEGITEXT000006074220"
            >
                code de l'environnemenent
            </a>
            """
            )
        )
