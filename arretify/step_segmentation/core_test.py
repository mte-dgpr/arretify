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

from arretify.regex_utils import PatternProxy
from .core import (
    make_while_splitter_for_text_segments,
    pick_text_segment,
    group_text_segments_splitter,
    Node,
    make_probe_from_pattern_proxy,
)
from .testing import _l


class TestMakeTextSegmentWhileSplitter(unittest.TestCase):

    def test_rejects_non_text_segments(self):
        # Arrange
        def probe(elements, index):
            return elements[index].contents.startswith("match")

        splitter = make_while_splitter_for_text_segments(
            probe,
            probe,
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
        def probe(elements, index):
            return elements[index].contents.startswith("match")

        splitter = make_while_splitter_for_text_segments(
            probe,
            probe,
        )
        elements = _l("no match", "match this", "match that", "no match")

        # Act
        result = splitter(elements)

        # Assert
        assert result == (elements[:1], elements[1:3], elements[3:])

    def test_start_is_matching_argument(self):
        # Arrange
        def start_condition(elements, index):
            return elements[index].contents == "match this"

        def while_condition(elements, index):
            return elements[index].contents.startswith("match")

        splitter = make_while_splitter_for_text_segments(
            start_condition,
            while_condition,
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
        def probe(elements, index):
            return elements[index].contents.startswith("match")

        splitter = make_while_splitter_for_text_segments(probe, probe)
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
        elements = [
            Node(type="node1", children=[]),
            *_l("line1", "line2", "line3"),
            Node(type="node2", children=[]),
        ]

        # Act
        result = group_text_segments_splitter(elements)

        # Assert
        assert result == (
            [
                Node(type="node1", children=[]),
            ],
            _l("line1", "line2", "line3"),
            [
                Node(type="node2", children=[]),
            ],
        )


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


class TestPickTextSegments(unittest.TestCase):

    def test_simple(self):
        # Arrange
        elements = [
            *_l("text1"),
            Node(type="some_node", children=[]),
            *_l("text2", "text3"),
        ]

        def probe(elements, index):
            return elements[index].contents.startswith("text")

        # Act
        text_segments_probe = pick_text_segment(probe)

        # Assert
        assert text_segments_probe(elements, 0) is True
        # If pick_text_segment not used, this should raise an error
        assert text_segments_probe(elements, 1) is False
        assert text_segments_probe(elements, 2) is True
        assert text_segments_probe(elements, 3) is True
