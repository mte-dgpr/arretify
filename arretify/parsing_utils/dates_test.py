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
from typing import cast

from bs4 import BeautifulSoup

from arretify.types import ProtectedSoup, ProtectedTagOrStr
from arretify.utils.html_split_merge import make_regex_tree_splitter
from arretify.utils.split_merge import split_and_map_elements

from .dates import DATE_NODE, render_date_regex_tree_match


class TestRenderDateRegexTreeMatch(unittest.TestCase):

    def test_with_alinea(self):
        assert _parsed_elements("24/03/95") == [
            '<time data-spec="date" datetime="1995-03-24">24/03/95</time>'
        ]

    def test_date1_valid_cases(self):
        assert _parsed_elements("1er janvier 2023") == [
            '<time data-spec="date" datetime="2023-01-01">1er janvier 2023</time>'
        ]
        assert _parsed_elements("15 février 2020") == [
            '<time data-spec="date" datetime="2020-02-15">15 février 2020</time>'
        ]
        assert _parsed_elements("3 mars 99") == [
            '<time data-spec="date" datetime="1999-03-03">3 mars 99</time>'
        ]
        assert _parsed_elements("10 octobre 2000") == [
            '<time data-spec="date" datetime="2000-10-10">10 octobre 2000</time>'
        ]
        assert _parsed_elements("1er décembre 1999") == [
            '<time data-spec="date" datetime="1999-12-01">1er décembre 1999</time>'
        ]
        assert _parsed_elements("1 janvier 20") == [
            '<time data-spec="date" datetime="2020-01-01">1 janvier 20</time>'
        ]

    def test_date_without_accents_valid_cases(self):
        assert _parsed_elements("15 fevrier 2020") == [
            '<time data-spec="date" datetime="2020-02-15">15 fevrier 2020</time>'
        ]
        assert _parsed_elements("15 aout 2020") == [
            '<time data-spec="date" datetime="2020-08-15">15 aout 2020</time>'
        ]
        assert _parsed_elements("15 decembre 2020") == [
            '<time data-spec="date" datetime="2020-12-15">15 decembre 2020</time>'
        ]

    def test_date2_valid_cases(self):
        assert _parsed_elements("15/02/2023") == [
            '<time data-spec="date" datetime="2023-02-15">15/02/2023</time>'
        ]
        assert _parsed_elements("03/03/99") == [
            '<time data-spec="date" datetime="1999-03-03">03/03/99</time>'
        ]
        assert _parsed_elements("10/10/2000") == [
            '<time data-spec="date" datetime="2000-10-10">10/10/2000</time>'
        ]
        assert _parsed_elements("01/12/1999") == [
            '<time data-spec="date" datetime="1999-12-01">01/12/1999</time>'
        ]
        assert _parsed_elements("31/01/1990") == [
            '<time data-spec="date" datetime="1990-01-31">31/01/1990</time>'
        ]

    def test_edge_cases(self):
        assert _parsed_elements("1er janvier 00") == [
            '<time data-spec="date" datetime="2000-01-01">1er janvier 00</time>'
        ]
        assert _parsed_elements("1 janvier 99") == [
            '<time data-spec="date" datetime="1999-01-01">1 janvier 99</time>'
        ]

    def test_date_invalid_cases(self):
        assert _parsed_elements("janvier 2023") == ["janvier 2023"]  # Missing day
        assert _parsed_elements("1 janvier") == ["1 janvier"]  # Missing year
        assert _parsed_elements("1er unknownmonth 2023") == [
            "1er unknownmonth 2023"
        ]  # Invalid month
        assert _parsed_elements("15/02/20a3") == ["15/02/20a3"]  # Invalid year format
        assert _parsed_elements("2023 janvier 1er") == ["2023 janvier 1er"]  # Wrong order

    def test_date1_and_date2_end_characters_cases(self):
        assert _parsed_elements("1er janvier 2023. Bla") == [
            '<time data-spec="date" datetime="2023-01-01">1er janvier 2023</time>',
            ". Bla",
        ]
        assert _parsed_elements("15 février 2020 ") == [
            '<time data-spec="date" datetime="2020-02-15">15 février 2020</time>',
            " ",
        ]
        assert _parsed_elements("15/02/2023)") == [
            '<time data-spec="date" datetime="2023-02-15">15/02/2023</time>',
            ")",
        ]

    def test_abbreviation_month(self):
        assert _parsed_elements("20 AVR. 2020") == [
            '<time data-spec="date" datetime="2020-04-20">20 AVR. 2020</time>',
        ]

    def test_3_chars_month(self):
        assert _parsed_elements("20 JUL 2020") == [
            '<time data-spec="date" datetime="2020-07-20">20 JUL 2020</time>',
        ]

    def test_syntactically_valid_but_non_existant_date(self):
        assert _parsed_elements("31 FEV 2013") == [
            '<time data-error_codes="non_existant_date" data-spec="date" '
            'datetime="0001-01-01">31 FEV 2013</time>',
        ]


def _parsed_elements(string: str) -> list[str]:
    soup = cast(ProtectedSoup, BeautifulSoup(string, features="html.parser"))
    elements: list[ProtectedTagOrStr] = [string]
    elements = split_and_map_elements(
        elements,
        make_regex_tree_splitter(DATE_NODE),
        lambda regex_tree_match: render_date_regex_tree_match(soup, regex_tree_match),
    )
    return [str(element) for element in elements]
