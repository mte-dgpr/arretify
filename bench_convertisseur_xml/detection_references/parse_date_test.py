import re
from typing import Dict
import unittest
from datetime import date

from .parse_date import parse_date, DATE1_RE, DATE2_RE

def _run_search(re_str: str, date_str: str) -> Dict | None:
    match = re.search(re_str, date_str)
    return match.groupdict() if match else None

class TestParseDateFunction(unittest.TestCase):
    def test_date1_valid_cases(self):
        # Test valid "DATE1_RE" cases
        assert parse_date(_run_search(DATE1_RE, "1er janvier 2023")) == date(2023, 1, 1)
        assert parse_date(_run_search(DATE1_RE, "15 fevrier 2020")) == date(2020, 2, 15)
        assert parse_date(_run_search(DATE1_RE, "3 mars 99")) == date(1999, 3, 3)
        assert parse_date(_run_search(DATE1_RE, "10 octobre 2000")) == date(2000, 10, 10)
        assert parse_date(_run_search(DATE1_RE, "1er decembre 1999")) == date(1999, 12, 1)
        assert parse_date(_run_search(DATE1_RE, "1 janvier 20")) == date(2020, 1, 1)

    def test_date2_valid_cases(self):
        # Test valid "DATE2_RE" cases
        assert parse_date(_run_search(DATE2_RE, "15/02/2023")) == date(2023, 2, 15)
        assert parse_date(_run_search(DATE2_RE, "03/03/99")) == date(1999, 3, 3)
        assert parse_date(_run_search(DATE2_RE, "10/10/2000")) == date(2000, 10, 10)
        assert parse_date(_run_search(DATE2_RE, "01/12/1999")) == date(1999, 12, 1)
        assert parse_date(_run_search(DATE2_RE, "31/01/1990")) == date(1990, 1, 31)

    def test_date1_invalid_cases(self):
        # Test invalid "DATE1_RE" cases
        assert _run_search(DATE1_RE, "janvier 2023") is None # Missing day
        assert _run_search(DATE1_RE, "1 janvier") is None # Missing year
        assert _run_search(DATE1_RE, "1er unknownmonth 2023") is None # Invalid month
        assert _run_search(DATE1_RE, "1er janvier 23a") is None # Invalid year format

    def test_date2_invalid_cases(self):
        # Test invalid "DATE2_RE" cases
        assert _run_search(DATE1_RE, "15/02") is None # Missing year
        assert _run_search(DATE1_RE, "15/02/20a3") is None # Invalid year format
        assert _run_search(DATE1_RE, "15-02-2023") is None # Wrong delimiter
        assert _run_search(DATE1_RE, "15//2023") is None # Missing month

    def test_ambiguous_or_malformed_inputs(self):
        # Test ambiguous or malformed inputs
        assert _run_search(DATE1_RE, "2023 janvier 1er") is None # Wrong order
        assert _run_search(DATE2_RE, "15/02/99/extra") is None # Extra text

    def test_edge_cases(self):
        # Test edge cases
        assert parse_date(_run_search(DATE1_RE, "1er janvier 00")) == date(2000, 1, 1)  # Year 200
        assert parse_date(_run_search(DATE1_RE, "1 janvier 99")) == date(1999, 1, 1)  # Year 199
        assert _run_search(DATE1_RE, "") is None # Empty string
