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
import unittest

from .core import PatternProxy
from .functional import (
    iter_regex_tree_match_page_elements_or_strings,
    map_matches,
    map_regex_tree_match,
)
from .regex_tree.types import RegexTreeMatch


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
        result = list(iter_regex_tree_match_page_elements_or_strings(match))

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
        result = list(iter_regex_tree_match_page_elements_or_strings(match))

        # Assert
        assert result == ["hello", "world", "!", "python"]

    def test_empty_match(self):
        # Arrange
        match = RegexTreeMatch(children=[], group_name=None, match_dict={})

        # Act
        result = list(iter_regex_tree_match_page_elements_or_strings(match))

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
        result = list(iter_regex_tree_match_page_elements_or_strings(match))

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
