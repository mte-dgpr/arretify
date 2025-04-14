import unittest

from .merge import merge_matches_with_siblings
from .split import split_string_with_regex
from .core import PatternProxy


class TestMergeMatchWithSiblingString(unittest.TestCase):

    def test_split_with_matches(self):
        # Arrange
        pattern = PatternProxy(r"\d+")
        string = "abc123def456ghi"

        # Act
        result = list(
            merge_matches_with_siblings(
                split_string_with_regex(
                    pattern,
                    string,
                ),
                "following",
            )
        )

        # Assert
        assert result == ["abc", "123def", "456ghi"]

    def test_split_with_matches_after(self):
        # Arrange
        pattern = PatternProxy(r"\d+")
        string = "abc123def456ghi"

        # Act
        result = list(
            merge_matches_with_siblings(
                split_string_with_regex(
                    pattern,
                    string,
                ),
                "previous",
            )
        )

        # Assert
        assert result == ["abc123", "def456", "ghi"]

    def test_split_with_no_matches(self):
        # Arrange
        pattern = PatternProxy(r"\d+")
        string = "abcdef"

        # Act
        result = list(
            merge_matches_with_siblings(
                split_string_with_regex(
                    pattern,
                    string,
                ),
                "following",
            )
        )

        # Assert
        assert result == ["abcdef"]

    def test_split_with_match_at_start(self):
        # Arrange
        pattern = PatternProxy(r"\d+")
        string = "123abc456"

        # Act
        result = list(
            merge_matches_with_siblings(
                split_string_with_regex(
                    pattern,
                    string,
                ),
                "following",
            )
        )

        # Assert
        assert result == ["123abc", "456"]

    def test_split_with_match_at_end(self):
        # Arrange
        pattern = PatternProxy(r"\d+")
        string = "abc123"

        # Act
        result = list(
            merge_matches_with_siblings(
                split_string_with_regex(
                    pattern,
                    string,
                ),
                "following",
            )
        )

        # Assert
        assert result == ["abc", "123"]
