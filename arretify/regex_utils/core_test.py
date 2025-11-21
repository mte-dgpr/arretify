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

from .core import MatchProxy, PatternProxy
from .types import Settings


class TestPatternProxy(unittest.TestCase):

    def setUp(self):
        self.pattern_string = r"\d+"
        self.settings = Settings(
            ignore_case=True,
            ignore_accents=True,
            normalize_quotes=True,
        )
        self.pattern_proxy = PatternProxy(self.pattern_string, self.settings)

    def test_match_success(self):
        # Arrange
        test_string = "123abc"

        # Act
        result = self.pattern_proxy.match(test_string)

        # Assert
        assert isinstance(result, MatchProxy)
        assert result.group(0) == "123"

    def test_match_failure(self):
        # Arrange
        test_string = "abc123"

        # Act
        result = self.pattern_proxy.match(test_string)

        # Assert
        assert result is None

    def test_match_with_positive_lookbehind(self):
        # Arrange
        pattern_string = r"(?<=abc)\d+"
        pattern_proxy = PatternProxy(pattern_string)
        test_string = "abc123"
        # Assert
        with self.assertRaises(NotImplementedError):
            pattern_proxy.match(test_string)

    def test_search_success(self):
        # Arrange
        test_string = "abc123"

        # Act
        result = self.pattern_proxy.search(test_string)

        # Assert
        assert isinstance(result, MatchProxy)
        assert result.group(0) == "123"

    def test_search_failure(self):
        # Arrange
        test_string = "abcdef"

        # Act
        result = self.pattern_proxy.search(test_string)

        # Assert
        assert result is None

    def test_finditer(self):
        # Arrange
        test_string = "abc123def456"

        # Act
        result = list(self.pattern_proxy.finditer(test_string))

        # Assert
        assert len(result), 2
        assert result[0].group(0) == "123"
        assert result[1].group(0) == "456"

    def test_sub(self):
        # Arrange
        test_string = "abc123déf456"
        repl = "REPL"
        expected = "abcREPLdéfREPL"

        # Act
        result = self.pattern_proxy.sub(repl, test_string)

        # Assert
        assert result == expected

    def test_sub_no_match(self):
        # Arrange
        test_string = "abc”déf"
        repl = "REPL"
        expected = "abc”déf"

        # Act
        result = self.pattern_proxy.sub(repl, test_string)

        # Assert
        assert result == expected

    def test_sub_with_matching_repl(self):
        """
        Tests the substitution of a pattern with a replacement string
        that also matches the pattern. We shouldnt end up in an infinite loop.
        """
        # Arrange
        test_string = "abc123déf456"
        repl = "666"

        # Act
        result = self.pattern_proxy.sub(repl, test_string)

        # Assert
        assert result == "abc666déf666"

    def test_ignore_case(self):
        # Arrange
        pattern_string = r"hello"
        settings = Settings(ignore_case=True)
        pattern_proxy = PatternProxy(pattern_string, settings)
        test_string = "HELLO world"

        # Act
        result = pattern_proxy.match(test_string)

        # Assert
        assert isinstance(result, MatchProxy)
        assert result.group(0) == "HELLO"

    def test_ignore_accents(self):
        # Arrange
        pattern_string = r"cafécafé"
        settings = Settings(ignore_accents=True)
        pattern_proxy = PatternProxy(pattern_string, settings)
        test_string = "cafecafé"

        # Act
        result = pattern_proxy.match(test_string)

        # Assert
        assert isinstance(result, MatchProxy)
        assert result.group(0) == "cafecafé"

    def test_normalize_quotes(self):
        # Arrange
        pattern_string = r"“double”single’"
        settings = Settings(normalize_quotes=True)
        pattern_proxy = PatternProxy(pattern_string, settings)
        test_string = '"double"single\''

        # Act
        result = pattern_proxy.match(test_string)

        # Assert
        assert isinstance(result, MatchProxy)
        assert result.group(0) == '"double"single\''

    def test_unimplemented_method(self):
        # Arrange
        method = "findall"

        # Act
        with self.assertRaises(NotImplementedError):
            getattr(self.pattern_proxy, method)


class TestMatchProxy(unittest.TestCase):
    def setUp(self):
        self.test_string = "abc123def"
        self.match = re.search(r"\d+", self.test_string)
        self.match_proxy = MatchProxy(self.test_string, self.match)

    def test_group(self):
        # Arrange
        pattern_string = r"cafe"
        settings = Settings(ignore_accents=True)
        pattern_proxy = PatternProxy(pattern_string, settings)
        test_string = "café"
        match_proxy = pattern_proxy.match(test_string)

        # Act
        result = match_proxy.group(0)

        # Assert
        assert result == "café"

    def test_group_absent(self):
        # Arrange
        pattern_string = r"bla(?P<blo>blo)?"
        pattern_proxy = PatternProxy(pattern_string)
        test_string = "bla"
        match_proxy = pattern_proxy.match(test_string)

        # Act
        result = match_proxy.group("blo")

        # Assert
        assert result is None

    def test_getattr(self):
        # Arrange
        attr = "start"

        # Act
        result = getattr(self.match_proxy, attr)

        # Assert
        assert result == self.match.start

    def test_groupdict(self):
        # Arrange
        pattern_string = r"(?P<first>\d+)-(?P<second>cafe)"
        test_string = "123-café"
        pattern_proxy = PatternProxy(pattern_string)
        match_proxy = pattern_proxy.match(test_string)

        # Act
        result = match_proxy.groupdict()

        # Assert
        expected = {"first": "123", "second": "café"}
        assert result == expected

    def test_groupdict_no_groups(self):
        # Arrange
        pattern_string = r"\d+"
        test_string = "123"
        pattern_proxy = PatternProxy(pattern_string)
        match_proxy = pattern_proxy.match(test_string)

        # Act
        result = match_proxy.groupdict()

        # Assert
        expected = {}
        assert result == expected
