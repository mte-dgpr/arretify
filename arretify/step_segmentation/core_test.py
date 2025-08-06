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
    make_while_splitter_for_text_span_nodes,
    pick_text_span_node,
    group_text_span_nodes_splitter,
    Node,
    make_probe_from_pattern_proxy,
    get_string,
    combine_text_spans,
)
from .testing import _l, make_text_spans


class TestMakeTextSegmentWhileSplitter(unittest.TestCase):

    def test_rejects_non_text_segments(self):
        # Arrange
        def probe(elements, index):
            return elements[index].children[0].contents.startswith("match")

        splitter = make_while_splitter_for_text_span_nodes(
            probe,
            probe,
        )
        elements = [
            Node(type="non_text", children=[]),
            *make_text_spans("match this"),
            Node(type="another_non_text", children=[]),
        ]

        # Act
        result = splitter(elements)

        # Assert
        assert result == (elements[0:1], elements[1:2], elements[2:])

    def test_match_found(self):
        # Arrange
        def probe(elements, index):
            return elements[index].children[0].contents.startswith("match")

        splitter = make_while_splitter_for_text_span_nodes(
            probe,
            probe,
        )
        elements = make_text_spans("no match", "match this", "match that", "no match")

        # Act
        result = splitter(elements)

        # Assert
        assert result == (elements[:1], elements[1:3], elements[3:])

    def test_start_is_matching_argument(self):
        # Arrange
        def start_condition(elements, index):
            return elements[index].children[0].contents == "match this"

        def while_condition(elements, index):
            return elements[index].children[0].contents.startswith("match")

        splitter = make_while_splitter_for_text_span_nodes(
            start_condition,
            while_condition,
        )
        elements = [
            Node(type="some_node", children=[]),
            *make_text_spans("match this", "match that", "no match"),
        ]

        # Act
        result = splitter(elements)

        # Assert
        assert result == (elements[:1], elements[1:3], elements[3:])

    def test_not_interrupted_by_inline_node(self):
        # Arrange
        def probe(elements, index):
            return elements[index].children[0].contents.startswith("match")

        splitter = make_while_splitter_for_text_span_nodes(probe, probe)
        elements = [
            *make_text_spans("match this"),
            Node(type="page_separator", children=[]),
            *make_text_spans("match this too", "but not this"),
        ]

        # Act
        result = splitter(elements)

        # Assert
        assert result == ([], elements[0:3], elements[3:])


class TestGroupTextSpanNodesSplitter(unittest.TestCase):

    def test_single_text_segment(self):
        # Arrange
        elements = [
            Node(type="node1", children=[]),
            Node(type="text_span", children=_l("line1")),
            Node(type="text_span", children=_l("line2", "line3")),
            Node(type="node2", children=[]),
        ]

        # Act
        result = group_text_span_nodes_splitter(elements)

        # Assert
        assert result == (
            [
                Node(type="node1", children=[]),
            ],
            [
                Node(type="text_span", children=_l("line1")),
                Node(type="text_span", children=_l("line2", "line3")),
            ],
            [
                Node(type="node2", children=[]),
            ],
        )


class TestMakeTextSegmentProbeFromPattern(unittest.TestCase):

    def test_pattern_match(self):
        # Arrange
        pattern = PatternProxy(r"^match")
        probe = make_probe_from_pattern_proxy(pattern)
        lines = make_text_spans("match this")

        # Act
        result = probe(lines, 0)

        # Assert
        assert result is True

    def test_pattern_no_match(self):
        # Arrange
        pattern = PatternProxy(r"^match")
        probe = make_probe_from_pattern_proxy(pattern)
        lines = make_text_spans("no match here")

        # Act
        result = probe(lines, 0)

        # Assert
        assert result is False


class TestPickTextSpanNode(unittest.TestCase):

    def test_simple(self):
        # Arrange
        elements = [
            Node(type="text_span", children=_l("bla1")),
            Node(type="some_node", children=[]),
            *_l("bla2"),
            Node(type="text_span", children=_l("blo4", "bla5")),
        ]

        def probe_first_child_starts_with_bla(elements, index):
            return elements[index].children[0].contents.startswith("bla")

        # Act
        text_span_node_probe = pick_text_span_node(probe_first_child_starts_with_bla)

        # Assert
        assert text_span_node_probe(elements, 0) is True  # text_span node with "bla1"
        assert text_span_node_probe(elements, 1) is False  # some_node
        assert text_span_node_probe(elements, 2) is False  # some TextSegment
        assert text_span_node_probe(elements, 3) is False  # text_span node with "blo4"


class TestGetString(unittest.TestCase):

    def test_text_segment(self):
        # Arrange
        text_segment = _l("This is a test")[0]

        # Act
        result = get_string(text_segment)

        # Assert
        assert result == "This is a test"

    def test_node_with_text_segments(self):
        # Arrange
        node = Node(type="some_node", children=_l("This is", " a test"))

        # Act
        result = get_string(node)

        # Assert
        assert result == "This is a test"

    def test_node_with_text_spans(self):
        # Arrange
        node = Node(
            type="some_node",
            children=[
                *_l("This is"),
                Node(type="text_span", children=_l(" a test")),
            ],
        )

        # Act
        result = get_string(node)

        # Assert
        assert result == "This is a test"

    def test_node_with_non_text_child(self):
        # Arrange
        node = Node(
            type="some_node",
            children=[
                *_l("This is"),
                Node(type="non_text", children=[]),
                *_l(" a test"),
            ],
        )

        # Assert
        with self.assertRaises(ValueError):
            get_string(node)


class TestCombineTextSpans(unittest.TestCase):

    def test_combine_list_text_spans_and_text_segments(self):
        # Arrange
        elements = [
            Node(
                type="text_span",
                children=[
                    TextSegment("This is", start=(1, 2, 3), end=(4, 5, 6)),
                ],
            ),
            Node(
                type="text_span",
                children=[
                    TextSegment(" a test", start=(7, 8, 9), end=(10, 11, 12)),
                    TextSegment(" with multiple lines.", start=(13, 14, 15), end=(16, 17, 18)),
                ],
            ),
        ]

        # Act
        result = combine_text_spans(elements)

        # Assert
        assert result == Node(
            type="text_span",
            children=[
                TextSegment("This is", start=(1, 2, 3), end=(4, 5, 6)),
                TextSegment(" a test", start=(7, 8, 9), end=(10, 11, 12)),
                TextSegment(" with multiple lines.", start=(13, 14, 15), end=(16, 17, 18)),
            ],
        )
