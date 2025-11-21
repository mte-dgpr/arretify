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

from arretify.utils.testing import make_testing_function_for_children_list, normalized_html_str

from .circulaires_detection import parse_circulaires_references

process_children = make_testing_function_for_children_list(parse_circulaires_references)


class TestParseCirculairesReferences(unittest.TestCase):

    def test_only_date(self):
        assert process_children("Bla bla circulaire du 30 mai 2005 relative à") == [
            "Bla bla ",
            normalized_html_str(
                """
                <a
                    data-date="2005-05-30"
                    data-spec="document_reference"
                    data-type="circulaire"
                >
                    circulaire du
                    <time data-spec="date" datetime="2005-05-30">
                        30 mai 2005
                    </time>
                </a>
                """
            ),
            " relative à",
        ]

    def test_with_ministerielle(self):
        assert process_children("Bla bla circulaire ministérielle du 30 mai 2005 relative à") == [
            "Bla bla ",
            normalized_html_str(
                """
                <a
                    data-date="2005-05-30"
                    data-spec="document_reference"
                    data-type="circulaire"
                >
                    circulaire ministérielle du
                    <time data-spec="date" datetime="2005-05-30">
                        30 mai 2005
                    </time>
                </a>
                """
            ),
            " relative à",
        ]

    def test_with_random_acronym(self):
        assert process_children("Bla bla circulaire DPPR/DE du 30 mai 2005 relative à") == [
            "Bla bla ",
            normalized_html_str(
                """
                <a
                    data-date="2005-05-30"
                    data-spec="document_reference"
                    data-type="circulaire"
                >
                    circulaire DPPR/DE du
                    <time data-spec="date" datetime="2005-05-30">
                        30 mai 2005
                    </time>
                </a>
                """
            ),
            " relative à",
        ]

    def test_with_identifier_and_date(self):
        assert process_children("Bla bla circulaire n°2005-12 du 30 mai 2005 relative à") == [
            "Bla bla ",
            normalized_html_str(
                """
                <a
                    data-date="2005-05-30"
                    data-num="2005-12"
                    data-spec="document_reference"
                    data-type="circulaire"
                >
                    circulaire n°2005-12 du
                    <time data-spec="date" datetime="2005-05-30">
                        30 mai 2005
                    </time>
                </a>
                """
            ),
            " relative à",
        ]
