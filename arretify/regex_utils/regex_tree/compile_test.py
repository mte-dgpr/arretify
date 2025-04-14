import unittest

from .compile import Literal, Group, Quantifier, Branching, Sequence
from . import compile


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
        node = Quantifier(Literal(pattern_string=r"\w+"), r"+")

        # Assert
        assert node.pattern.pattern == r"(\w+)+"
        assert node.child.pattern.pattern == r"\w+"

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
        quantifier_node = Quantifier(
            child1,
            r"+",
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

    def test_node_repr(self):
        # Arrange
        compile._COUNTER = 0
        node1 = Literal(r"bla")
        node2 = Literal(r"bla|blo|bli|blu")

        # Assert
        assert repr(node1) == f'<{node1.id}, LiteralNode, "bla">'
        assert repr(node2) == f'<{node2.id}, LiteralNode, "bla|blo|bl...">'
