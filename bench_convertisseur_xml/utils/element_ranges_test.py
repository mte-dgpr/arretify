import unittest
from typing import List

from bs4 import Tag

from bench_convertisseur_xml.utils.testing import create_bs, normalized_html_str
from .element_ranges import (
    iter_collapsed_range_right,
    iter_collapsed_range_left,
    _find_next_after,
    _collapse_element_range,
    ElementRange,
    get_contiguous_elements_left,
    get_contiguous_elements_right,
)


class TestIterCollapsedRange(unittest.TestCase):

    def test_right(self):
        # Arrange
        soup = create_bs(
            normalized_html_str(
                """
            <div>
                bla <a>link</a>
                <span class="start">
                    blo <b>bold blo</b>
                </span>
            </div>
            <div>
                <div>
                    bli <i>italic bli</i>
                </div>
                <blockquote>
                    blu <u>underline blu</u>
                </blockquote>
            </div>
        """
            )
        )
        start_tag = soup.find(class_="start")
        assert start_tag is not None

        # Act
        results = []
        for element_range in iter_collapsed_range_right(start_tag):
            results.append(_range_to_str(element_range))
            if (
                element_range
                and isinstance(element_range[-1], Tag)
                and element_range[-1].name == "blockquote"
            ):
                break

        # Assert
        assert results == [
            [
                '<span class="start">blo <b>bold blo</b></span>',
                "<div><div>bli <i>italic bli</i></div>"
                "<blockquote>blu <u>underline blu</u></blockquote></div>",
            ],
            [
                '<span class="start">blo <b>bold blo</b></span>',
                "<div>bli <i>italic bli</i></div>",
            ],
            [
                '<span class="start">blo <b>bold blo</b></span>',
                "bli ",
            ],
            [
                '<span class="start">blo <b>bold blo</b></span>',
                "bli ",
                "<i>italic bli</i>",
            ],
            [
                '<span class="start">blo <b>bold blo</b></span>',
                "bli ",
                "italic bli",
            ],
            [
                '<span class="start">blo <b>bold blo</b></span>',
                "<div>bli <i>italic bli</i></div>",
                "<blockquote>blu <u>underline blu</u></blockquote>",
            ],
        ]

    def test_left(self):
        # Arrange
        soup = create_bs(
            normalized_html_str(
                """
            <div>
                bla <a>link</a>
                <span>
                    blo <b>bold blo</b>
                </span>
            </div>
            <div>
                <div>
                    bli <i>italic bli</i>
                </div>
                <blockquote class="start">
                    blu <u>underline blu</u>
                </blockquote>
            </div>
        """
            )
        )
        start_tag = soup.find(class_="start")
        assert start_tag is not None

        # Act
        results = []
        for element_range in iter_collapsed_range_left(start_tag):
            results.append(_range_to_str(element_range))
            if (
                element_range
                and isinstance(element_range[0], Tag)
                and element_range[0].name == "span"
            ):
                break

        # Assert
        assert results == [
            [
                "italic bli",
                '<blockquote class="start">blu <u>underline blu</u></blockquote>',
            ],
            [
                "<i>italic bli</i>",
                '<blockquote class="start">blu <u>underline blu</u></blockquote>',
            ],
            [
                "bli ",
                "<i>italic bli</i>",
                '<blockquote class="start">blu <u>underline blu</u></blockquote>',
            ],
            [
                "<div>bli <i>italic bli</i></div>",
                '<blockquote class="start">blu <u>underline blu</u></blockquote>',
            ],
            [
                "bold blo",
                "<div>bli <i>italic bli</i></div>",
                '<blockquote class="start">blu <u>underline blu</u></blockquote>',
            ],
            [
                "<b>bold blo</b>",
                "<div>bli <i>italic bli</i></div>",
                '<blockquote class="start">blu <u>underline blu</u></blockquote>',
            ],
            [
                "blo ",
                "<b>bold blo</b>",
                "<div>bli <i>italic bli</i></div>",
                '<blockquote class="start">blu <u>underline blu</u></blockquote>',
            ],
            [
                "<span>blo <b>bold blo</b></span>",
                "<div>bli <i>italic bli</i></div>",
                '<blockquote class="start">blu <u>underline blu</u></blockquote>',
            ],
        ]


class TestFindNextAfter(unittest.TestCase):
    def test_direct_sibling(self):
        # Arrange
        soup = create_bs(
            normalized_html_str(
                """
            <span class="start">
                blo <b>bold blo</b>
            </span>
            <div id="next">
                bli
            </div>
        """
            )
        )
        start_tag = soup.find(class_="start")
        assert start_tag is not None

        # Act
        next_element = _find_next_after(start_tag)

        # Assert
        assert str(next_element) == '<div id="next">bli</div>'

    def test_cross_container(self):
        # Arrange
        soup = create_bs(
            normalized_html_str(
                """
            <div>
                <span class="start">
                    blo <b>bold blo</b>
                </span>
            </div>
            <div id="next">
                <i>bli</i>
            </div>
        """
            )
        )
        start_tag = soup.find(class_="start")
        assert start_tag is not None

        # Act
        next_element = _find_next_after(start_tag)

        # Assert
        assert str(next_element) == '<div id="next"><i>bli</i></div>'

    def test_no_next_element(self):
        # Arrange
        soup = create_bs(
            normalized_html_str(
                """
            <span class="start">
                blo <b>bold blo</b>
            </span>
        """
            )
        )
        start_tag = soup.find(class_="start")
        assert start_tag is not None

        # Act
        next_element = _find_next_after(start_tag)

        # Assert
        assert next_element is None


class TestCollapseElementRange(unittest.TestCase):

    def test_collapse_full(self):
        # Arrange
        soup = create_bs(
            normalized_html_str(
                """
            <div id="el1">
                <div id="el2"></div>
                <div id="el3"></div>
            </div>
            <div id="el4"></div>
            <div id="el5">
                <div id="el6">
                    <div id="el7"></div>
                </div>
            </div>
        """
            )
        )
        all_divs = list(soup.find_all("div"))
        assert [div["id"] for div in all_divs] == [
            "el1",
            "el2",
            "el3",
            "el4",
            "el5",
            "el6",
            "el7",
        ]

        # Act
        collapsed = _collapse_element_range(all_divs)

        # Assert
        assert [div["id"] for div in collapsed] == [
            "el1",
            "el4",
            "el5",
        ]

    def test_should_not_collapse_partial(self):
        # Arrange
        soup = create_bs(
            normalized_html_str(
                """
            <div id="el1">
                <div id="el2"></div>
            </div>
            <div id="el3">
                <div id="el4"></div>
                <div id="el5"></div>
                <div id="el6"></div>
            </div>
        """
            )
        )
        divs = list(soup.find_all(lambda tag: tag["id"] in ["el1", "el2", "el3", "el4", "el5"]))
        assert len(divs) == 5

        # Act
        collapsed = _collapse_element_range(divs)

        # Assert
        assert [div["id"] for div in collapsed] == [
            "el1",
            "el4",
            "el5",
        ]

    def test_should_not_collapse_partial_end_deep(self):
        # Arrange
        soup = create_bs(
            normalized_html_str(
                """
            <div id="el1">
                <div id="el2"></div>
            </div>
            <div id="el3">
                <div id="el4"></div>
                <div id="el5">
                    <div id="el6"></div>
                    <div id="el7"></div>
                </div>
            </div>
        """
            )
        )
        divs = list(
            soup.find_all(lambda tag: tag["id"] in ["el1", "el2", "el3", "el4", "el5", "el6"])
        )
        assert len(divs) == 6

        # Act
        collapsed = _collapse_element_range(divs)

        # Assert
        assert [div["id"] for div in collapsed] == [
            "el1",
            "el4",
            "el6",
        ]

    def test_should_not_collapse_partial_start_deep(self):
        # Arrange
        soup = create_bs(
            normalized_html_str(
                """
            <div id="el1">
                <div id="el2">
                    <div id="el3"></div>
                    <div id="el4"></div>
                </div>
            </div>
            <div id="el5"></div>
        """
            )
        )
        divs = list(soup.find_all(lambda tag: tag["id"] in ["el4", "el5"]))
        assert len(divs) == 2

        # Act
        collapsed = _collapse_element_range(divs)

        # Assert
        assert [div["id"] for div in collapsed] == ["el4", "el5"]

    def test_should_work_if_already_collapsed(self):
        # Arrange
        soup = create_bs(
            normalized_html_str(
                """
            <div id="el1">
                <div id="el2"></div>
            </div>
            <div id="el3">
                <div id="el4"></div>
                <div id="el5"></div>
                <div id="el6"></div>
            </div>
        """
            )
        )
        all_divs = list(soup.find_all("div"))
        assert [div["id"] for div in all_divs] == [
            "el1",
            "el2",
            "el3",
            "el4",
            "el5",
            "el6",
        ]
        already_collapsed = [all_divs[0], all_divs[2]]

        # Act
        collapsed = _collapse_element_range(already_collapsed)

        # Assert
        assert [div["id"] for div in collapsed] == ["el1", "el3"]


class TestGetContiguousElementsLeft(unittest.TestCase):

    def test_simple(self):
        # Arrange
        soup = create_bs(
            normalized_html_str(
                """
            <div>
                <div id="blu"></div>
                <div id="bli">
                    <span id="bla"></span>
                    blo
                </div>
                <div id="start"></div>
            </div>
        """
            )
        )
        start_tag = soup.find(id="start")

        # Act
        contiguous = get_contiguous_elements_left(start_tag)

        # Assert
        assert [str(tag) for tag in contiguous] == [
            '<div id="bli"><span id="bla"></span> blo</div>',
            " blo",
        ]

    def test_no_parent(self):
        # Arrange
        soup = create_bs(
            normalized_html_str(
                """
            <div id="blu"></div>
            <div id="bli">
                <span id="bla"></span>
                blo
            </div>
            <div id="start"></div>
        """
            )
        )
        start_tag = soup.find(id="start")

        # Act
        contiguous = get_contiguous_elements_left(start_tag)

        # Assert
        assert [str(tag) for tag in contiguous] == [
            '<div id="bli"><span id="bla"></span> blo</div>',
            " blo",
        ]


class TestGetContiguousElementsRight(unittest.TestCase):

    def test_simple(self):
        # Arrange
        soup = create_bs(
            normalized_html_str(
                """
            <div id="start"></div>
            <div id="bli">
                <span id="bla">blo</span>
                blu
            </div>
            <div id="ble"></div>
        """
            )
        )
        start_tag = soup.find(id="start")

        # Act
        contiguous = get_contiguous_elements_right(start_tag)

        # Assert
        assert [str(tag) for tag in contiguous] == [
            '<div id="bli"><span id="bla">blo</span> blu</div>',
            '<span id="bla">blo</span>',
            "blo",
        ]


def _range_to_str(element_range: ElementRange) -> List[str]:
    return [str(element) for element in element_range]
