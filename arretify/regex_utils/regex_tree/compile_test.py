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

from arretify.regex_utils.types import Settings

from . import compile
from .compile import (
    Branching,
    Group,
    Literal,
    NonCapturing,
    Optional,
    Repeat,
    Sequence,
    _initialize_child,
)
from .types import BranchingNode, GroupNode, SequenceNode


class TestCompilePattern(unittest.TestCase):

    def test_compile_simple_pattern(self):
        # Arrange
        node = Literal(r"\d+")

        # Assert
        assert node.id
        assert node.pattern.pattern == r"\d+"

    def test_compile_or_pattern(self):
        # Arrange
        node = Branching([Literal(pattern_string=r"bla(?P<index>\d+)"), r"\w+"])
        assert len(node.children) == 2
        ids = list(node.children.keys())

        # Assert
        assert node.pattern.pattern == r"(?P<" + ids[0] + r">bla(\d+))|(?P<" + ids[1] + r">\w+)"
        assert node.children[ids[0]].pattern.pattern == r"bla(?P<index>\d+)"
        assert node.children[ids[1]].pattern.pattern == r"\w+"

    def test_compile_sequence_pattern(self):
        # Arrange
        node = Sequence([Literal(r"bla(?P<index>\d+)"), r"\w+"])
        assert len(node.children) == 2
        ids = list(node.children.keys())

        # Assert
        assert node.pattern.pattern == r"(?P<" + ids[0] + r">bla(\d+))(?P<" + ids[1] + r">\w+)"
        assert node.children[ids[0]].pattern.pattern == r"bla(?P<index>\d+)"

    def test_compile_repeat_pattern(self):
        # Arrange
        node = Repeat(Literal(pattern_string=r"\w+"), (1, ...))

        # Assert
        assert node.pattern.pattern == r"(\w+)+"
        assert node.child.pattern.pattern == r"\w+"

    def test_compile_repeat_pattern_with_separator(self):
        # Arrange
        node = Repeat(Literal(pattern_string=r"\w+"), (1, ...), separator=",")

        # Assert
        assert node.pattern.pattern == r"(\w+)((,)(\w+))*"

    def test_compile_group_pattern(self):
        # Arrange
        node = Group(
            r"(blabla)+",
            "group1",
        )

        # Assert
        assert node.group_name == "group1"
        assert node.pattern.pattern == r"(?P<" + node.child.id + r">(blabla)+)"
        assert node.child.pattern.pattern == r"(blabla)+"

    def test_children_nodes_have_unique_ids(self):
        # Arrange
        child1 = Literal(r"bla")
        child2 = Literal(r"blo")
        sequence_node = Sequence(
            [
                child1,
                child2,
            ]
        )
        quantifier_node = Repeat(
            child1,
            (1, ...),
        )
        branching_node = Branching(
            [
                child1,
                child2,
            ]
        )
        group_node = Group(
            child1,
            "group1",
        )

        # Assert
        for node in [sequence_node, branching_node]:
            children = list(node.children.values())
            assert len(children) == 2
            assert children[0].pattern is child1.pattern
            assert children[0].id != child1.id
            assert children[1].pattern is child2.pattern
            assert children[1].id != child2.id

        for node in [quantifier_node, group_node]:
            assert node.child.pattern is child1.pattern
            assert node.child.id != child1.id

    def test_compile_literal_with_key(self):
        # Arrange
        node = Literal(r"bla", key="key1")

        # Assert
        assert node.key == "key1"
        assert node.pattern.pattern == r"(?P<key1>bla)"

    def test_node_repr(self):
        # Arrange
        compile._COUNTER = 0
        node1 = Literal(r"bla")
        node2 = Literal(r"bla|blo|bli|blu")

        # Assert
        assert repr(node1) == f'<{node1.id}, LiteralNode, "bla">'
        assert repr(node2) == f'<{node2.id}, LiteralNode, "bla|blo|bl...">'


class TestInitializeChild(unittest.TestCase):

    def test_initialize_child_with_optional_node_not_in_sequence_raises_error(self):
        with self.assertRaises(ValueError) as context:
            _initialize_child(BranchingNode, Optional(r"test"), Settings())
        assert "OptionalNode is allowed only in SequenceNode" in str(context.exception)

    def test_initialize_child_with_non_capturing_node_not_in_sequence_raises_error(self):
        with self.assertRaises(ValueError) as context:
            _initialize_child(GroupNode, NonCapturing(r"test"), Settings())
        assert "NonCapturingNode is allowed only in SequenceNode" in str(context.exception)

    def test_initialize_child_with_optional_node_in_sequence_works(self):
        node = _initialize_child(SequenceNode, Optional(r"test"), Settings())
        assert node is not None


class TestRepeat(unittest.TestCase):

    def test_repeat_with_min_0_raises_error(self):
        with self.assertRaises(ValueError) as context:
            Repeat(Literal(r"test"), (0, 3))
        assert "Quantifier min must be >= 1" in str(context.exception)


class TestSequence(unittest.TestCase):

    def test_single_non_capturing_at_beginning_works(self):
        node = Sequence([NonCapturing(r"a"), r"middle", r"last"])
        assert len(node.children) == 3

    def test_single_non_capturing_at_end_works(self):
        node = Sequence([r"first", r"middle", NonCapturing(r"a")])
        assert len(node.children) == 3

    def test_multiple_optional_nodes_at_beginning_works(self):
        node = Sequence([Optional(r"a"), Optional(r"b"), r"middle", r"last"])
        assert len(node.children) == 4

    def test_non_capturing_node_in_middle_raises_error(self):
        with self.assertRaises(ValueError):
            Sequence([r"first", NonCapturing(r"middle"), r"last"])

    def test_multiple_non_capturing_nodes_at_beginning_raises_error(self):
        with self.assertRaises(ValueError):
            Sequence([NonCapturing(r"a"), NonCapturing(r"b"), r"middle"])

    def test_mix_optional_and_non_capturing_at_beginning_raises_error(self):
        with self.assertRaises(ValueError):
            Sequence([Optional(r"a"), NonCapturing(r"b"), r"middle"])
