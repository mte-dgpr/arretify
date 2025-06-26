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

from .content import parse_section_titles, parse_sections
from .core import Node
from .testing import (
    assert_node_flows_equal,
    _l,
)


class TestParseSectionTitles(unittest.TestCase):

    def test_parse_section_titles(self):
        # Arrange
        node_flow = [
            _l(
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
        ]

        # Act
        result = list(parse_section_titles(node_flow))

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
