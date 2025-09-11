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
    make_while_splitter_for_text_span_nodes,
    pick_text_span_node,
    pick_str,
    group_text_span_nodes_splitter,
    Node,
    make_probe_from_pattern_proxy,
    get_string,
    combine_text_spans,
    make_pattern_splitter,
    make_recombine_interrupted_lines_splitter,
)
from .testing import make_text_spans, assert_elements_equal


class TestMakeWhileSplitterForTextSpanNodes(unittest.TestCase):

    def test_rejects_non_text_span(self):
        # Arrange
        def probe(elements, index):
            return elements[index].children[0].startswith("match")

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
            return elements[index].children[0].startswith("match")

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
            return elements[index].children[0] == "match this"

        def while_condition(elements, index):
            return elements[index].children[0].startswith("match")

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

    def test_not_interrupted_by_transparent_node(self):
        # Arrange
        def probe(elements, index):
            return elements[index].children[0].startswith("match")

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

    def test_simple(self):
        # Arrange
        elements = [
            Node(type="node1", children=[]),
            Node(type="text_span", children=["line1"]),
            Node(type="text_span", children=["line2", "line3"]),
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
                Node(type="text_span", children=["line1"]),
                Node(type="text_span", children=["line2", "line3"]),
            ],
            [
                Node(type="node2", children=[]),
            ],
        )


class TestMakeProbeFromPatternProxy(unittest.TestCase):

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
            Node(type="text_span", children=["bla1"]),
            Node(type="some_node", children=[]),
            "bla2",
            Node(type="text_span", children=["blo4", "bla5"]),
        ]

        # Act
        text_span_node_probe = pick_text_span_node(lambda elements, index: True)

        # Assert
        assert text_span_node_probe(elements, 0) is True
        assert text_span_node_probe(elements, 1) is False
        assert text_span_node_probe(elements, 2) is False
        assert text_span_node_probe(elements, 3) is True


class TestPickStr(unittest.TestCase):

    def test_simple(self):
        # Arrange
        elements = [
            "bla1",
            Node(type="some_node", children=[]),
            "blo4",
        ]

        # Act
        probe = pick_str(lambda elements, index: True)

        # Assert
        assert probe(elements, 0) is True
        assert probe(elements, 1) is False
        assert probe(elements, 2) is True


class TestMakeRecombineInterruptedLinesSplitter(unittest.TestCase):

    def test_multiple_lines_and_page_separators(self):
        # Arrange
        splitter = make_recombine_interrupted_lines_splitter("some_type")
        elements = [
            Node(
                type="some_type",
                children=["This is a line"],
            ),
            Node(type="page_separator", children=[], data=dict(page_index=1)),
            *make_text_spans(
                " that continues ",
            ),
            Node(type="page_separator", children=[], data=dict(page_index=2)),
            Node(type="page_separator", children=[], data=dict(page_index=3)),
            *make_text_spans(
                " and continues again.",
            ),
        ]

        # Act
        result = splitter(elements)

        # Assert
        assert result is not None
        before, match, after = result
        assert_elements_equal(before, [])
        assert_elements_equal(
            match,
            (
                Node(
                    type="some_type",
                    children=["This is a line"],
                ),
                Node(type="page_separator", children=[], data=dict(page_index=1)),
                *make_text_spans(
                    " that continues ",
                ),
                Node(type="page_separator", children=[], data=dict(page_index=2)),
                Node(type="page_separator", children=[], data=dict(page_index=3)),
                *make_text_spans(
                    " and continues again.",
                ),
            ),
        )
        assert_elements_equal(after, [])

    def test_line_is_not_continuing(self):
        # Arrange
        splitter = make_recombine_interrupted_lines_splitter("some_type")
        elements = [
            Node(
                type="some_type",
                children=["This is a line."],
            ),
            Node(type="page_separator", children=[], data=dict(page_index=1)),
            *make_text_spans(
                "blo blo blo",
            ),
        ]

        # Act
        result = splitter(elements)

        # Assert
        assert result is None

    def test_line_is_continuing_but_no_page_separator(self):
        # Arrange
        splitter = make_recombine_interrupted_lines_splitter("some_type")
        elements = [
            Node(
                type="some_type",
                children=["This is a line"],
            ),
            *make_text_spans(" that continues."),
        ]

        # Act
        result = splitter(elements)

        # Assert
        assert result is None


class TestGetString(unittest.TestCase):

    def test_string(self):
        # Arrange
        string = "This is a test"

        # Act
        result = get_string(string)

        # Assert
        assert result == "This is a test"

    def test_node_with_string_children(self):
        # Arrange
        node = Node(type="some_node", children=["This is", " a test"])

        # Act
        result = get_string(node)

        # Assert
        assert result == "This is a test"

    def test_node_with_text_spans(self):
        # Arrange
        node = Node(
            type="some_node",
            children=[
                "This is",
                Node(type="text_span", children=[" a test"]),
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
                "This is",
                Node(type="non_text", children=[]),
                " a test",
            ],
        )

        # Assert
        with self.assertRaises(ValueError):
            get_string(node)

    def test_inline_nodes_inside_text_span(self):
        # Arrange
        node = Node(
            type="text_span",
            children=[
                "Viens au ",
                Node(type="address", children=["123 rue de la Paix"]),
                ", à 12h",
            ],
        )

        # Act
        result = get_string(node)

        # Assert
        assert result == "Viens au 123 rue de la Paix, à 12h"


class TestCombineTextSpans(unittest.TestCase):

    def test_combine_text_spans(self):
        # Arrange
        elements = [
            Node(
                type="text_span",
                children=["This is"],
                data=dict(start=(1, 2, 3), end=(4, 5, 6)),
            ),
            Node(
                type="text_span",
                children=[" a test", " with multiple lines."],
                data=dict(start=(7, 8, 9), end=(16, 17, 18)),
            ),
        ]

        # Act
        result = combine_text_spans(elements)

        # Assert
        assert_elements_equal(
            [result],
            [
                Node(
                    type="text_span",
                    children=[
                        "This is",
                        " a test",
                        " with multiple lines.",
                    ],
                    data=dict(start=(1, 2, 3), end=(16, 17, 18)),
                )
            ],
        )

    def test_containing_inline_node(self):
        # Arrange
        elements = [
            Node(
                type="text_span",
                children=["This is"],
                data=dict(start=(1, 2, 3), end=(4, 5, 6)),
            ),
            Node(
                type="text_span",
                children=[
                    " a test ",
                    Node(type="address", children=["123 rue de la Paix"]),
                    " with multiple lines.",
                ],
                data=dict(start=(7, 8, 9), end=(16, 17, 18)),
            ),
        ]

        # Act
        result = combine_text_spans(elements)

        # Assert
        assert_elements_equal(
            [result],
            [
                Node(
                    type="text_span",
                    children=[
                        "This is",
                        " a test ",
                        Node(type="address", children=["123 rue de la Paix"]),
                        " with multiple lines.",
                    ],
                    data=dict(start=(1, 2, 3), end=(16, 17, 18)),
                )
            ],
        )


class TestMakePatternSplitter(unittest.TestCase):

    def test_match_middle(self):
        # Arrange
        pattern = PatternProxy(r"\d+")
        splitter = make_pattern_splitter(pattern)
        elements = [
            "abc",
            Node(
                type="some_type",
                children=[],
            ),
            "def123ghi",
            Node(
                type="some_type",
                children=[],
            ),
            "jkl",
        ]

        # Act
        result = splitter(elements)

        # Assert
        assert result is not None
        before, match, after = result
        assert_elements_equal(
            before,
            [
                "abc",
                Node(
                    type="some_type",
                    children=[],
                ),
                "def",
            ],
        )
        assert_elements_equal(
            after,
            [
                "ghi",
                Node(
                    type="some_type",
                    children=[],
                ),
                "jkl",
            ],
        )
        assert match.group(0) == "123"

    def test_match_start(self):
        # Arrange
        pattern = PatternProxy(r"\d+")
        splitter = make_pattern_splitter(pattern)
        elements = ["123abc"]

        # Act
        result = splitter(elements)

        # Assert
        assert result is not None
        before, match, after = result
        assert_elements_equal(before, [])
        assert_elements_equal(after, ["abc"])
        assert match.group(0) == "123"

    def test_match_end(self):
        # Arrange
        pattern = PatternProxy(r"\d+")
        splitter = make_pattern_splitter(pattern)
        elements = ["jkl456"]

        # Act
        result = splitter(elements)

        # Assert
        assert result is not None
        before, match, after = result
        assert_elements_equal(before, ["jkl"])
        assert_elements_equal(after, [])
        assert match.group(0) == "456"

    def test_no_match(self):
        # Arrange
        pattern = PatternProxy(r"\d+")
        splitter = make_pattern_splitter(pattern)
        elements = ["abc", "defghi", "jkl"]

        # Act
        result = splitter(elements)

        # Assert
        assert result is None

    def test_match_across_segments(self):
        # Arrange
        pattern = PatternProxy(r"defghi")
        splitter = make_pattern_splitter(pattern)
        elements = ["abcdef", "ghijkl"]

        # Act
        result = splitter(elements)

        # Assert
        assert result is not None
        before, match, after = result
        assert_elements_equal(before, ["abc"])
        assert_elements_equal(after, ["jkl"])
        assert match.group(0) == "defghi"
