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

from arretify.utils.testing import (
    make_testing_function_for_single_tag,
    normalized_html_str,
    create_document_context,
)
from .codes_resolution import (
    resolve_code_article_legifrance_id,
    resolve_code_legifrance_id,
)
from arretify.law_data.types import Document, Section, DocumentType, SectionType

process_code_document_reference = make_testing_function_for_single_tag(resolve_code_legifrance_id)


class TestResolveSectionsDocuments(unittest.TestCase):
    def test_simple_article(self):
        # Arrange
        document_context = create_document_context(
            """
            <a
                class="dsr-section_reference"
                data-num="R541-15"
                data-type="article"
            >
                article R541-15
            </a>
        """
        )
        section_reference_tag = document_context.soup.select_one(".dsr-section_reference")
        document = Document(
            type=DocumentType.code,
            id="LEGITEXT000006074220",
        )
        sections = [
            Section(
                type=SectionType.ARTICLE,
                start_num="R541-15",
            ),
        ]

        # Act
        resolve_code_article_legifrance_id(
            document_context, section_reference_tag, document, sections
        )

        # Assert
        assert normalized_html_str(str(document_context.soup)) == normalized_html_str(
            """
                <a
                    class="dsr-section_reference"
                    data-id="LEGIARTI000032728274,"
                    data-num="R541-15,"
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
                class="dsr-section_reference"
                data-num="R541-15,R541-20"
                data-type="article"
            >
                articles R541-15 à R541-20
            </a>
        """
        )
        section_reference_tag = document_context.soup.select_one(".dsr-section_reference")
        document = Document(
            type=DocumentType.code,
            id="LEGITEXT000006074220",
        )
        sections = [
            Section(
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
        assert normalized_html_str(str(document_context.soup)) == normalized_html_str(
            """
            <a
                class="dsr-section_reference"
                data-id="LEGIARTI000032728274,LEGIARTI000028249688"
                data-num="R541-15,R541-20"
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
                class="dsr-document_reference"
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
                class="dsr-document_reference"
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
