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

from .execute import match
from .types import RegexTreeMatch, Settings
from .compile import Sequence, Branching, Group, Repeat, Literal


class TestSearchCompiledPattern(unittest.TestCase):

    def test_complex_match(self):
        # Arrange
        compiled_pattern = Group(
            Sequence(
                [
                    r"(?P<greetings>Hello|Hi) ",
                    Repeat(
                        Sequence(
                            [
                                Group(
                                    Branching(
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
        string = "Hi hello_seb,123,hello_john"

        # Act
        result = match(compiled_pattern, string)

        # Assert
        assert result == RegexTreeMatch(
            group_name="root",
            match_dict=dict(greetings="Hi"),
            children=[
                "Hi ",
                RegexTreeMatch(
                    group_name="nickname",
                    match_dict=dict(nickname="seb"),
                    children=["hello_seb"],
                ),
                ",",
                RegexTreeMatch(
                    group_name="nickname",
                    match_dict=dict(),
                    children=["123"],
                ),
                ",",
                RegexTreeMatch(
                    group_name="nickname",
                    match_dict=dict(nickname="john"),
                    children=["hello_john"],
                ),
            ],
        )

    def test_no_match_simple(self):
        # Arrange
        compiled_pattern = Group(
            Sequence(
                [
                    r"bla",
                    r"blo",
                ]
            ),
            group_name="root",
        )

        # Act
        result = match(compiled_pattern, "hello")

        # Assert
        assert result is None

    def test_match_second_branch_when_first_nested_fails(self):
        # When a first branch succeeds, but then a nested node fails
        # because it has different settings than the Branch node,
        # then the second branch should be tried.

        # Arrange
        compiled_pattern = Group(
            Branching(
                [
                    Literal(
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
        result = match(compiled_pattern, "hello")

        # Assert
        assert result == RegexTreeMatch(
            group_name="root",
            match_dict=dict(branch2="hello"),
            children=["hello"],
        )
