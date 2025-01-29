import unittest
import re
from typing import Iterator

from .regex import sub_with_match, without_named_groups, named_groups_index


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


class TestIncrementNamedGroups(unittest.TestCase):

    def test_increment_named_groups_with_suffix(self):
        # Arrange
        pattern = r"(?P<group1>.*)(?P<another666>\d+)"

        # Act
        result = named_groups_index(pattern, 11)

        # Assert
        assert result == r"(?P<group11>.*)(?P<another11>\d+)"

    def test_increment_named_groups_without_suffix(self):
        # Arrange
        pattern = r"(?P<group>.*)(?P<another>\w+)"

        # Act
        result = named_groups_index(pattern, 777)

        # Assert
        assert result == r"(?P<group>.*)(?P<another>\w+)"