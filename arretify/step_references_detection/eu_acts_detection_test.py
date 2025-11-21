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

from .eu_acts_detection import parse_eu_acts_references

process_children = make_testing_function_for_children_list(parse_eu_acts_references)


class TestParseEuActsReferences(unittest.TestCase):

    def test_domain_before(self):
        assert process_children("Bla bla de la directive (CE) n° 1013/2006 du 22 juin 2006") == [
            "Bla bla de la ",
            normalized_html_str(
                """
                <a
                    data-date="2006"
                    data-num="1013"
                    data-spec="document_reference"
                    data-type="eu-directive"
                >
                    directive (CE) n° 1013/2006
                </a>
                """
            ),
            " du 22 juin 2006",
        ]

    def test_domain_after(self):
        assert process_children("VU la directive 2010/75/UE du 24 novembre 2010") == [
            "VU la ",
            normalized_html_str(
                """
                <a
                    data-date="2010"
                    data-num="75"
                    data-spec="document_reference"
                    data-type="eu-directive"
                >
                    directive 2010/75/UE
                </a>
                """
            ),
            " du 24 novembre 2010",
        ]

    def test_domain_after_year_2digits(self):
        assert process_children("VU la directive 96/75/UE du 24 novembre 1996") == [
            "VU la ",
            normalized_html_str(
                """
                <a
                    data-date="1996"
                    data-num="75"
                    data-spec="document_reference"
                    data-type="eu-directive"
                >
                    directive 96/75/UE
                </a>
                """
            ),
            " du 24 novembre 1996",
        ]

    def test_with_word_europeen(self):
        assert process_children("VU le règlement européen (CE) n° 1013/2006 du 22 juin 2006") == [
            "VU le ",
            normalized_html_str(
                """
                <a
                    data-date="2006"
                    data-num="1013"
                    data-spec="document_reference"
                    data-type="eu-regulation"
                >
                    règlement européen (CE) n° 1013/2006
                </a>
                """
            ),
            " du 22 juin 2006",
        ]

    def test_parsing_2digit_year(self):
        assert process_children("Bla bla de la directive (CE) n° 1013/96 du 12 aout 1996") == [
            "Bla bla de la ",
            normalized_html_str(
                """
                <a
                    data-date="1996"
                    data-num="1013"
                    data-spec="document_reference"
                    data-type="eu-directive"
                >
                    directive (CE) n° 1013/96
                </a>
                """
            ),
            " du 12 aout 1996",
        ]

    def test_ignore_if_malformed(self):
        assert process_children("VU la directive 96/75/POIPOI du 24 novembre 1996") == [
            "VU la directive 96/75/POIPOI du 24 novembre 1996",
        ]
