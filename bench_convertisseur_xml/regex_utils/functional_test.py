import unittest

from .functional import (
    iter_regex_tree_match_strings,
    map_matches,
    map_regex_tree_match,
)
from .regex_tree.types import RegexTreeMatch
from .core import PatternProxy


class TestFlatMapNonString(unittest.TestCase):

    def setUp(self):
        self.pattern_proxy = PatternProxy("bla|blo")

    def test_map_matches(self):
        # Arrange
        elements = [
            "hello",
            self.pattern_proxy.match("bla"),
            "world",
            self.pattern_proxy.match("blo"),
        ]

        def map_func(m):
            return "MATCHED:" + m.group(0)

        # Act
        result = list(map_matches(elements, map_func))

        # Assert
        assert result == [
            "hello",
            "MATCHED:bla",
            "world",
            "MATCHED:blo",
        ]


class TestIterRegexTreeMatchStrings(unittest.TestCase):
    def test_single_level(self):
        # Arrange
        match = RegexTreeMatch(
            children=["hello", "world"],
            group_name=None,
            match_dict={},
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
                    match_dict={},
                ),
                "python",
            ],
            group_name=None,
            match_dict={},
        )

        # Act
        result = list(iter_regex_tree_match_strings(match))

        # Assert
        assert result == ["hello", "world", "!", "python"]

    def test_empty_match(self):
        # Arrange
        match = RegexTreeMatch(children=[], group_name=None, match_dict={})

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
                            match_dict={},
                        ),
                    ],
                    group_name=None,
                    match_dict={},
                ),
            ],
            group_name=None,
            match_dict={},
        )

        # Act
        result = list(iter_regex_tree_match_strings(match))

        # Assert
        assert result == ["level1", "level2", "level3", "deep"]


class TestMapRegexTreeMatch(unittest.TestCase):

    def test_single_level(self):
        # Arrange
        match = [
            "bla",
            RegexTreeMatch(
                children=["hello", "world"],
                group_name=None,
                match_dict={},
            ),
            "blo",
        ]

        def map_func(m):
            return "MATCHED:" + ",".join([m.children[0], m.children[1]])

        # Act
        result = list(map_regex_tree_match(match, map_func))

        # Assert
        assert result == ["bla", "MATCHED:hello,world", "blo"]
