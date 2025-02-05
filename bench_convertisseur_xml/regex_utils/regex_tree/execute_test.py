import unittest
import re
from dataclasses import dataclass
from typing import List, Union

from .execute import match
from .types import RegexTreeMatch, Settings
from .compile import Sequence, Branching, Group, Quantifier, Leaf


class TestSearchCompiledPattern(unittest.TestCase):

    def test_complex_match(self):
        # Arrange
        group_node = Group(
            Sequence([
                r'(?P<greetings>Hello|Hi) ',
                Quantifier(
                    Sequence([
                        Group(
                            Branching([
                                r'hello_(?P<nickname>\w+)',
                                r'123',
                            ]),
                            'nickname',
                        ),
                        ',?'
                    ]),
                    quantifier='+',
                ),
            ]),
            group_name='root',
        )
        string = 'Hi hello_seb,123,hello_john'

        # Act
        result = match(group_node, string)

        # Assert
        assert result == RegexTreeMatch(
            group_name='root',
            match_dict=dict(greetings='Hi'),
            children=[
                'Hi ',
                RegexTreeMatch(
                    group_name='nickname',
                    match_dict=dict(nickname='seb'),
                    children=['hello_seb'],
                ),
                ',',
                RegexTreeMatch(
                    group_name='nickname',
                    match_dict=dict(),
                    children=['123'],
                ),
                ',',
                RegexTreeMatch(
                    group_name='nickname',
                    match_dict=dict(nickname='john'),
                    children=['hello_john'],
                ),
            ]
        )

    def test_nested_match_with_ignorecase(self):
        # Arrange
        group_node = Group(
            Sequence(
                [
                    r'poi',
                    Leaf(
                        'POI', 
                        settings=Settings(ignore_case=False)
                    ),
                ], 
                settings=Settings(ignore_case=True)
            ),
            group_name='root',
        )

        # Act
        result = match(group_node, 'PoiPOI')

        # Assert
        assert result == RegexTreeMatch(
            group_name='root',
            match_dict=dict(),
            children=[
                'Poi',
                'POI',
            ]
        )


    def test_nested_no_match_with_ignorecase(self):
        # Arrange
        group_node = Group(
            Sequence(
                [
                    r'poi',
                    Leaf(
                        'POI', 
                        settings=Settings(ignore_case=False)
                    ),
                ], 
                settings=Settings(ignore_case=True)
            ),
            group_name='root',
        )

        # Act
        # Should not match because of ignore_case=False
        result = match(group_node, 'poipoi')

        # Assert
        assert result == None
