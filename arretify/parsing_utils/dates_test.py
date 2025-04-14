import unittest
from datetime import date

from bs4 import BeautifulSoup

from .dates import (
    DATE_NODE,
    parse_date_str,
    render_date_str,
    render_date_regex_tree_match,
    parse_year_str,
    render_year_str,
)
from arretify.regex_utils import (
    map_regex_tree_match,
    split_string_with_regex_tree,
)


class TestStrToDateAndDateToStr(unittest.TestCase):
    def test_parse_date_str(self):
        assert parse_date_str("1997-09-12") == date(year=1997, month=9, day=12)

    def test_render_date_str(self):
        assert render_date_str(date(year=2001, month=1, day=31)) == "2001-01-31"


class TestParseYearStrAndRenderYearStr(unittest.TestCase):
    def test_parse_year_2digits(self):
        assert parse_year_str("00") == 2000
        assert parse_year_str("99") == 1999

    def test_parse_year_4digits(self):
        assert parse_year_str("2000") == 2000
        assert parse_year_str("1999") == 1999

    def test_render_year_str(self):
        assert render_year_str(2000) == "2000"
        assert render_year_str(1999) == "1999"


class TestRenderDateRegexTreeMatch(unittest.TestCase):

    def test_with_alinea(self):
        assert _parsed_elements("24/03/95") == [
            '<time class="dsr-date" datetime="1995-03-24">24/03/95</time>'
        ]

    def test_date1_valid_cases(self):
        assert _parsed_elements("1er janvier 2023") == [
            '<time class="dsr-date" datetime="2023-01-01">1er janvier 2023</time>'
        ]
        assert _parsed_elements("15 février 2020") == [
            '<time class="dsr-date" datetime="2020-02-15">15 février 2020</time>'
        ]
        assert _parsed_elements("3 mars 99") == [
            '<time class="dsr-date" datetime="1999-03-03">3 mars 99</time>'
        ]
        assert _parsed_elements("10 octobre 2000") == [
            '<time class="dsr-date" datetime="2000-10-10">10 octobre 2000</time>'
        ]
        assert _parsed_elements("1er décembre 1999") == [
            '<time class="dsr-date" datetime="1999-12-01">1er décembre 1999</time>'
        ]
        assert _parsed_elements("1 janvier 20") == [
            '<time class="dsr-date" datetime="2020-01-01">1 janvier 20</time>'
        ]

    def test_date_without_accents_valid_cases(self):
        assert _parsed_elements("15 fevrier 2020") == [
            '<time class="dsr-date" datetime="2020-02-15">15 fevrier 2020</time>'
        ]
        assert _parsed_elements("15 aout 2020") == [
            '<time class="dsr-date" datetime="2020-08-15">15 aout 2020</time>'
        ]
        assert _parsed_elements("15 decembre 2020") == [
            '<time class="dsr-date" datetime="2020-12-15">15 decembre 2020</time>'
        ]

    def test_date2_valid_cases(self):
        assert _parsed_elements("15/02/2023") == [
            '<time class="dsr-date" datetime="2023-02-15">15/02/2023</time>'
        ]
        assert _parsed_elements("03/03/99") == [
            '<time class="dsr-date" datetime="1999-03-03">03/03/99</time>'
        ]
        assert _parsed_elements("10/10/2000") == [
            '<time class="dsr-date" datetime="2000-10-10">10/10/2000</time>'
        ]
        assert _parsed_elements("01/12/1999") == [
            '<time class="dsr-date" datetime="1999-12-01">01/12/1999</time>'
        ]
        assert _parsed_elements("31/01/1990") == [
            '<time class="dsr-date" datetime="1990-01-31">31/01/1990</time>'
        ]

    def test_edge_cases(self):
        assert _parsed_elements("1er janvier 00") == [
            '<time class="dsr-date" datetime="2000-01-01">1er janvier 00</time>'
        ]
        assert _parsed_elements("1 janvier 99") == [
            '<time class="dsr-date" datetime="1999-01-01">1 janvier 99</time>'
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
            '<time class="dsr-date" datetime="2023-01-01">1er janvier 2023</time>',
            ". Bla",
        ]
        assert _parsed_elements("15 février 2020 ") == [
            '<time class="dsr-date" datetime="2020-02-15">15 février 2020</time>',
            " ",
        ]
        assert _parsed_elements("15/02/2023)") == [
            '<time class="dsr-date" datetime="2023-02-15">15/02/2023</time>',
            ")",
        ]


def _parsed_elements(string: str) -> list[str]:
    soup = BeautifulSoup(string, features="html.parser")
    elements = map_regex_tree_match(
        split_string_with_regex_tree(DATE_NODE, string),
        lambda regex_tree_match: render_date_regex_tree_match(soup, regex_tree_match),
        allowed_group_names=[DATE_NODE.group_name],
    )
    return [str(element) for element in elements]
