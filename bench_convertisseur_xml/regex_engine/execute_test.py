import unittest
import re
from dataclasses import dataclass
from typing import List, Union

from .execute import match
from .types import MatchGroup
from .compile import Sequence, Branching, Group, Quantifier


class TestSearchCompiledPattern(unittest.TestCase):

    def test_complex_match(self):
        # Arrange
        compiled_pattern = Group(
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
        result = match(compiled_pattern, string)

        # Assert
        assert result == MatchGroup(
            group_name='root',
            match_dict=dict(greetings='Hi'),
            children=[
                'Hi ',
                MatchGroup(
                    group_name='nickname',
                    match_dict=dict(nickname='seb'),
                    children=['hello_seb'],
                ),
                ',',
                MatchGroup(
                    group_name='nickname',
                    match_dict=dict(),
                    children=['123'],
                ),
                ',',
                MatchGroup(
                    group_name='nickname',
                    match_dict=dict(nickname='john'),
                    children=['hello_john'],
                ),
            ]
        )
