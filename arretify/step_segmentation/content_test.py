import unittest
from typing import List

from arretify.parsing_utils.source_mapping import initialize_lines
from arretify.types import TextSegments, TextSegment
from .content import parse_section_titles, parse_sections
from .core import Element, ElementFlow, is_element


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
        assert_element_flows_equal(result, [
            Element(
                name="section_title",
                contents=[
                    _l("Titre I - Introduction"),
                ],
                data=dict(
                    level=0,
                    number='I',
                    title='Introduction',
                    type='titre',
                ),
            ),
            Element(
                name="section_title",
                contents=[
                    _l("1. Contexte"),
                ],
                data=dict(
                    level=1,
                    number='1',
                    title='Contexte',
                    type='unknown',
                ),
            ),
            _l("bla bla bla"),
            Element(
                name="section_title",
                contents=[_l("2. Objectifs")],
                data=dict(
                    level=1,
                    number='2',
                    title='Objectifs',
                    type='unknown',
                ),
            ),
            _l(
                "blo blo blo", 
                "bli bli bli",
            ),
            Element(
                name="section_title",
                contents=[_l("Titre II - Méthodologie")],
                data=dict(
                    level=0,
                    number='II',
                    title='Méthodologie',
                    type='titre',
                ),
            ),
            _l(
                "blu blu blu",
                "ble ble ble",
            ),
        ])


class TestParseSections(unittest.TestCase):

    def test_parse_sections(self):
        # Arrange
        element_flow = [
            _l("bly bly bly"),
            Element(
                name="section_title",
                data=dict(level=1),
                contents=[
                    _l("Titre I - Introduction"),
                ],
            ),
            Element(
                name="section_title",
                data=dict(level=2),
                contents=[
                    _l("1. Contexte"),
                ],
            ),
            _l("bla bla bla"),
            Element(
                name="section_title",
                data=dict(level=2),
                contents=[
                    _l("2. Objectifs"),
                ],
            ),
            _l(
                "blo blo blo", 
                "bli bli bli",
            ),
            Element(
                name="section_title",
                data=dict(level=1),
                contents=[
                    _l("Titre II - Méthodologie"),
                ],
            ),
            _l(
                "blu blu blu",
                "ble ble ble",
            ),
        ]

        # Act
        result = list(parse_sections(element_flow, level=1))

        # Assert
        assert_element_flows_equal(result, [
            Element(
                name="alinea",
                contents=[_l("bly bly bly")],
                data=dict(number='1'),
            ),
            Element(
                name="section",
                contents=[
                    Element(
                        name="section_title",
                        contents=[_l("Titre I - Introduction")],
                    ),
                    Element(
                        name="section",
                        contents=[ 
                            Element(
                                name="section_title",
                                contents=[_l("1. Contexte")]
                            ),
                            Element(
                                name="alinea",
                                contents=[_l("bla bla bla")],
                                data=dict(number='1'),
                            ),
                        ]
                    ),
                    Element(
                        name="section",
                        contents=[
                            Element(
                                name="section_title",
                                contents=[_l("2. Objectifs")]
                            ),
                            Element(
                                name="alinea",
                                contents=[_l("blo blo blo")],
                                data=dict(number='1'),
                            ),
                            Element(
                                name="alinea",
                                contents=[_l("bli bli bli")],
                                data=dict(number='2'),
                            ),
                        ]
                    ),
                ]
            ),
            Element(
                name="section",
                contents=[
                    Element(
                        name="section_title",
                        contents=[_l("Titre II - Méthodologie")],
                    ),
                    Element(
                        name="alinea",
                        contents=[_l("blu blu blu")],
                        data=dict(number='1'),
                    ),
                    Element(
                        name="alinea",
                        contents=[_l("ble ble ble")],
                        data=dict(number='2'),
                    ),
                ]
            )

        ])

    def test_parse_sections_contents(self):
        # Arrange
        element_flow = [
            Element(
                name="section_title",
                data=dict(level=0),
                contents=[_l("1. Bla")],
            ),
            _l(
                "bla bla bla"
            ),
            Element(
                name="section_title",
                data=dict(level=1),
                contents=[_l("1.1. Blabla")],
            ),
            _l("bli bli bli"),
        ]

        # Act
        result = list(parse_sections(element_flow, level=0))

        # Assert
        assert_element_flows_equal(result, [
            Element(
                name="section",
                contents=[
                    Element(
                        name="section_title",
                        contents=[
                            _l("1. Bla"),
                        ],
                    ),
                    Element(
                        name="alinea",
                        contents=[_l("bla bla bla")],
                        data=dict(number='1'),
                    ),
                    Element(
                        name="section",
                        contents=[
                            Element(
                                name="section_title",
                                contents=[_l("1.1. Blabla")],
                            ),
                            Element(
                                name="alinea",
                                contents=[_l("bli bli bli")],
                                data=dict(number='1'),
                            ),
                        ]
                    ),
                ]
            ),
        ])

    def test_parse_sections_missing_level(self):
        # Arrange
        element_flow = [
            Element(
                name="section_title",
                data=dict(level=0),
                contents=[
                    _l("1. Bla"),
                ],
            ),
            Element(
                name="section_title",
                data=dict(level=2),
                contents=[
                    _l("1.1.1. Blabla"),
                ],
            ),
        ]

        # Act
        result = list(parse_sections(element_flow, level=0))

        # Assert
        assert_element_flows_equal(result, [
            Element(
                name="section",
                contents=[
                    Element(
                        name="section_title",
                        contents=[_l("1. Bla")],
                    ),
                    Element(
                        name="section",
                        contents=[
                            Element(
                                name="section_title",
                                contents=[_l("1.1.1. Blabla")],
                            ),
                        ]
                    ),
                ]
            ),
        ])

    def test_parse_missing_title_current_level(self):
        # Arrange
        element_flow = [
            Element(
                name="section_title",
                data=dict(level=1),
                contents=[
                    _l("1.1. bla"),
                ],
            ),
            Element(
                name="section_title",
                data=dict(level=2),
                contents=[
                    _l("1.1.1. bla"),
                ],
            ),
            Element(
                name="section_title",
                data=dict(level=1),
                contents=[
                    _l("1.2. bla"),
                ],
            ),
            Element(
                name="section_title",
                data=dict(level=0),
                contents=[
                    _l("2. bla"),
                ],
            ),
            Element(
                name="section_title",
                data=dict(level=1),
                contents=[
                    _l("2.1. bla"),
                ],
            ),
        ]

        # Act
        result = list(parse_sections(element_flow, level=0))

        # Assert
        assert_element_flows_equal(result, [
            Element(
                name="section",
                contents=[
                    Element(
                        name="section_title",
                        contents=[_l("1.1. bla")],
                    ),
                    Element(
                        name="section",
                        contents=[
                            Element(
                                name="section_title",
                                contents=[_l("1.1.1. bla")],
                            ),
                        ]
                    ),
                ]
            ),
            Element(
                name="section",
                contents=[
                    Element(
                        name="section_title",
                        contents=[_l("1.2. bla")],
                    ),
                ]
            ),
            Element(
                name="section",
                contents=[
                    Element(
                        name="section_title",
                        contents=[_l("2. bla")],
                    ),
                    Element(
                        name="section",
                        contents=[
                            Element(
                                name="section_title",
                                contents=[_l("2.1. bla")],
                            ),
                        ]
                    ),
                ]
            ),
        ])


def assert_element_flows_equal(actual: ElementFlow, expected: ElementFlow, path=""): 
    actual = list(actual)
    expected = list(expected)
    assert len(actual) == len(expected), f"[{path}] Expected {len(expected)} elements, got {len(actual)}"
    for i, (a, e) in enumerate(zip(actual, expected)):
        child_path = f'{path}/{i}'
        if is_element(e):
            assert is_element(a, name=e.name), f"[{child_path}] Expected {e}, got {a}"
            # Test data only if defined is test expectations
            if e.data:
                assert a.data == e.data, f"[{child_path}] Expected {e.data}, got {a.data}"
            assert_element_flows_equal(a.contents, e.contents, path=child_path)
        else:
            assert isinstance(a, list), f"[{child_path}] Expected TextSegments, got {a}"
            assert isinstance(e, list)
            assert line_column_to_zero(a) == line_column_to_zero(e), f"[{child_path}] Expected {e}, got {a}"


def line_column_to_zero(lines: TextSegments) -> TextSegments:
    return [TextSegment(contents=t.contents, start=(0,0), end=(0,0)) for t in lines]


def assert_text_segments_equal(actual: TextSegments, expected: TextSegments):
    assert len(actual) == len(expected), f"Expected {len(expected)} segments, got {len(actual)}"

def _l(*raw_lines: str):
    return initialize_lines(list(raw_lines))