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

from .markdown_cleaning import _clean_failed_month_abbreviations, clean_markdown


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


class TestCleanMarkdown(unittest.TestCase):

    def test_remove_newline_at_end(self):
        # Arrange
        text = "This is a test\n\n"

        # Act
        result = clean_markdown(text)

        # Assert
        assert result == "This is a test", "Should remove trailing newlines"

    def test_remove_asterisk_at_start(self):
        # Arrange
        text = "**Test without space** bla"

        # Act
        result = clean_markdown(text)

        # Assert
        assert (
            result == "Test without space bla"
        ), "Should remove leading asterisks not followed by space"

    def test_keep_asterisk_with_space_at_start(self):
        # Arrange
        text = "* Test with space* bla"

        # Act
        result = clean_markdown(text)

        # Assert
        assert (
            result == "* Test with space* bla"
        ), "Should retain leading asterisks followed by space"

    def test_remove_asterisk_at_end(self):
        # Arrange
        text = "Test without space*"

        # Act
        result = clean_markdown(text)

        # Assert
        assert (
            result == "Test without space*"
        ), "Should keep trailing asterisks not preceded by space"

    def test_remove_hashes_and_whitespace_at_start(self):
        # Arrange
        text = "   ##   Heading"

        # Act
        result = clean_markdown(text)

        # Assert
        assert result == "Heading", "Should remove leading hashes and whitespace"

    def test_remove_mixed_hashes_and_spaces(self):
        # Arrange
        text = "   # # Heading"

        # Act
        result = clean_markdown(text)

        # Assert
        assert result == "Heading", "Should remove mixed hashes and whitespace at start"
