import re
import unittest
from unittest.mock import patch
from .core import PatternProxy, MatchProxy
from .types import Settings


class TestPatternProxy(unittest.TestCase):
    
    def setUp(self):
        self.pattern_string = r'\d+'
        self.settings = Settings(ignore_case=True, ignore_accents=True, normalize_quotes=True)
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

    def test_ignore_case(self):
        # Arrange
        pattern_string = r'hello'
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
        pattern_string = r'cafécafé'
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
        pattern_string = r'“double”single’'
        settings = Settings(normalize_quotes=True)
        pattern_proxy = PatternProxy(pattern_string, settings)
        test_string = '"double"single\''

        # Act
        result = pattern_proxy.match(test_string)

        # Assert
        assert isinstance(result, MatchProxy)
        assert result.group(0) == '"double"single\''


class TestMatchProxy(unittest.TestCase):
    def setUp(self):
        self.test_string = "abc123def"
        self.match = re.search(r'\d+', self.test_string)
        self.match_proxy = MatchProxy(self.test_string, self.match)

    def test_group(self):
        # Arrange
        pattern_string = r'cafe'
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
        pattern_string = r'bla(?P<blo>blo)?'
        pattern_proxy = PatternProxy(pattern_string)
        test_string = "bla"
        match_proxy = pattern_proxy.match(test_string)

        # Act
        result = match_proxy.group('blo')

        # Assert
        assert result is None

    def test_getattr(self):
        # Arrange
        attr = 'start'

        # Act
        result = getattr(self.match_proxy, attr)

        # Assert
        assert result == self.match.start

    def test_groupdict(self):
        # Arrange
        pattern_string = r'(?P<first>\d+)-(?P<second>cafe)'
        test_string = "123-café"
        pattern_proxy = PatternProxy(pattern_string)
        match_proxy = pattern_proxy.match(test_string)

        # Act
        result = match_proxy.groupdict()

        # Assert
        expected = {'first': '123', 'second': 'café'}
        assert result == expected

    def test_groupdict_no_groups(self):
        # Arrange
        pattern_string = r'\d+'
        test_string = "123"
        pattern_proxy = PatternProxy(pattern_string)
        match_proxy = pattern_proxy.match(test_string)

        # Act
        result = match_proxy.groupdict()

        # Assert
        expected = {}
        assert result == expected
