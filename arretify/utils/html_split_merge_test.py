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

from bs4 import BeautifulSoup

from arretify.utils.split_merge import SplitMatch, SplitNotAMatch
from arretify.regex_utils import PatternProxy, regex_tree, Settings
from .html_split_merge import (
    pick_string,
    make_pattern_splitter,
    _split_before_string_index,
    _trim_strings_before_merging,
    _split_match_by_named_groups,
    regex_tree_match,
    _NamedGroupSplitterMatch,
)


class TestPickStrings(unittest.TestCase):

    def setUp(self):
        self.soup = BeautifulSoup("", features="html.parser")

    def test_simple(self):
        # Arrange
        elements = [
            "text1",
            self.soup.new_tag("div"),
            "text2",
            "text3",
        ]

        def probe(elements, index):
            return elements[index].startswith("text")

        # Act
        text_segments_probe = pick_string(probe)

        # Assert
        assert text_segments_probe(elements, 0) is True
        # If pick_text_segment not used, this should raise an error
        assert text_segments_probe(elements, 1) is False
        assert text_segments_probe(elements, 2) is True
        assert text_segments_probe(elements, 3) is True


class TestMakePatternSplitter(unittest.TestCase):

    def setUp(self):
        self.soup = BeautifulSoup("", features="html.parser")

    def test_splitter(self):
        # Arrange
        pattern_proxy = PatternProxy(r"bla\d")
        tag = self.soup.new_tag("br")
        elements = [
            "text1",
            tag,
            "text2",
            "text3 bla1 text4bla2text5",
        ]

        # Act
        splitter = make_pattern_splitter(pattern_proxy)
        before1, match1, after1 = splitter(elements)
        before2, match2, after2 = splitter(after1)

        # Assert
        assert before1 == ["text1", tag, "text2", "text3 "]
        assert after1 == [" text4bla2text5"]
        assert match1.match_proxy.group(0) == "bla1"
        assert match1.elements == ["bla1"]

        assert before2 == [" text4"]
        assert after2 == ["text5"]
        assert match2.match_proxy.group(0) == "bla2"
        assert match2.elements == ["bla2"]

    def test_split_beginning_of_string(self):
        # Arrange
        pattern_proxy = PatternProxy(
            r"bla",
        )
        elements = [
            "bla text",
        ]

        # Act
        splitter = make_pattern_splitter(pattern_proxy)
        before, match, after = splitter(elements)

        # Assert
        assert before == []
        assert after == [" text"]
        assert match.match_proxy.group(0) == "bla"
        assert match.elements == ["bla"]

    def test_split_end_of_string(self):
        # Arrange
        pattern_proxy = PatternProxy(
            r"bla",
        )
        elements = [
            "text bla",
        ]

        # Act
        splitter = make_pattern_splitter(pattern_proxy)
        before, match, after = splitter(elements)

        # Assert
        assert before == ["text "]
        assert after == []
        assert match.match_proxy.group(0) == "bla"
        assert match.elements == ["bla"]

    def test_split_around_inline_tag(self):
        # Arrange
        pattern_proxy = PatternProxy(
            r"hello",
        )
        tag = self.soup.new_tag("br")
        elements = [
            "text1",
            "hel",
            tag,
            "lo text2",
        ]

        # Act
        splitter = make_pattern_splitter(pattern_proxy)
        before, match, after = splitter(elements)

        # Assert
        assert before == ["text1"]
        assert after == [" text2"]
        assert match.match_proxy.group(0) == "hello"
        assert match.elements == ["hel", tag, "lo"]


class TestSplitBeforeStringIndex(unittest.TestCase):

    def setUp(self):
        self.soup = BeautifulSoup("", features="html.parser")

    def test_split_beginning(self):
        # Arrange
        elements = [
            "text1",
            "text2",
            "text3",
        ]
        split_index = 0

        # Act
        before, after = _split_before_string_index(elements, split_index)

        # Assert
        assert before == []
        assert after == elements

    def test_split_middle(self):
        # Arrange
        elements = [
            "text1",
            "text2",
            "text3",
        ]
        split_index = 6

        # Act
        before, after = _split_before_string_index(elements, split_index)

        # Assert
        assert before == ["text1", "t"]
        assert after == ["ext2", "text3"]

    def test_split_end(self):
        # Arrange
        elements = [
            "text1",
            "text2",
            "text3",
        ]
        split_index = 15

        # Act
        before, after = _split_before_string_index(elements, split_index)

        # Assert
        assert before == ["text1", "text2", "text3"]
        assert after == []

    def test_split_after_tag(self):
        # Arrange
        tag = self.soup.new_tag("div")
        elements = [
            "text1",
            "text2",
            tag,
            "text3",
        ]
        split_index = 12

        # Act
        before, after = _split_before_string_index(elements, split_index)

        # Assert
        assert before == ["text1", "text2", tag, "te"]
        assert after == ["xt3"]

    def test_split_before_tag(self):
        # Arrange
        tag = self.soup.new_tag("div")
        elements = [
            "text1",
            tag,
            "text2",
            "text3",
        ]
        split_index = 3

        # Act
        before, after = _split_before_string_index(elements, split_index)

        # Assert
        assert before == ["tex"]
        assert after == ["t1", tag, "text2", "text3"]


class TestRegexTreeMatch(unittest.TestCase):

    def test_complex_match(self):
        # Arrange
        group_node = regex_tree.Group(
            regex_tree.Sequence(
                [
                    r"(?P<greetings>Hello|Hi) ",
                    regex_tree.Repeat(
                        regex_tree.Sequence(
                            [
                                regex_tree.Group(
                                    regex_tree.Branching(
                                        [
                                            r"hello_(?P<nickname>\w+)",
                                            r"123",
                                        ]
                                    ),
                                    "nickname",
                                ),
                                ",?",
                            ]
                        ),
                        quantifier=(1, ...),
                    ),
                ]
            ),
            group_name="root",
        )
        elements = ["Hi hello_seb,123,hello_john"]

        # Act
        result = regex_tree_match(elements, group_node)

        # Assert
        assert result == regex_tree.Match(
            group_name="root",
            match_dict=dict(greetings="Hi"),
            children=[
                "Hi ",
                regex_tree.Match(
                    group_name="nickname",
                    match_dict=dict(nickname="seb"),
                    children=["hello_seb"],
                ),
                ",",
                regex_tree.Match(
                    group_name="nickname",
                    match_dict=dict(),
                    children=["123"],
                ),
                ",",
                regex_tree.Match(
                    group_name="nickname",
                    match_dict=dict(nickname="john"),
                    children=["hello_john"],
                ),
            ],
        )

    def test_no_match_simple(self):
        # Arrange
        group_node = regex_tree.Group(
            regex_tree.Sequence(
                [
                    r"bla",
                    r"blo",
                ]
            ),
            group_name="root",
        )

        # Act
        elements = ["hello"]

        # Assert
        with self.assertRaises(ValueError):
            regex_tree_match(elements, group_node)

    def test_match_second_branch_when_first_nested_fails(self):
        # When a first branch succeeds, but then a nested node fails
        # because it has different settings than the Branch node,
        # then the second branch should be tried.

        # Arrange
        group_node = regex_tree.Group(
            regex_tree.Branching(
                [
                    regex_tree.Literal(
                        r"(?P<branch1>héllo)",
                        settings=Settings(ignore_accents=False),
                    ),
                    r"(?P<branch2>hello)",
                ],
                settings=Settings(ignore_accents=True),
            ),
            group_name="root",
        )

        # Act
        elements = ["hello"]
        result = regex_tree_match(elements, group_node)

        # Assert
        assert result == regex_tree.Match(
            group_name="root",
            match_dict=dict(branch2="hello"),
            children=["hello"],
        )


class TestTrimStringsBeforeMerging(unittest.TestCase):
    def setUp(self):
        self.soup = BeautifulSoup("", features="html.parser")

    def test_trim_if_double_space(self):
        # Arrange
        elements = [
            "text1",
            "text2 ",
            self.soup.new_tag("br"),
            " text3",
        ]

        # Act
        trimmed_elements = _trim_strings_before_merging(elements)

        # Assert
        assert trimmed_elements == ["text1", "text2", self.soup.new_tag("br"), " text3"]

    def test_no_trim_if_single_space(self):
        # Arrange
        elements = [
            "text1",
            "text2 ",
            self.soup.new_tag("br"),
            "text3",
        ]

        # Act
        trimmed_elements = _trim_strings_before_merging(elements)

        # Assert
        assert trimmed_elements == ["text1", "text2 ", self.soup.new_tag("br"), "text3"]

    def test_no_trim_if_no_tag(self):
        # Arrange
        elements = [
            "text1",
            "text2 ",
            " text3",
        ]

        # Act
        trimmed_elements = _trim_strings_before_merging(elements)

        # Assert
        assert trimmed_elements == ["text1", "text2 ", " text3"]


class TestSplitMatchByNamedGroups(unittest.TestCase):

    def test_simple_split(self):
        # Arrange
        pattern = PatternProxy(r"(?P<part1>hello) bla (?P<part2>world)")
        elements = ["hello bla world"]
        match_proxy = pattern.match(elements[0])

        # Act
        splitted_elements = _split_match_by_named_groups(match_proxy, elements)

        # Assert
        assert splitted_elements == [
            SplitMatch(
                _NamedGroupSplitterMatch(
                    group_name="part1",
                    elements=["hello"],
                )
            ),
            SplitNotAMatch([" bla "]),
            SplitMatch(
                _NamedGroupSplitterMatch(
                    group_name="part2",
                    elements=["world"],
                )
            ),
        ]
