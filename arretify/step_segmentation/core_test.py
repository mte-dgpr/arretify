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

from arretify.types import TextSegment
from arretify.regex_utils import PatternProxy
from .core import (
    split_elements,
    make_single_line_splitter,
    make_while_splitter,
    make_text_segment_while_splitter,
    make_negated_probe,
    split_before_match,
    text_segment_group_splitter,
    SplitMatch,
    SplitNotAMatch,
    Node,
    make_probe_from_pattern_proxy,
)
from .testing import _l, assert_elements_equal


class TestSplitBeforeMatch(unittest.TestCase):

    def test_no_match(self):
        # Arrange
        node_list = [
            Node(type="bla", children=[]),
            *_l("a", "b", "c"),
            Node(type="blo", children=[]),
        ]

        def is_matching(elements, i):
            return isinstance(elements[i], TextSegment) and elements[i].contents == "d"

        # Act
        before, after = split_before_match(node_list, is_matching)

        # Assert
        assert_elements_equal(before, node_list)
        assert_elements_equal(after, [])

    def test_match_first_line(self):
        # Arrange
        node_list = _l("match", "b", "c")

        def is_matching(elements, i):
            return isinstance(elements[i], TextSegment) and elements[i].contents == "match"

        # Act
        before, after = split_before_match(node_list, is_matching)

        # Assert
        assert_elements_equal(before, [])
        assert_elements_equal(after, _l("match", "b", "c"))

    def test_match_middle_line(self):
        # Arrange
        node_list = [
            Node(type="bla", children=[]),
            *_l("a", "match", "c"),
            Node(type="blo", children=[]),
        ]

        def is_matching(elements, i):
            return isinstance(elements[i], TextSegment) and elements[i].contents == "match"

        # Act
        before, after = split_before_match(node_list, is_matching)

        # Assert
        assert_elements_equal(before, [Node(type="bla", children=[]), *_l("a")])
        assert_elements_equal(after, [*_l("match", "c"), Node(type="blo", children=[])])

    def test_match_last_line(self):
        # Arrange
        node_list = _l("a", "b", "match")

        def is_matching(elements, i):
            return isinstance(elements[i], TextSegment) and elements[i].contents == "match"

        # Act
        before, after = split_before_match(node_list, is_matching)

        # Assert
        assert_elements_equal(before, _l("a", "b"))
        assert_elements_equal(after, _l("match"))


class TestSplitElements(unittest.TestCase):

    def test_no_matches(self):
        # Arrange
        elements = _l("a", "b", "c")

        def splitter(elements):
            return None

        # Act
        result = list(split_elements(elements, splitter))

        # Assert
        assert result == [SplitNotAMatch(elements)]

    def test_all_match_start(self):
        # Arrange
        elements = _l("start1", "start2")

        def splitter(elements):
            return ([], elements, [])

        # Act
        result = list(split_elements(elements, splitter))

        # Assert
        assert result == [SplitMatch(elements)]

    def test_mixed_match(self):
        # Arrange
        elements = _l("a", "b", "c", "d", "e", "f", "g")

        def splitter(elements):
            return (
                (elements[0:1], elements[1:3], elements[3:]) if len(elements) >= 3 else None
            )  # Matches [b, c] and [e, f]

        # Act
        result = list(split_elements(elements, splitter))

        # Assert
        expected = [
            SplitNotAMatch(elements[:1]),  # 'a' does not match
            SplitMatch(elements[1:3]),  # 'b', 'c' matches
            SplitNotAMatch(elements[3:4]),  # 'd' does not match
            SplitMatch(elements[4:6]),  # 'e', 'f' matches
            SplitNotAMatch(elements[6:]),  # 'g' does not match
        ]
        assert result == expected

    def test_contiguous_matching_segments(self):
        # Arrange
        elements = _l("start1", "start2", "start3")

        def splitter(elements):
            return ([], elements[0:1], elements[1:])

        # Act
        result = list(split_elements(elements, splitter))

        # Assert
        expected = [
            SplitMatch(elements[0:1]),
            SplitMatch(elements[1:2]),
            SplitMatch(elements[2:3]),
        ]
        assert result == expected


class TestMakeSingleLineSplitter(unittest.TestCase):

    def test_match_found(self):
        # Arrange
        splitter = make_single_line_splitter(
            lambda elements, index: elements[index].contents == "match"
        )
        elements = _l("no match", "match", "no match")

        # Act
        result = splitter(elements)

        # Assert
        assert result == (elements[:1], elements[1:2], elements[2:])

    def test_match_found_first_line(self):
        # Arrange
        splitter = make_single_line_splitter(
            lambda elements, index: elements[index].contents == "match"
        )
        elements = _l("match", "no match", "no match")

        # Act
        result = splitter(elements)

        # Assert
        assert result == (elements[:0], elements[0:1], elements[1:])

    def test_no_match(self):
        # Arrange
        splitter = make_single_line_splitter(
            lambda elements, index: elements[index].contents == "match"
        )
        elements = _l("no match", "also no match")

        # Act
        result = splitter(elements)

        # Assert
        assert result is None


class TestMakeWhileSplitter(unittest.TestCase):

    def test_match_found(self):
        # Arrange
        splitter = make_while_splitter(
            lambda elements, index: elements[index].contents.startswith("match")
        )
        elements = _l("no match", "match1", "match2", "no match", "match3")

        # Act
        result = splitter(elements)

        # Assert
        assert result == (elements[:1], elements[1:3], elements[3:])

    def test_match_found_first_line(self):
        # Arrange
        splitter = make_while_splitter(
            lambda elements, index: elements[index].contents.startswith("match")
        )
        elements = _l("match1", "match2", "no match", "match3")

        # Act
        result = splitter(elements)

        # Assert
        assert result == (elements[:0], elements[0:2], elements[2:])

    def test_match_found_last_line(self):
        # Arrange
        splitter = make_while_splitter(
            lambda elements, index: elements[index].contents.startswith("match")
        )
        elements = _l("no match", "match1", "match2")

        # Act
        result = splitter(elements)

        # Assert
        assert result == (elements[:1], elements[1:3], [])

    def test_no_match(self):
        # Arrange
        splitter = make_while_splitter(
            lambda elements, index: elements[index].contents.startswith("match")
        )
        elements = _l("no match", "also no match")

        # Act
        result = splitter(elements)

        # Assert
        assert result is None


class TestMakeNegatedProbe(unittest.TestCase):

    def test_negated_probe(self):
        # Arrange
        probe = make_negated_probe(
            lambda elements, index: elements[index].contents.startswith("match")
        )
        elements = _l("no match", "also no match", "match this")

        # Assert
        assert probe(elements, 0) is True  # "no match"
        assert probe(elements, 1) is True  # "also no match"
        assert probe(elements, 2) is False  # "match this"


class TestMakeTextSegmentWhileSplitter(unittest.TestCase):

    def test_rejects_non_text_segments(self):
        # Arrange
        splitter = make_text_segment_while_splitter(
            lambda elements, index: elements[index].contents.startswith("match")
        )
        elements = [
            Node(type="non_text", children=[]),
            *_l("match this"),
            Node(type="another_non_text", children=[]),
        ]

        # Act
        result = splitter(elements)

        # Assert
        assert result == (elements[0:1], elements[1:2], elements[2:])

    def test_match_found(self):
        # Arrange
        splitter = make_text_segment_while_splitter(
            lambda elements, index: elements[index].contents.startswith("match")
        )
        elements = _l("no match", "match this", "match that", "no match")

        # Act
        result = splitter(elements)

        # Assert
        assert result == (elements[:1], elements[1:3], elements[3:])

    def test_start_is_matching_argument(self):
        # Arrange
        splitter = make_text_segment_while_splitter(
            lambda elements, index: elements[index].contents.startswith("match"),
            start_is_matching=lambda elements, index: elements[index].contents == "match this",
        )
        elements = [
            Node(type="some_node", children=[]),
            *_l("match this", "match that", "no match"),
        ]

        # Act
        result = splitter(elements)

        # Assert
        assert result == (elements[:1], elements[1:3], elements[3:])

    def test_not_interrupted_by_inline_node(self):
        # Arrange
        splitter = make_text_segment_while_splitter(
            lambda elements, index: elements[index].contents.startswith("match")
        )
        elements = [
            *_l("match this"),
            Node(type="page_separator", children=[]),
            *_l("match this too", "but not this"),
        ]

        # Act
        result = splitter(elements)

        # Assert
        assert result == ([], elements[0:3], elements[3:])


class TestTextSegmentGroupSplitter(unittest.TestCase):

    def test_single_text_segment(self):
        # Arrange
        input_list = [
            Node(type="node1", children=[]),
            *_l("line1", "line2", "line3"),
            Node(type="node2", children=[]),
        ]

        # Act
        result = text_segment_group_splitter(input_list)

        # Assert
        assert result is not None
        before, match, after = result
        assert_elements_equal(before, [Node(type="node1", children=[])])
        assert_elements_equal(match, _l("line1", "line2", "line3"))
        assert_elements_equal(after, [Node(type="node2", children=[])])


class TestMakeTextSegmentProbeFromPattern(unittest.TestCase):

    def test_pattern_match(self):
        # Arrange
        pattern = PatternProxy(r"^match")
        probe = make_probe_from_pattern_proxy(pattern)
        lines = _l("match this")

        # Act
        result = probe(lines, 0)

        # Assert
        assert result is True

    def test_pattern_no_match(self):
        # Arrange
        pattern = PatternProxy(r"^match")
        probe = make_probe_from_pattern_proxy(pattern)
        lines = _l("no match here")

        # Act
        result = probe(lines, 0)

        # Assert
        assert result is False
