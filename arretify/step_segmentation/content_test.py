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

from arretify.parsing_utils.source_mapping import initialize_lines
from arretify.types import TextSegments, TextSegment
from .content import parse_section_titles, parse_sections
from .core import Node, NodeFlow, is_node


class TestParseSectionTitles(unittest.TestCase):

    def test_parse_section_titles(self):
        # Arrange
        lines = _l(
            "Titre I - Introduction",
            "1. Contexte",
            "bla bla bla",
            "2. Objectifs",
            "blo blo blo",
            "bli bli bli",
            "Titre II - Méthodologie",
            "blu blu blu",
            "ble ble ble",
        )

        # Act
        result = list(parse_section_titles(lines))

        # Assert
        assert_node_flows_equal(
            result,
            [
                Node(
                    type="section_title",
                    children=[
                        _l("Titre I - Introduction"),
                    ],
                    data=dict(
                        level=0,
                        number="I",
                        title="Introduction",
                        type="titre",
                    ),
                ),
                Node(
                    type="section_title",
                    children=[
                        _l("1. Contexte"),
                    ],
                    data=dict(
                        level=1,
                        number="1",
                        title="Contexte",
                        type="unknown",
                    ),
                ),
                _l("bla bla bla"),
                Node(
                    type="section_title",
                    children=[_l("2. Objectifs")],
                    data=dict(
                        level=1,
                        number="2",
                        title="Objectifs",
                        type="unknown",
                    ),
                ),
                _l(
                    "blo blo blo",
                    "bli bli bli",
                ),
                Node(
                    type="section_title",
                    children=[_l("Titre II - Méthodologie")],
                    data=dict(
                        level=0,
                        number="II",
                        title="Méthodologie",
                        type="titre",
                    ),
                ),
                _l(
                    "blu blu blu",
                    "ble ble ble",
                ),
            ],
        )


class TestParseSections(unittest.TestCase):

    def test_parse_sections(self):
        # Arrange
        node_flow = [
            _l("bly bly bly"),
            Node(
                type="section_title",
                data=dict(level=1),
                children=[
                    _l("Titre I - Introduction"),
                ],
            ),
            Node(
                type="section_title",
                data=dict(level=2),
                children=[
                    _l("1. Contexte"),
                ],
            ),
            _l("bla bla bla"),
            Node(
                type="section_title",
                data=dict(level=2),
                children=[
                    _l("2. Objectifs"),
                ],
            ),
            _l(
                "blo blo blo",
                "bli bli bli",
            ),
            Node(
                type="section_title",
                data=dict(level=1),
                children=[
                    _l("Titre II - Méthodologie"),
                ],
            ),
            _l(
                "blu blu blu",
                "ble ble ble",
            ),
        ]

        # Act
        result = list(parse_sections(node_flow, level=1))

        # Assert
        assert_node_flows_equal(
            result,
            [
                Node(
                    type="alinea",
                    children=[_l("bly bly bly")],
                    data=dict(number="1"),
                ),
                Node(
                    type="section",
                    children=[
                        Node(
                            type="section_title",
                            children=[_l("Titre I - Introduction")],
                        ),
                        Node(
                            type="section",
                            children=[
                                Node(type="section_title", children=[_l("1. Contexte")]),
                                Node(
                                    type="alinea",
                                    children=[_l("bla bla bla")],
                                    data=dict(number="1"),
                                ),
                            ],
                        ),
                        Node(
                            type="section",
                            children=[
                                Node(type="section_title", children=[_l("2. Objectifs")]),
                                Node(
                                    type="alinea",
                                    children=[_l("blo blo blo")],
                                    data=dict(number="1"),
                                ),
                                Node(
                                    type="alinea",
                                    children=[_l("bli bli bli")],
                                    data=dict(number="2"),
                                ),
                            ],
                        ),
                    ],
                ),
                Node(
                    type="section",
                    children=[
                        Node(
                            type="section_title",
                            children=[_l("Titre II - Méthodologie")],
                        ),
                        Node(
                            type="alinea",
                            children=[_l("blu blu blu")],
                            data=dict(number="1"),
                        ),
                        Node(
                            type="alinea",
                            children=[_l("ble ble ble")],
                            data=dict(number="2"),
                        ),
                    ],
                ),
            ],
        )

    def test_parse_sections_contents(self):
        # Arrange
        node_flow = [
            Node(
                type="section_title",
                data=dict(level=0),
                children=[_l("1. Bla")],
            ),
            _l("bla bla bla"),
            Node(
                type="section_title",
                data=dict(level=1),
                children=[_l("1.1. Blabla")],
            ),
            _l("bli bli bli"),
        ]

        # Act
        result = list(parse_sections(node_flow, level=0))

        # Assert
        assert_node_flows_equal(
            result,
            [
                Node(
                    type="section",
                    children=[
                        Node(
                            type="section_title",
                            children=[
                                _l("1. Bla"),
                            ],
                        ),
                        Node(
                            type="alinea",
                            children=[_l("bla bla bla")],
                            data=dict(number="1"),
                        ),
                        Node(
                            type="section",
                            children=[
                                Node(
                                    type="section_title",
                                    children=[_l("1.1. Blabla")],
                                ),
                                Node(
                                    type="alinea",
                                    children=[_l("bli bli bli")],
                                    data=dict(number="1"),
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        )

    def test_parse_sections_missing_level(self):
        # Arrange
        node_flow = [
            Node(
                type="section_title",
                data=dict(level=0),
                children=[
                    _l("1. Bla"),
                ],
            ),
            Node(
                type="section_title",
                data=dict(level=2),
                children=[
                    _l("1.1.1. Blabla"),
                ],
            ),
        ]

        # Act
        result = list(parse_sections(node_flow, level=0))

        # Assert
        assert_node_flows_equal(
            result,
            [
                Node(
                    type="section",
                    children=[
                        Node(
                            type="section_title",
                            children=[_l("1. Bla")],
                        ),
                        Node(
                            type="section",
                            children=[
                                Node(
                                    type="section_title",
                                    children=[_l("1.1.1. Blabla")],
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        )

    def test_parse_missing_title_current_level(self):
        # Arrange
        node_flow = [
            Node(
                type="section_title",
                data=dict(level=1),
                children=[
                    _l("1.1. bla"),
                ],
            ),
            Node(
                type="section_title",
                data=dict(level=2),
                children=[
                    _l("1.1.1. bla"),
                ],
            ),
            Node(
                type="section_title",
                data=dict(level=1),
                children=[
                    _l("1.2. bla"),
                ],
            ),
            Node(
                type="section_title",
                data=dict(level=0),
                children=[
                    _l("2. bla"),
                ],
            ),
            Node(
                type="section_title",
                data=dict(level=1),
                children=[
                    _l("2.1. bla"),
                ],
            ),
        ]

        # Act
        result = list(parse_sections(node_flow, level=0))

        # Assert
        assert_node_flows_equal(
            result,
            [
                Node(
                    type="section",
                    children=[
                        Node(
                            type="section_title",
                            children=[_l("1.1. bla")],
                        ),
                        Node(
                            type="section",
                            children=[
                                Node(
                                    type="section_title",
                                    children=[_l("1.1.1. bla")],
                                ),
                            ],
                        ),
                    ],
                ),
                Node(
                    type="section",
                    children=[
                        Node(
                            type="section_title",
                            children=[_l("1.2. bla")],
                        ),
                    ],
                ),
                Node(
                    type="section",
                    children=[
                        Node(
                            type="section_title",
                            children=[_l("2. bla")],
                        ),
                        Node(
                            type="section",
                            children=[
                                Node(
                                    type="section_title",
                                    children=[_l("2.1. bla")],
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        )


def assert_node_flows_equal(actual: NodeFlow, expected: NodeFlow, path=""):
    actual = list(actual)
    expected = list(expected)
    assert len(actual) == len(
        expected
    ), f"[{path}] Expected {len(expected)} nodes, got {len(actual)}"
    for i, (a, e) in enumerate(zip(actual, expected)):
        child_path = f"{path}/{i}"
        if is_node(e):
            assert is_node(a, type_in=[e.type]), f"[{child_path}] Expected {e}, got {a}"
            # Test data only if defined is test expectations
            if e.data:
                assert a.data == e.data, f"[{child_path}] Expected {e.data}, got {a.data}"
            assert_node_flows_equal(a.children, e.children, path=child_path)
        else:
            assert isinstance(a, list), f"[{child_path}] Expected TextSegments, got {a}"
            assert isinstance(e, list)
            assert line_column_to_zero(a) == line_column_to_zero(
                e
            ), f"[{child_path}] Expected {e}, got {a}"


def line_column_to_zero(lines: TextSegments) -> TextSegments:
    return [TextSegment(contents=t.contents, start=(0, 0), end=(0, 0)) for t in lines]


def assert_text_segments_equal(actual: TextSegments, expected: TextSegments):
    assert len(actual) == len(expected), f"Expected {len(expected)} segments, got {len(actual)}"


def _l(*raw_lines: str):
    return initialize_lines(list(raw_lines))
