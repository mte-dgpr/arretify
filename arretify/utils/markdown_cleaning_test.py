import unittest

from .markdown_cleaning import (
    _clean_failed_month_abbreviations,
)


class TestCleanFailedMonthAbbreviations(unittest.TestCase):
    def test_clean_failed_month_abbreviations(self):
        # Arrange
        test_line = "Aux jours du 8 janv, du 6 juill, et du 10 août 2010"
        expected_line = "Aux jours du 8 janv. du 6 juill. et du 10 août 2010"

        # Act
        result = _clean_failed_month_abbreviations(test_line)

        # Assert
        assert result == expected_line

    def test_shouldn_match_correct_months(self):
        # Arrange
        test_line = "Aux jours du 8 janv. du 6 juillet et du 10 août 2010"
        expected_line = "Aux jours du 8 janv. du 6 juillet et du 10 août 2010"

        # Act
        result = _clean_failed_month_abbreviations(test_line)

        # Assert
        assert result == expected_line
