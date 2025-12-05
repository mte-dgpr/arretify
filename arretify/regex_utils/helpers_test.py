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
import re
import unittest

from .helpers import (
    join_with_or,
    lookup_normalized_version,
    normalize_string,
    quantifier_to_string,
    repeated_with_separator,
    sub_with_match,
    without_named_groups,
)
from .types import Settings


class TestSubWithMatch(unittest.TestCase):

    def test_remove_full_match(self):
        # Arrange
        string = "Hello, this is a test."
        match = re.search(r"this is", string)

        # Act
        result = sub_with_match(string, match)

        # Assert
        assert result == "Hello,  a test.", "Should remove the matched substring"

    def test_remove_group_match(self):
        # Arrange
        string = "Hello, (this is) a test."
        match = re.search(r"\((.*?)\)", string)

        # Act
        result = sub_with_match(string, match, group=1)

        # Assert
        assert result == "Hello, () a test.", "Should remove the content of the matched group"

    def test_no_match(self):
        # Arrange
        string = "Hello, this is a test."
        match = re.search(r"not in string", string)

        # Act / Assert
        assert match is None, "Match should be None if pattern is not found"


class TestWithoutNamedGroups(unittest.TestCase):

    def test_simple(self):
        assert (
            without_named_groups(
                r"(([nN]° ?(?P<code1>\S+))|(?P<code2>\S+[/\-]\S+))(?=\s|\.|$|,|\)|;)"
            )
            == r"(([nN]° ?(\S+))|(\S+[/\-]\S+))(?=\s|\.|$|,|\)|;)"
        )


class TestNormalizeString(unittest.TestCase):

    def test_normalize_all(self):
        # Arrange
        settings = Settings()

        # Act
        result = normalize_string("“Héllo", settings)

        # Assert
        assert result == '"hello'


class TestLookupNormalizedVersion(unittest.TestCase):

    def test_simple(self):
        # Arrange
        choices = ["Hello", "World", "Test"]
        text = "hello"
        settings = Settings(ignore_case=True)

        # Act
        result = lookup_normalized_version(choices, text, settings)

        # Assert
        assert result == "Hello"


class TestQuantifierMinMaxToString(unittest.TestCase):
    def test_min_max_to_string(self):
        # Arrange
        test_cases = [
            ((0, 1), "{0,1}"),
            ((0, ...), "*"),
            ((1, ...), "+"),
            ((2, 3), "{2,3}"),
            ((2, ...), "{2,}"),
            ((1, 1), "{1}"),
            ((1, 2), "{1,2}"),
        ]

        # Act & Assert
        for quantifier, expected in test_cases:
            result = quantifier_to_string(quantifier)
            assert result == expected


class TestRepeatedWithSeparator(unittest.TestCase):

    def test_repeated_with_separator(self):
        # Arrange
        pattern = r"\w+"
        separator = ","
        quantifier = (1, 3)

        # Act
        result = repeated_with_separator(pattern, separator, quantifier)

        # Assert
        assert result == r"(\w+)((,)(\w+)){0,2}"

    def test_repeated_with_separator_min_zero(self):
        # Arrange
        pattern = r"\w+"
        separator = ","
        quantifier = (0, 3)

        # Act
        result = repeated_with_separator(pattern, separator, quantifier)

        # Assert
        assert result == r"((\w+)((,)(\w+)){0,2})?"


class TestJoinWithOr(unittest.TestCase):

    def test_join_with_or_simple(self):
        # Arrange
        patterns = [r"cat", r"dog", r"mouse"]

        # Act
        result = join_with_or(patterns)

        # Assert
        assert result == r"cat|dog|mouse"

    def test_join_with_or_prefix_conflict(self):
        # Arrange
        patterns = [r"cat", r"caterpillar", r"dog"]

        # Act / Assert
        with self.assertRaises(ValueError):
            join_with_or(patterns)
