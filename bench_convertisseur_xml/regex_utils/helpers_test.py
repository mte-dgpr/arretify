import unittest
import re
from typing import Iterator

from .helpers import sub_with_match, without_named_groups, normalize_string, lookup_normalized_version
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
        assert without_named_groups(r'(([nN]° ?(?P<code1>\S+))|(?P<code2>\S+[/\-]\S+))(?=\s|\.|$|,|\)|;)') == r'(([nN]° ?(\S+))|(\S+[/\-]\S+))(?=\s|\.|$|,|\)|;)'


class TestNormalizeString(unittest.TestCase):

    def test_normalize_ignore_case(self):
        # Arrange
        settings = Settings(ignore_case=True)

        # Act
        result = normalize_string("Hello", settings, ignore_case_settings=False)

        # Assert
        assert result == "hello"

    def test_normalize_ignore_case_ignore_setting(self):
        # Arrange
        settings = Settings(ignore_case=True)

        # Act
        result = normalize_string("Hello", settings, ignore_case_settings=True)

        # Assert
        assert result == "Hello"


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