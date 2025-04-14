import unittest
import re

from .merge import merge_strings


class TestMergeStrings(unittest.TestCase):

    def test_simple(self):
        # Arrange
        match_mock1 = re.match(r"dummy1", "dummy1")
        match_mock2 = re.match(r"dummy2", "dummy2")
        input_gen = iter(
            [
                "abc",
                match_mock1,
                "def",
                "ghi",
                match_mock2,
                "jkl",
                "mno",
            ]
        )

        # Act
        result = list(merge_strings(input_gen))

        # Assert
        assert result[0] == "abc"
        assert result[1] == match_mock1
        assert result[2] == "defghi"
        assert result[3] == match_mock2
        assert result[4] == "jklmno"

    def test_merge_strings_with_matches(self):
        # Arrange
        match_mock = re.match(r"dummy", "dummy")
        input_gen = iter(["abc", match_mock, "def"])

        # Act
        result = list(merge_strings(input_gen))

        # Assert
        assert result[0] == "abc"
        assert result[1] == match_mock
        assert result[2] == "def"

    def test_with_empty_before_and_after(self):
        # Arrange
        match_mock = re.match(r"dummy", "dummy")
        input_gen = iter(["", match_mock, ""])

        # Act
        result = list(merge_strings(input_gen))

        # Assert
        assert result[0] == ""
        assert result[1] == match_mock
        assert result[2] == ""

    def test_merge_strings_with_only_matches(self):
        # Arrange
        match_mock1 = re.match(r"dummy1", "dummy1")
        match_mock2 = re.match(r"dummy2", "dummy2")
        input_gen = iter([match_mock1, match_mock2])

        # Act
        result = list(merge_strings(input_gen))

        # Assert
        assert result == [match_mock1, match_mock2]
