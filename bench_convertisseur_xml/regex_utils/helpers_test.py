import unittest
import re
from typing import Iterator

from .helpers import sub_with_match, without_named_groups


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
