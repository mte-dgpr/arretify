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
from arretify.types import DocumentType
from arretify.utils.testing import BaseTestCaseHtml, assert_elements_equal

from .eu_acts_resolution import (
    resolve_eu_decision_eurlex_url,
    resolve_eu_directive_eurlex_url,
    resolve_eu_regulation_eurlex_url,
)


class TestResolveEuActUrls(BaseTestCaseHtml):
    def test_directive(self):
        # Arrange
        reference_tag = self.make_semantic_tag(
            DocumentReferenceSpec,
            data=DocumentReferenceData(type=DocumentType.eu_directive, date="2010", num="75"),
            contents=["directive 2010/75/UE"],
        )
        self.soup_extend([reference_tag])

        # Act
        resolve_eu_directive_eurlex_url(self.context, reference_tag)

        # Assert
        assert_elements_equal(
            reference_tag,
            self.make_semantic_tag(
                DocumentReferenceSpec,
                data=DocumentReferenceData(
                    type=DocumentType.eu_directive,
                    date="2010",
                    num="75",
                    id=(
                        "https://eur-lex.europa.eu/legal-content/FR/TXT/HTML/"
                        "?uri=cellar:c7191b72-4e07-4712-86d6-d3ae5e4f0082"
                    ),
                ),
                contents=["directive 2010/75/UE"],
                attrs=dict(
                    href=(
                        "https://eur-lex.europa.eu/legal-content/FR/TXT/HTML/"
                        "?uri=cellar:c7191b72-4e07-4712-86d6-d3ae5e4f0082"
                    )
                ),
            ),
        )

    def test_decision(self):
        # Arrange
        reference_tag = self.make_semantic_tag(
            DocumentReferenceSpec,
            data=DocumentReferenceData(type=DocumentType.eu_decision, date="2020", num="2019"),
            contents=["décision 2019/2020/UE"],
        )
        self.soup_extend([reference_tag])

        # Act
        resolve_eu_decision_eurlex_url(self.context, reference_tag)

        # Assert
        assert_elements_equal(
            reference_tag,
            self.make_semantic_tag(
                DocumentReferenceSpec,
                data=DocumentReferenceData(
                    type=DocumentType.eu_decision,
                    date="2020",
                    num="2019",
                    id=(
                        "https://eur-lex.europa.eu/legal-content/FR/TXT/HTML/"
                        "?uri=cellar:8e42e417-3ab2-11eb-b27b-01aa75ed71a1"
                    ),
                ),
                contents=["décision 2019/2020/UE"],
                attrs=dict(
                    href=(
                        "https://eur-lex.europa.eu/legal-content/FR/TXT/HTML/"
                        "?uri=cellar:8e42e417-3ab2-11eb-b27b-01aa75ed71a1"
                    )
                ),
            ),
        )

    def test_regulation(self):
        # Arrange
        reference_tag = self.make_semantic_tag(
            DocumentReferenceSpec,
            data=DocumentReferenceData(type=DocumentType.eu_regulation, date="2012", num="601"),
            contents=["règlement 2012/601/UE"],
        )
        self.soup_extend([reference_tag])

        # Act
        resolve_eu_regulation_eurlex_url(self.context, reference_tag)

        # Assert
        assert_elements_equal(
            reference_tag,
            self.make_semantic_tag(
                DocumentReferenceSpec,
                data=DocumentReferenceData(
                    type=DocumentType.eu_regulation,
                    date="2012",
                    num="601",
                    id=(
                        "https://eur-lex.europa.eu/legal-content/FR/TXT/HTML/"
                        "?uri=cellar:a025c83e-c7f9-4f94-87bb-3522f4ff930d"
                    ),
                ),
                contents=["règlement 2012/601/UE"],
                attrs=dict(
                    href=(
                        "https://eur-lex.europa.eu/legal-content/FR/TXT/HTML/"
                        "?uri=cellar:a025c83e-c7f9-4f94-87bb-3522f4ff930d"
                    )
                ),
            ),
        )
