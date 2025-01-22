import re
from typing import Dict
import unittest
from datetime import date

from bench_convertisseur_xml.utils.regex import search_groupdict

from .dates import handle_date_match_groupdict, DATE1_RES, DATE2_RES, parse_date_attribute, render_date_attribute


class TestParseDateFunction(unittest.TestCase):
    def test_date1_valid_cases(self):
        # Test valid "DATE1_RES" cases
        assert handle_date_match_groupdict(search_groupdict(DATE1_RES, "1er janvier 2023")) == date(2023, 1, 1)
        assert handle_date_match_groupdict(search_groupdict(DATE1_RES, "15 février 2020")) == date(2020, 2, 15)
        assert handle_date_match_groupdict(search_groupdict(DATE1_RES, "3 mars 99")) == date(1999, 3, 3)
        assert handle_date_match_groupdict(search_groupdict(DATE1_RES, "10 octobre 2000")) == date(2000, 10, 10)
        assert handle_date_match_groupdict(search_groupdict(DATE1_RES, "1er décembre 1999")) == date(1999, 12, 1)
        assert handle_date_match_groupdict(search_groupdict(DATE1_RES, "1 janvier 20")) == date(2020, 1, 1)

    def test_date2_valid_cases(self):
        # Test valid "DATE2_RES" cases
        assert handle_date_match_groupdict(search_groupdict(DATE2_RES, "15/02/2023")) == date(2023, 2, 15)
        assert handle_date_match_groupdict(search_groupdict(DATE2_RES, "03/03/99")) == date(1999, 3, 3)
        assert handle_date_match_groupdict(search_groupdict(DATE2_RES, "10/10/2000")) == date(2000, 10, 10)
        assert handle_date_match_groupdict(search_groupdict(DATE2_RES, "01/12/1999")) == date(1999, 12, 1)
        assert handle_date_match_groupdict(search_groupdict(DATE2_RES, "31/01/1990")) == date(1990, 1, 31)

    def test_date1_invalid_cases(self):
        # Test invalid "DATE1_RES" cases
        assert search_groupdict(DATE1_RES, "janvier 2023") is None # Missing day
        assert search_groupdict(DATE1_RES, "1 janvier") is None # Missing year
        assert search_groupdict(DATE1_RES, "1er unknownmonth 2023") is None # Invalid month
        assert search_groupdict(DATE1_RES, "1er janvier 23a") is None # Invalid year format

    def test_date2_invalid_cases(self):
        # Test invalid "DATE2_RES" cases
        assert search_groupdict(DATE1_RES, "15/02") is None # Missing year
        assert search_groupdict(DATE1_RES, "15/02/20a3") is None # Invalid year format
        assert search_groupdict(DATE1_RES, "15-02-2023") is None # Wrong delimiter
        assert search_groupdict(DATE1_RES, "15//2023") is None # Missing month

    def test_ambiguous_or_malformed_inputs(self):
        # Test ambiguous or malformed inputs
        assert search_groupdict(DATE1_RES, "2023 janvier 1er") is None # Wrong order
        assert search_groupdict(DATE2_RES, "15/02/99/extra") is None # Extra text

    def test_edge_cases(self):
        # Test edge cases
        assert handle_date_match_groupdict(search_groupdict(DATE1_RES, "1er janvier 00")) == date(2000, 1, 1)  # Year 200
        assert handle_date_match_groupdict(search_groupdict(DATE1_RES, "1 janvier 99")) == date(1999, 1, 1)  # Year 199
        assert search_groupdict(DATE1_RES, "") is None # Empty string

    def test_date1_and_date2_end_characters_cases(self):
        # Test valid "DATE1_RES" cases
        assert handle_date_match_groupdict(search_groupdict(DATE1_RES, "1er janvier 2023. Bla")) == date(2023, 1, 1)
        assert handle_date_match_groupdict(search_groupdict(DATE1_RES, "15 février 2020 ")) == date(2020, 2, 15)
        # Test valid "DATE2_RES" cases
        assert handle_date_match_groupdict(search_groupdict(DATE2_RES, "15/02/2023)")) == date(2023, 2, 15)


class TestStrToDateAndDateToStr(unittest.TestCase):
    def test_parse_date_attribute(self):
        assert parse_date_attribute('1997-09-12') == date(year=1997, month=9, day=12)

    def test_render_date_attribute(self):
        assert render_date_attribute(date(year=2001, month=1, day=31)) == '2001-01-31'