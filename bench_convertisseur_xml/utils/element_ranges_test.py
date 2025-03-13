import unittest
from typing import List

from bs4 import BeautifulSoup, Tag

from .element_ranges import iter_collapsed_range_right, iter_collapsed_range_left, _find_next_after, _is_descendant, _is_parent, _collapse_element_range, ElementRange


class TestIterCollapsedRange(unittest.TestCase):

    def test_right(self):
        # Arrange
        html = '''
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
        '''
        soup = BeautifulSoup(_clean_html(html), features='html.parser')
        start_tag = soup.find(class_='start')
        assert start_tag is not None

        # Act
        results = []
        for element_range in iter_collapsed_range_right(start_tag):
            results.append(_range_to_str(element_range))
            if (
                element_range 
                and isinstance(element_range[-1], Tag) 
                and element_range[-1].name == 'blockquote'
            ):
                break

        # Assert
        assert results == [
            [
                '<span class="start">blo <b>bold blo</b></span>',
                '<div><div>bli <i>italic bli</i></div><blockquote>blu <u>underline blu</u></blockquote></div>', 
            ],
            [
                '<span class="start">blo <b>bold blo</b></span>',
                '<div>bli <i>italic bli</i></div>', 
            ],
            [
                '<span class="start">blo <b>bold blo</b></span>',
                'bli ',
            ],
            [
                '<span class="start">blo <b>bold blo</b></span>',
                'bli ',
                '<i>italic bli</i>',
            ],
            [
                '<span class="start">blo <b>bold blo</b></span>',
                'bli ',
                'italic bli',
            ],
            [
                '<span class="start">blo <b>bold blo</b></span>',
                '<div>bli <i>italic bli</i></div>',
                '<blockquote>blu <u>underline blu</u></blockquote>',
            ],
        ]

    def test_left(self):
        # Arrange
        html = '''
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
        '''
        soup = BeautifulSoup(_clean_html(html), features='html.parser')
        start_tag = soup.find(class_='start')
        assert start_tag is not None

        # Act
        results = []
        for element_range in iter_collapsed_range_left(start_tag):
            results.append(_range_to_str(element_range))
            if (
                element_range 
                and isinstance(element_range[0], Tag) 
                and element_range[0].name == 'span'
            ):
                break

        # Assert
        assert results == [
            [
                'italic bli',
                '<blockquote class="start">blu <u>underline blu</u></blockquote>',
            ],
            [
                '<i>italic bli</i>',
                '<blockquote class="start">blu <u>underline blu</u></blockquote>',
            ],
            [
                'bli ',
                '<i>italic bli</i>',
                '<blockquote class="start">blu <u>underline blu</u></blockquote>',
            ],
            [
                '<div>bli <i>italic bli</i></div>',
                '<blockquote class="start">blu <u>underline blu</u></blockquote>',
            ],
            [
                'bold blo',
                '<div>bli <i>italic bli</i></div>',
                '<blockquote class="start">blu <u>underline blu</u></blockquote>',
            ],
            [
                '<b>bold blo</b>',
                '<div>bli <i>italic bli</i></div>',
                '<blockquote class="start">blu <u>underline blu</u></blockquote>',
            ],
            [
                'blo ',
                '<b>bold blo</b>',
                '<div>bli <i>italic bli</i></div>',
                '<blockquote class="start">blu <u>underline blu</u></blockquote>',
            ],
            [
                '<span>blo <b>bold blo</b></span>',
                '<div>bli <i>italic bli</i></div>',
                '<blockquote class="start">blu <u>underline blu</u></blockquote>',
            ]
        ]
                


class TestIsDescendant(unittest.TestCase):

    def test_is_descendant(self):
        # Arrange
        html = '''
            <div>
                bla <a>link</a>
                <span class="parent">
                    blo <b class="child">bold blo</b>
                </span>
            </div>
        '''
        soup = BeautifulSoup(_clean_html(html), features='html.parser')
        parent_tag = soup.find(class_='parent')
        child_tag = soup.find(class_='child')
        assert parent_tag is not None
        assert child_tag is not None

        # Assert
        assert _is_descendant(child_tag, parent_tag) is True

    def test_is_not_descendant(self):
        # Arrange
        html = '''
            <div>
                bla <a class="other">link</a>
                <span class="parent">
                    blo <b>bold blo</b>
                </span>
            </div>
        '''
        soup = BeautifulSoup(_clean_html(html), features='html.parser')
        parent_tag = soup.find(class_='parent')
        other_tag = soup.find(class_='other')
        assert parent_tag is not None
        assert other_tag is not None

        # Assert
        assert _is_descendant(parent_tag.find('b'), parent_tag.find('a')) is False


class TestIsParent(unittest.TestCase):

    def test_is_parent(self):
        # Arrange
        html = '''
            <div>
                bla <a>link</a>
                <span class="parent">
                    blo <b class="child">bold blo</b>
                </span>
            </div>
        '''
        soup = BeautifulSoup(_clean_html(html), features='html.parser')
        parent_tag = soup.find(class_='parent')
        child_tag = soup.find(class_='child')
        assert parent_tag is not None
        assert child_tag is not None

        # Assert
        assert _is_parent(parent_tag, child_tag) is True

    def test_is_not_parent(self):
        # Arrange
        html = '''
            <div>
                bla <a class="other">link</a>
                <span class="parent">
                    blo <b>bold blo</b>
                </span>
            </div>
        '''
        soup = BeautifulSoup(_clean_html(html), features='html.parser')
        parent_tag = soup.find(class_='parent')
        other_tag = soup.find(class_='other')
        assert parent_tag is not None
        assert other_tag is not None

        # Assert
        assert _is_parent(other_tag, parent_tag) is False


class TestFindNextAfter(unittest.TestCase):
    def test_direct_sibling(self):
        # Arrange
        html = '''
            <span class="start">
                blo <b>bold blo</b>
            </span>
            <div id="next">
                bli
            </div>
        '''
        soup = BeautifulSoup(_clean_html(html), features='html.parser')
        start_tag = soup.find(class_='start')
        assert start_tag is not None

        # Act
        next_element = _find_next_after(start_tag)

        # Assert
        assert str(next_element) == '<div id="next">bli</div>'

    def test_cross_container(self):
        # Arrange
        html = '''
            <div>
                <span class="start">
                    blo <b>bold blo</b>
                </span>
            </div>
            <div id="next">
                <i>bli</i>
            </div>
        '''
        soup = BeautifulSoup(_clean_html(html), features='html.parser')
        start_tag = soup.find(class_='start')
        assert start_tag is not None

        # Act
        next_element = _find_next_after(start_tag)

        # Assert
        assert str(next_element) == '<div id="next"><i>bli</i></div>'

    def test_no_next_element(self):
        # Arrange
        html = '''
            <span class="start">
                blo <b>bold blo</b>
            </span>
        '''
        soup = BeautifulSoup(_clean_html(html), features='html.parser')
        start_tag = soup.find(class_='start')
        assert start_tag is not None

        # Act
        next_element = _find_next_after(start_tag)

        # Assert
        assert next_element is None


class TestCollapseElementRange(unittest.TestCase):

    def test_collapse_full(self):
        # Arrange
        html = '''
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
        '''
        soup = BeautifulSoup(_clean_html(html), features='html.parser')
        all_divs = list(soup.find_all('div'))
        assert [div['id'] for div in all_divs] == ['el1', 'el2', 'el3', 'el4', 'el5', 'el6', 'el7']

        # Act
        collapsed = _collapse_element_range(all_divs)

        # Assert
        assert [div['id'] for div in collapsed] == ['el1', 'el4', 'el5']

    def test_should_not_collapse_partial(self):
        # Arrange
        html = '''
            <div id="el1">
                <div id="el2"></div>
            </div>
            <div id="el3">
                <div id="el4"></div>
                <div id="el5"></div>
                <div id="el6"></div>
            </div>
        '''
        soup = BeautifulSoup(_clean_html(html), features='html.parser')
        divs = list(soup.find_all(lambda tag: tag['id'] in ['el1', 'el2', 'el3', 'el4', 'el5']))
        assert len(divs) == 5

        # Act
        collapsed = _collapse_element_range(divs)

        # Assert
        assert [div['id'] for div in collapsed] == ['el1', 'el4', 'el5']


    def test_should_not_collapse_partial_end_deep(self):
        # Arrange
        html = '''
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
        '''
        soup = BeautifulSoup(_clean_html(html), features='html.parser')
        divs = list(soup.find_all(lambda tag: tag['id'] in ['el1', 'el2', 'el3', 'el4', 'el5', 'el6']))
        assert len(divs) == 6

        # Act
        collapsed = _collapse_element_range(divs)

        # Assert
        assert [div['id'] for div in collapsed] == ['el1', 'el4', 'el6']

    def test_should_not_collapse_partial_start_deep(self):
        # Arrange
        html = '''
            <div id="el1">
                <div id="el2">
                    <div id="el3"></div>
                    <div id="el4"></div>
                </div>
            </div>
            <div id="el5"></div>
        '''
        soup = BeautifulSoup(_clean_html(html), features='html.parser')
        divs = list(soup.find_all(lambda tag: tag['id'] in ['el4', 'el5']))
        assert len(divs) == 2

        # Act
        collapsed = _collapse_element_range(divs)

        # Assert
        assert [div['id'] for div in collapsed] == ['el4', 'el5']


    def test_should_work_if_already_collapsed(self):
        # Arrange
        html = '''
            <div id="el1">
                <div id="el2"></div>
            </div>
            <div id="el3">
                <div id="el4"></div>
                <div id="el5"></div>
                <div id="el6"></div>
            </div>
        '''
        soup = BeautifulSoup(_clean_html(html), features='html.parser')
        all_divs = list(soup.find_all('div'))
        assert [div['id'] for div in all_divs] == ['el1', 'el2', 'el3', 'el4', 'el5', 'el6']
        already_collapsed = [all_divs[0], all_divs[2]]

        # Act
        collapsed = _collapse_element_range(already_collapsed)

        # Assert
        assert [div['id'] for div in collapsed] == ['el1', 'el3']


def _clean_html(html: str) -> str:
    return html.replace('\n', '').replace('    ', '')


def _range_to_str(element_range: ElementRange) -> List[str]:
    return [str(element) for element in element_range]