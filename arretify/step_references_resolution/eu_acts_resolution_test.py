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

from arretify.utils.testing import make_testing_function_for_single_tag, normalized_html_str

from .eu_acts_resolution import (
    resolve_eu_decision_eurlex_url,
    resolve_eu_directive_eurlex_url,
    resolve_eu_regulation_eurlex_url,
)

process_eu_directive_document_reference = make_testing_function_for_single_tag(
    resolve_eu_directive_eurlex_url
)
process_eu_decision_document_reference = make_testing_function_for_single_tag(
    resolve_eu_decision_eurlex_url
)
process_eu_regulation_document_reference = make_testing_function_for_single_tag(
    resolve_eu_regulation_eurlex_url
)


class TestResolveEuActUrls(unittest.TestCase):
    def test_directive(self):
        assert (
            process_eu_directive_document_reference(
                """
            <a
                data-spec="document_reference"
                data-date="2010"
                data-num="75"
                data-type="eu-directive"
            >
                directive 2010/75/UE
            </a>
            """
            )
            == normalized_html_str(
                """
            <a
                data-spec="document_reference"
                data-date="2010"
                data-id="https://eur-lex.europa.eu/legal-content/FR/TXT/HTML/?uri=cellar:c7191b72-4e07-4712-86d6-d3ae5e4f0082"
                data-num="75"
                data-type="eu-directive"
                href="https://eur-lex.europa.eu/legal-content/FR/TXT/HTML/?uri=cellar:c7191b72-4e07-4712-86d6-d3ae5e4f0082"
            >
                directive 2010/75/UE
            </a>
            """
            )
        )

    def test_decision(self):
        assert (
            process_eu_decision_document_reference(
                """
            <a
                data-spec="document_reference"
                data-date="2020"
                data-num="2019"
                data-type="eu-decision"
            >
                décision 2019/2020/UE
            </a>
            """
            )
            == normalized_html_str(
                """
            <a
                data-spec="document_reference"
                data-date="2020"
                data-id="https://eur-lex.europa.eu/legal-content/FR/TXT/HTML/?uri=cellar:8e42e417-3ab2-11eb-b27b-01aa75ed71a1"
                data-num="2019"
                data-type="eu-decision"
                href="https://eur-lex.europa.eu/legal-content/FR/TXT/HTML/?uri=cellar:8e42e417-3ab2-11eb-b27b-01aa75ed71a1"
            >
                décision 2019/2020/UE
            </a>
            """
            )
        )

    def test_regulation(self):
        assert (
            process_eu_regulation_document_reference(
                """
            <a
                data-spec="document_reference"
                data-date="2012"
                data-num="601"
                data-type="eu-regulation"
            >
                règlement 2012/601/UE
            </a>
            """
            )
            == normalized_html_str(
                """
            <a
                data-spec="document_reference"
                data-date="2012"
                data-id="https://eur-lex.europa.eu/legal-content/FR/TXT/HTML/?uri=cellar:a025c83e-c7f9-4f94-87bb-3522f4ff930d"
                data-num="601"
                data-type="eu-regulation"
                href="https://eur-lex.europa.eu/legal-content/FR/TXT/HTML/?uri=cellar:a025c83e-c7f9-4f94-87bb-3522f4ff930d"
            >
                règlement 2012/601/UE
            </a>
            """
            )
        )
