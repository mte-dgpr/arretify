import unittest
import re
from typing import Iterator

from . import regex_tree
from .split_with_regex_tree import split_string_with_regex_tree
from .types import MatchNamedGroup, Settings
from .core import MatchFlow, PatternProxy
from bench_convertisseur_xml.types import PageElementOrString


class TestSplitStringWithRegexTree(unittest.TestCase):

    def test_simple(self):
        # Arrange
        group_node = regex_tree.Group(
            regex_tree.Sequence(
                [
                    'poi',
                    'MLK',
                ],
            ),
            group_name='root',
        )
        string = 'blaPoiMLKblo'

        # Act
        actual_results = list(split_string_with_regex_tree(group_node, string))
        
        # Assert
        expected_results = [
            "bla", 
            regex_tree.Match(
                group_name='root',
                match_dict=dict(),
                children=[
                    'Poi',
                    'MLK',
                ]
            ),
            "blo"
        ]
        assert actual_results == expected_results

    def test_simple_no_match(self):
        # Arrange
        group_node = regex_tree.Group(
            regex_tree.Leaf('poi'),
            group_name='root',
        )
        string = 'blaMLKblo'

        # Act
        actual_results = list(split_string_with_regex_tree(group_node, string))
        
        # Assert
        expected_results = ["blaMLKblo"]
        assert actual_results == expected_results

    def test_nested_no_match(self):
        # Arrange
        group_node = regex_tree.Group(
            regex_tree.Sequence(
                [
                    r'poi',
                    regex_tree.Leaf(
                        'POI', 
                        settings=Settings(ignore_case=False)
                    ),
                ], 
                settings=Settings(ignore_case=True)
            ),
            group_name='root',
        )
        # Should not match because of ignore_case=False in the leaf
        string = 'blaPoipoiblo'

        # Act
        actual_results = list(split_string_with_regex_tree(group_node, string))
        
        # Assert
        expected_results = [
            "blaPoipoiblo",
        ]
        assert actual_results == expected_results