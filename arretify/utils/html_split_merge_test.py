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

import pytest
from bs4 import BeautifulSoup

from arretify.regex_utils import PatternProxy, Settings, regex_tree
from arretify.utils.split_merge import SplitMatch, SplitNotAMatch

from .html_split_merge import (
    _NamedGroupSplitterMatch,
    _slice_elements_with_string_index,
    _split_before_string_index,
    _split_match_by_named_groups,
    _trim_strings_before_merging,
    make_pattern_splitter_ignoring_inline_tags,
    make_regex_tree_splitter,
    pick_string,
    recombine_strings,
    regex_tree_match,
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
        probe = pick_string(probe)

        # Assert
        assert probe(elements, 0) is True
        # If pick_str not used, this should raise an error
        assert probe(elements, 1) is False
        assert probe(elements, 2) is True
        assert probe(elements, 3) is True


class TestMakePatternSplitterIgnoringInlineTags(unittest.TestCase):

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
        splitter = make_pattern_splitter_ignoring_inline_tags(pattern_proxy)
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
        splitter = make_pattern_splitter_ignoring_inline_tags(pattern_proxy)
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
        splitter = make_pattern_splitter_ignoring_inline_tags(pattern_proxy)
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
        elements = [
            "text1",
            "hel",
            self.soup.new_tag("br"),
            "lo text2",
        ]

        # Act
        splitter = make_pattern_splitter_ignoring_inline_tags(pattern_proxy)
        before, match, after = splitter(elements)

        # Assert
        assert before == ["text1"]
        assert after == [" text2"]
        assert match.match_proxy.group(0) == "hello"
        assert match.elements == ["hel", self.soup.new_tag("br"), "lo"]

    def test_split_just_before_inline_tag(self):
        # Arrange
        pattern_proxy = PatternProxy(
            r"bla",
        )
        elements = ["blo bla", self.soup.new_tag("br"), "bli blu"]
        splitter = make_pattern_splitter_ignoring_inline_tags(pattern_proxy)

        # Act
        before, match, after = splitter(elements)

        # Assert
        assert before == ["blo "]
        assert match.elements == ["bla"]
        assert after == [self.soup.new_tag("br"), "bli blu"]


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

    @pytest.mark.skip("Known issue: alternation order not yet handled properly")
    def test_match_with_longest_alternation(self):
        """
        Test for a specific case where alternation order matters.
        What happens here is that the pattern compiled for the Sequence node will match the whole
        string, but when descending into the Literal node with the substring "123", the node
        will match only "12", and therefore fail to decompose the entirety of the substring.
        We need to make sure this does not happen and always match the longest alternation.

        For now, we just ensure that the join_with_or helper raises an error when such a situation
        is detected.
        """
        # Arrange
        group_node = regex_tree.Group(
            regex_tree.Sequence(
                [
                    "bla",
                    regex_tree.Literal(
                        r"12|123",
                    ),
                    "blo",
                ],
            ),
            group_name="root",
        )

        # Act
        elements = ["bla123blo"]
        result = regex_tree_match(elements, group_node)

        # Assert
        assert result == regex_tree.Match(
            group_name="root",
            match_dict=dict(),
            children=["bla", "123", "blo"],
        )

    @pytest.mark.skip("Known issue: alternation order not yet handled properly")
    def test_match_longest_alternation_with_repeat(self):
        # Arrange
        group_node = regex_tree.Group(
            regex_tree.Repeat(
                regex_tree.Literal(
                    r"12|123",
                ),
                quantifier=(1, ...),
            ),
            group_name="root",
        )

        # Act
        elements = ["12312312"]
        result = regex_tree_match(elements, group_node)

        # Assert
        assert result == regex_tree.Match(
            group_name="root",
            match_dict=dict(),
            children=[
                "123",
                "123",
                "12",
            ],
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


class TestMakeRegexTreeSplitter(unittest.TestCase):

    def setUp(self):
        self.soup = BeautifulSoup("", features="html.parser")

    def test_split_simple(self):
        # Arrange
        bla_node = regex_tree.Group(
            regex_tree.Literal(
                r"bla",
            ),
            group_name="root",
        )
        elements = ["blo bla bli", self.soup.new_tag("br"), "blu"]
        splitter = make_regex_tree_splitter(bla_node)

        # Act
        before, match, after = splitter(elements)

        # Assert
        assert before == ["blo "]
        assert match.children == ["bla"]
        assert after == [" bli", self.soup.new_tag("br"), "blu"]

    def test_split_around_tag(self):
        # Arrange
        hello_node = regex_tree.Group(
            regex_tree.Literal(
                r"hello",
            ),
            group_name="root",
        )
        elements = [
            "text1 ",
            "hel",
            self.soup.new_tag("br"),
            "lo text2",
        ]
        splitter = make_regex_tree_splitter(hello_node)

        # Act
        before, match, after = splitter(elements)

        # Assert
        assert before == ["text1 "]
        assert match.children == ["hel", self.soup.new_tag("br"), "lo"]
        assert after == [" text2"]


class TestSliceElementsWithStringIndex(unittest.TestCase):
    def setUp(self):
        self.soup = BeautifulSoup("", features="html.parser")

    def test_slice_elements(self):
        # Arrange
        elements = [
            "Hello",
            self.soup.new_tag("br"),
            "World",
        ]
        start_index = 2
        end_index = 7

        # Act
        before, match, after = _slice_elements_with_string_index(
            elements,
            start_index,
            end_index,
        )

        # Assert
        assert before == ["He"]
        assert match == [
            "llo",
            self.soup.new_tag("br"),
            "Wo",
        ]
        assert after == ["rld"]

    def test_slice_just_before_tag(self):
        # Arrange
        elements = [
            "Hello",
            self.soup.new_tag("br"),
            "World",
        ]
        start_index = 0
        end_index = 5

        # Act
        before, match, after = _slice_elements_with_string_index(
            elements,
            start_index,
            end_index,
        )

        # Assert
        assert before == []
        assert match == [
            "Hello",
        ]
        assert after == [
            self.soup.new_tag("br"),
            "World",
        ]

    def test_slice_just_after_tag(self):
        # Arrange
        elements = [
            "Hello",
            self.soup.new_tag("br"),
            "World",
        ]
        start_index = 5
        end_index = 10

        # Act
        before, match, after = _slice_elements_with_string_index(
            elements,
            start_index,
            end_index,
        )

        # Assert
        assert before == [
            "Hello",
            self.soup.new_tag("br"),
        ]
        assert match == [
            "World",
        ]
        assert after == []


class TestRecombineStrings(unittest.TestCase):

    def setUp(self):
        self.soup = BeautifulSoup("", features="html.parser")

    def test_recombine_strings(self):
        # Arrange
        elements = [
            "text1 ",
            "text2",
            self.soup.new_tag("br"),
            " text3 ",
            " text4",
        ]

        # Act
        recombined = recombine_strings(elements)

        # Assert
        assert recombined == [
            "text1 text2",
            self.soup.new_tag("br"),
            " text3  text4",
        ]
