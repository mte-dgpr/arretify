import unittest
from typing import List, Union

from .functional import iter_regex_tree_match_strings
from .regex_tree.types import RegexTreeMatch


class TestIterRegexTreeMatchStrings(unittest.TestCase):
    def test_single_level(self):
        # Arrange
        match = RegexTreeMatch(
            children=["hello", "world"],
            group_name=None,
            match_dict={}
        )

        # Act
        result = list(iter_regex_tree_match_strings(match))

        # Assert
        assert result == ["hello", "world"]

    def test_nested_levels(self):
        # Arrange
        match = RegexTreeMatch(
            children=[
                "hello",
                RegexTreeMatch(
                    children=["world", "!"],
                    group_name=None,
                    match_dict={}
                ),
                "python"
            ],
            group_name=None,
            match_dict={}
        )

        # Act
        result = list(iter_regex_tree_match_strings(match))

        # Assert
        assert result == ["hello", "world", "!", "python"]

    def test_empty_match(self):
        # Arrange
        match = RegexTreeMatch(
            children=[],
            group_name=None,
            match_dict={}
        )

        # Act
        result = list(iter_regex_tree_match_strings(match))

        # Assert
        assert result == []

    def test_deeply_nested(self):
        # Arrange
        match = RegexTreeMatch(
            children=[
                "level1",
                RegexTreeMatch(
                    children=[
                        "level2",
                        RegexTreeMatch(
                            children=["level3", "deep"],
                            group_name=None,
                            match_dict={}
                        )
                    ],
                    group_name=None,
                    match_dict={}
                )
            ],
            group_name=None,
            match_dict={}
        )

        # Act
        result = list(iter_regex_tree_match_strings(match))

        # Assert
        assert result == ["level1", "level2", "level3", "deep"]
