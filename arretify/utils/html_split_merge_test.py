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
from arretify.regex_utils.regex_tree.types import RegexTreeMatch
from arretify.utils.split_merge import SplitMatch, SplitNotAMatch
from arretify.utils.testing import BaseTestCaseHtml

from .html_split_merge import (
    RegexTreeSplitterContext,
    _NamedGroupSplitterMatch,
    _regex_tree_splitter,
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


class TestRegexTreeSplitterLiteral(unittest.TestCase):

    def test_split_literal_match_dict(self):
        # Arrange
        node = regex_tree.Literal(
            r"(?P<greeting>hello)",
        )
        elements = ["well hello world!"]
        context = RegexTreeSplitterContext()

        # Act
        before, match, after = _regex_tree_splitter(context, elements, node)

        # Assert
        assert before == ["well "]
        assert match == ["hello"]
        assert after == [" world!"]
        assert context.match_dict == {"greeting": "hello"}


class TestRegexTreeSplitterBranching(unittest.TestCase):

    def test_split_with_alternation(self):
        # Arrange
        node = regex_tree.Branching(
            [
                "def",
                "abc",
            ]
        )
        elements = ["xyz abc 123"]
        context = RegexTreeSplitterContext()

        # Act
        before, match, after = _regex_tree_splitter(context, elements, node)

        # Assert
        assert before == ["xyz "]
        assert match == ["abc"]
        assert after == [" 123"]

    def test_branching_no_match(self):
        # Arrange
        node = regex_tree.Branching(
            [
                "def",
                "ghi",
            ]
        )
        elements = ["xyz abc 123"]
        context = RegexTreeSplitterContext()

        # Act
        split = _regex_tree_splitter(context, elements, node)

        # Assert
        assert split is None

    def test_priorize_contiguous_match(self):
        # Arrange
        node = regex_tree.Branching(
            [
                "abc",
                "def",
            ]
        )
        elements = ["def abc 123"]
        context = RegexTreeSplitterContext()

        # Act
        before, match, after = _regex_tree_splitter(context, elements, node)

        # Assert
        assert before == []
        assert match == ["def"]
        assert after == [" abc 123"]

    def test_captures_match_dict(self):
        # Arrange
        node = regex_tree.Branching(
            [
                r"(?P<first>abc)",
                r"(?P<second>def)",
            ]
        )
        elements = ["xyz abc def 123"]
        context = RegexTreeSplitterContext()

        # Act
        before, match, after = _regex_tree_splitter(context, elements, node)

        # Assert
        assert before == ["xyz "]
        assert match == ["abc"]
        assert after == [" def 123"]
        assert context.match_dict == {"first": "abc"}


class TestRegexTreeSplitterRepeat(unittest.TestCase):

    def test_split_repeat_any_number(self):
        # Arrange
        node = regex_tree.Repeat("bla", quantifier=(1, ...))
        elements = ["bli blablablable blo"]
        context = RegexTreeSplitterContext()

        # Act
        split = _regex_tree_splitter(context, elements, node)

        # Assert
        assert split is not None
        before, match, after = split
        assert before == ["bli "]
        assert match == ["blablabla"]
        assert after == ["ble blo"]

    def test_split_repeat_min(self):
        # Arrange
        node = regex_tree.Repeat("bla", quantifier=(3, ...))
        elements = ["bli blabla blo"]
        context = RegexTreeSplitterContext()

        # Act
        split = _regex_tree_splitter(context, elements, node)

        # Assert
        assert split is None

    def test_split_repeat_max(self):
        # Arrange
        node = regex_tree.Repeat("bla", quantifier=(1, 2))
        elements = ["bli blablablable blo"]
        context = RegexTreeSplitterContext()

        # Act
        split = _regex_tree_splitter(context, elements, node)

        # Assert
        assert split is not None
        before, match, after = split
        assert before == ["bli "]
        assert match == ["blabla"]
        assert after == ["blable blo"]

    def test_split_repeat_with_separator(self):

        # Arrange
        node = regex_tree.Repeat(
            "bla",
            quantifier=(1, ...),
            separator=",",
        )
        elements = ["bli bla,bla,bla blo"]
        context = RegexTreeSplitterContext()

        # Act
        split = _regex_tree_splitter(context, elements, node)

        # Assert
        assert split is not None
        before, match, after = split
        assert before == ["bli "]
        assert match == ["bla,bla,bla"]
        assert after == [" blo"]

    def test_split_repeat_with_trailing_separator(self):
        # Arrange
        node = regex_tree.Repeat(
            "bla",
            quantifier=(1, ...),
            separator=",",
        )
        elements = ["bli bla,bla,bla, blo"]
        context = RegexTreeSplitterContext()

        # Act
        split = _regex_tree_splitter(context, elements, node)

        # Assert
        assert split is not None
        before, match, after = split
        assert before == ["bli "]
        assert match == ["bla,bla,bla"]
        assert after == [", blo"]

    def test_split_missing_separator(self):
        # Arrange
        node = regex_tree.Repeat(
            "bla",
            quantifier=(1, ...),
            separator=",",
        )
        elements = ["bli bla,blabla blo"]
        context = RegexTreeSplitterContext()

        # Act
        split = _regex_tree_splitter(context, elements, node)

        # Assert
        assert split is not None
        before, match, after = split
        assert before == ["bli "]
        assert match == ["bla,bla"]
        assert after == ["bla blo"]


class TestRegexTreeSplitterSequence(unittest.TestCase):

    def test_split_sequence(self):
        # Arrange
        node = regex_tree.Sequence(["hello", " ", "world"])
        elements = ["well hello world!"]
        context = RegexTreeSplitterContext()

        # Act
        split = _regex_tree_splitter(context, elements, node)

        # Assert
        assert split is not None
        before, match, after = split
        assert before == ["well "]
        assert match == ["hello world"]
        assert after == ["!"]

    def test_simple_backtracking(self):
        # Arrange
        node = regex_tree.Sequence(
            [
                r"\s",
                "world",
            ]
        )

        elements = ["well hello world!"]
        context = RegexTreeSplitterContext()

        # Act
        split = _regex_tree_splitter(context, elements, node)

        # Assert
        assert split is not None
        before, match, after = split
        # Even if " hello" matches partially, the splitter should backtrack
        # and start the sequence match at the next index, which allows " world" to match fully.
        assert before == ["well hello"]
        assert match == [" world"]
        assert after == ["!"]

    def test_backtracking_just_after_first_matched_element(self):
        # Arrange
        node = regex_tree.Sequence(
            [
                r"[0-9]{3}\s",
                r"[a-z0-9]{3}\s",
                r"bla",
            ]
        )

        elements = ["123 456 abc bla"]
        context = RegexTreeSplitterContext()

        # Act
        split = _regex_tree_splitter(context, elements, node)

        # Assert
        assert split is not None
        before, match, after = split
        assert before == ["123 "]
        assert match == ["456 abc bla"]
        assert after == []

    def test_restore_match_dict_backtracking(self):
        # Arrange
        node = regex_tree.Sequence(
            [
                r"((?P<french>salut)|hello)",
                r" world",
            ]
        )
        elements = ["salut ! hello world !"]
        context = RegexTreeSplitterContext()

        # Act
        split = _regex_tree_splitter(context, elements, node, expects_before=True)

        # Assert
        assert split is not None
        assert context.match_dict == {}

    def test_partial_match(self):
        # Arrange
        node = regex_tree.Sequence(["hello", " ", "world"])
        elements = ["well hello cruel world!"]
        context = RegexTreeSplitterContext()

        # Act
        split = _regex_tree_splitter(context, elements, node)

        # Assert
        assert split is None

    def test_no_head_match(self):
        # Arrange
        node = regex_tree.Sequence(["hello", " ", "world"])
        elements = ["well hi world!"]
        context = RegexTreeSplitterContext()

        # Act
        split = _regex_tree_splitter(context, elements, node)

        # Assert
        assert split is None

    def test_split_sequence_end_of_string(self):
        # Arrange
        node = regex_tree.Sequence(["world", "$"])
        elements = ["world"]
        context = RegexTreeSplitterContext()

        # Act
        split = _regex_tree_splitter(context, elements, node)

        # Assert
        assert split is not None
        before, match, after = split
        assert before == []
        assert match == ["world"]
        assert after == []

    def test_split_sequence_catch_all(self):
        # Arrange
        node = regex_tree.Sequence([".*", " hello"])
        elements = ["well hello"]
        context = RegexTreeSplitterContext()

        # Act
        split = _regex_tree_splitter(context, elements, node)

        # Assert
        assert split is None

    def test_restore_match_dict_if_match_failed(self):
        # Arrange
        node = regex_tree.Sequence(
            [
                r"(?P<first>hello)",
                r"(?P<second>world)",
            ]
        )
        elements = ["well hello cruel world!"]
        context = RegexTreeSplitterContext()

        # Act
        split = _regex_tree_splitter(context, elements, node, expects_before=True)

        # Assert
        assert split is None
        assert context.match_dict == {}

    def test_optional_node_mid_sequence(self):
        """
        Test that the splitter properly matches if an optional node mid-sequence doesn't match.
        """
        # Arrange
        node = regex_tree.Sequence(
            [
                "well ",
                regex_tree.Optional("you "),
                "hello",
            ]
        )

        elements = ["hum, well hello you !"]
        context = RegexTreeSplitterContext()

        # Act
        split = _regex_tree_splitter(context, elements, node)

        # Assert
        assert split is not None
        before, match, after = split
        # Even if "you " matches, the splitter should backtrack and try to match "hello" directly
        # after "well ", which allows the whole sequence to match.
        assert before == ["hum, "]
        assert match == ["well hello"]
        assert after == [" you !"]

    def test_optional_node_head_sequence(self):
        """
        Test that the splitter matches the closest match when an optional node at the head
        of a sequence can match multiple times.
        """
        # Arrange
        node = regex_tree.Sequence(
            [
                regex_tree.Optional("you "),
                "hello",
            ]
        )

        elements = ["hum, well hello you !"]
        context = RegexTreeSplitterContext()

        # Act
        split = _regex_tree_splitter(context, elements, node)

        # Assert
        assert split is not None
        before, match, after = split
        # Even if "you " matches first, the splitter should backtrack and match "hello" which is
        # closer.
        assert before == ["hum, well "]
        assert match == ["hello"]
        assert after == [" you !"]

    def test_non_capturing_head(self):
        r"""
        This case is useful when we want to match a sequence that starts with a string
        that can be repeated multiple times, for example :
        "(?=article )((article )?\d(,\s)?)+"
        to match "article 1, 2, 3" but not "1, 2, 3".
        """
        # Arrange
        node = regex_tree.Sequence(
            [
                regex_tree.NonCapturing("well "),
                "well ",
                "hello",
            ]
        )

        elements = ["hum, well hello you !"]
        context = RegexTreeSplitterContext()

        # Act
        split = _regex_tree_splitter(context, elements, node)

        # Assert
        assert split is not None
        before, match, after = split
        assert before == ["hum, "]
        assert match == ["well hello"]
        assert after == [" you !"]

    def test_non_capturing_head_backtracking(self):
        # Arrange
        node = regex_tree.Sequence(
            [
                regex_tree.NonCapturing("well "),
                "well ",
                "hello",
            ]
        )

        elements = ["hum, well hi well hello you !"]
        context = RegexTreeSplitterContext()

        # Act
        split = _regex_tree_splitter(context, elements, node)

        # Assert
        assert split is not None
        before, match, after = split
        # Even if the first "well " matches first, the splitter should backtrack
        # and match "hello" which is closer.
        assert before == ["hum, well hi "]
        assert match == ["well hello"]
        assert after == [" you !"]

    def test_non_capturing_end_matching(self):
        # Arrange
        node = regex_tree.Sequence(
            [
                "well ",
                "hello",
                regex_tree.NonCapturing(" you"),
            ]
        )

        elements = ["hum, well hello you !"]
        context = RegexTreeSplitterContext()

        # Act
        split = _regex_tree_splitter(context, elements, node)

        # Assert
        assert split is not None
        before, match, after = split
        # Even if " you" matches first, the splitter should backtrack and match "hello" which is
        # closer.
        assert before == ["hum, "]
        assert match == ["well hello"]
        assert after == [" you !"]

    def test_non_capturing_end_no_match(self):
        # Arrange
        node = regex_tree.Sequence(
            [
                "well ",
                "hello",
                regex_tree.NonCapturing(" you"),
            ]
        )

        elements = ["hum, well hello !"]
        context = RegexTreeSplitterContext()

        # Act
        split = _regex_tree_splitter(context, elements, node)

        # Assert
        assert split is None


class TestRegexTreeSplitterIntegration(unittest.TestCase):
    """
    This test covers the integration of multiple nodes in the same tree,
    and ensures that the match_dict is properly propagated.
    """

    def test_split_group(self):
        # Arrange
        node = regex_tree.Group(
            regex_tree.Sequence(["hello", " ", "world"]),
            group_name="greeting",
        )
        elements = ["well hello world!"]
        context = RegexTreeSplitterContext()

        # Act
        split = _regex_tree_splitter(context, elements, node)

        # Assert
        assert split is not None
        before, match, after = split
        assert before == ["well "]
        assert len(match) == 1
        assert isinstance(match[0], RegexTreeMatch)
        assert match[0].group_name == "greeting"
        assert match[0].children == ["hello world"]
        assert after == ["!"]

    def test_no_match_dict_capture_in_branch_partial_match(self):
        # Arrange
        node = regex_tree.Branching(
            [
                regex_tree.Sequence(
                    [
                        r"(?P<greeting>hello)",
                        " ",
                        r"(?P<target>world)",
                    ]
                ),
                "goodbye",
            ]
        )

        elements = ["well hello goodbye!"]
        context = RegexTreeSplitterContext()

        # Act
        split = _regex_tree_splitter(context, elements, node)

        # Assert
        assert split is not None
        before, match, after = split
        assert before == ["well hello "]
        assert match == ["goodbye"]
        assert after == ["!"]
        # Even if the first branch matches partially, the match_dict shouldnot be updated
        # with the partial match.
        assert context.match_dict == {}

    def test_no_match_dict_capture_in_repeat_partial_match(self):
        # Arrange
        node = regex_tree.Repeat(
            regex_tree.Sequence(
                [
                    r"(?P<greeting>hello|salut)",
                    " world",
                ]
            ),
            quantifier=(1, ...),
        )

        elements = ["well hello world salut!"]
        context = RegexTreeSplitterContext()

        # Act
        split = _regex_tree_splitter(context, elements, node)

        # Assert
        assert split is not None
        before, match, after = split
        assert before == ["well "]
        assert match == ["hello world"]
        assert after == [" salut!"]
        # Even if "salut world" matches partially, the match_dict shouldnot be updated
        assert context.match_dict == {"greeting": "hello"}

    def test_nested_branching_backtracking(self):
        # Arrange
        node = regex_tree.Sequence(
            [
                "well ",
                regex_tree.Branching(
                    [
                        "world",
                        "hello",
                    ]
                ),
            ]
        )

        elements = ["well hello world!"]
        context = RegexTreeSplitterContext()

        # Act
        split = _regex_tree_splitter(context, elements, node)

        # Assert
        assert split is not None
        before, match, after = split
        # Even if "world" matches partially, the splitter should backtrack
        # and try the second branch, which matches fully.
        assert before == []
        assert match == ["well hello"]
        assert after == [" world!"]

    def test_nested_branching_backtracking_branching_at_root(self):
        # Arrange
        node = regex_tree.Branching(
            [
                regex_tree.Sequence(
                    [
                        "well ",
                        "world",
                    ]
                ),
                "goodbye",
            ]
        )

        elements = ["well hello world! goodbye!"]
        context = RegexTreeSplitterContext()

        # Act
        split = _regex_tree_splitter(context, elements, node)

        # Assert
        assert split is not None
        before, match, after = split
        # Even if "well " matches partially, the splitter should backtrack
        # and try the second branch, which matches fully.
        assert before == ["well hello world! "]
        assert match == ["goodbye"]
        assert after == ["!"]


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
        splitter = make_regex_tree_splitter(group_node)
        result = splitter(elements)

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
        splitter = make_regex_tree_splitter(group_node)
        result = splitter(elements)

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


class TestRecombineStrings(BaseTestCaseHtml):

    def test_group_and_recombine_strings(self):
        # Arrange
        elements = [
            "text1 ",
            "text2",
            self.make_tag("br"),
            " text3 ",
            " text4",
        ]

        # Act
        recombined = recombine_strings(elements)

        # Assert
        assert recombined == [
            "text1 text2",
            self.make_tag("br"),
            " text3  text4",
        ]

    def test_recombine_strings_with_separator(self):
        # Arrange
        elements = [
            "text1",
            "text2",
        ]

        # Act
        recombined = recombine_strings(elements, separator="/")

        # Assert
        assert recombined == [
            "text1/text2",
        ]
