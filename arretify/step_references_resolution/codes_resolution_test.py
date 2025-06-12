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
)
from .codes_resolution import (
    resolve_code_article_legifrance_id,
    resolve_code_legifrance_id,
)

process_code_document_reference = make_testing_function_for_single_tag(resolve_code_legifrance_id)
process_code_article_section_reference = make_testing_function_for_single_tag(
    resolve_code_article_legifrance_id
)


class TestResolveSectionsDocuments(unittest.TestCase):
    def test_simple_article(self):
        assert (
            process_code_article_section_reference(
                """
            <a
                class="dsr-section_reference"
                data-uri="dsr://code_LEGITEXT000006074220___/article__R541-15__"
            >
                article R541-15
            </a>
            """
            )
            == normalized_html_str(
                """
            <a
                class="dsr-section_reference"
                data-uri="dsr://code_LEGITEXT000006074220___/article_LEGIARTI000032728274_R541-15__"
                href="https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000032728274"
            >
                article R541-15
            </a>
            """
            )
        )

    def test_article_range(self):
        assert (
            process_code_article_section_reference(
                """
            <a
                class="dsr-section_reference"
                data-uri="dsr://code_LEGITEXT000006074220___/article__R541-15__R541-20"
            >
                articles R541-15 à R541-20
            </a>
            """
            )
            == normalized_html_str(
                """
            <a
                class="dsr-section_reference"
                data-uri="dsr://code_LEGITEXT000006074220___/article_LEGIARTI000032728274_R541-15_LEGIARTI000028249688_R541-20"
                href="https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000032728274"
            >
                articles R541-15 à R541-20
            </a>
            """
            )
        )


class TestResolveCodeDocuments(unittest.TestCase):
    def test_resolve_code(self):
        assert (
            process_code_document_reference(
                """
            <a
                class="dsr-document_reference"
                data-uri="dsr://code____Code%20de%20l%27environnement"
            >
                code de l'environnemenent
            </a>
            """
            )
            == normalized_html_str(
                """
            <a
                class="dsr-document_reference"
                data-uri="dsr://code_LEGITEXT000006074220___Code%20de%20l%27environnement"
                href="https://www.legifrance.gouv.fr/codes/texte_lc/LEGITEXT000006074220"
            >
                code de l'environnemenent
            </a>
            """
            )
        )
