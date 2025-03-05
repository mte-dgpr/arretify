import unittest

from bs4 import BeautifulSoup

from .html_ranges import find_element_range, _find_next_after, _is_descendant, _is_parent, _collapse_element_range


class TestFindElementRange(unittest.TestCase):
    def test_find_element_range_across_container_tags(self):
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
        element_range = find_element_range(start_tag, lambda element, _: element.name == 'blockquote')

        # Assert
        assert [str(element) for element in element_range] == [
            '<span class="start">blo <b>bold blo</b></span>',
            '<div>bli <i>italic bli</i></div>',
            '<blockquote>blu <u>underline blu</u></blockquote>',
        ]

    def test_find_element_range_interupt(self):
        # Arrange
        html = '''
            <div>
                bla <a>link</a>
                <span class="start">
                    blo <b>bold blo</b>
                </span>
            </div>
        '''
        soup = BeautifulSoup(_clean_html(html), features='html.parser')
        start_tag = soup.find(class_='start')
        assert start_tag is not None

        # Act
        def is_end_element(element, _):
            if element.name == 'a':
                return None
        element_range = find_element_range(start_tag, is_end_element)

        # Assert
        assert element_range is None

    def test_find_element_range_passed_callback(self):
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
        call_params = []
        def is_end_element(element, tmp):
            call_params.append((element, tmp[:]))
            if element.name == 'blockquote':
                return True
            return False
        find_element_range(start_tag, is_end_element)

        # Assert
        assert [(str(element), [str(e) for e in element_range]) for element, element_range in call_params] == [
            (
                '<div><div>bli <i>italic bli</i></div><blockquote>blu <u>underline blu</u></blockquote></div>', 
                [
                    '<span class="start">blo <b>bold blo</b></span>',
                ]
            ),
            (
                '<div>bli <i>italic bli</i></div>', 
                [
                    '<span class="start">blo <b>bold blo</b></span>',
                ]
            ),
            (
                'bli ',
                [
                    '<span class="start">blo <b>bold blo</b></span>',
                ]
            ),
            (
                '<i>italic bli</i>',
                [
                    '<span class="start">blo <b>bold blo</b></span>',
                    'bli '
                ]
            ),
                        (
                'italic bli',
                [
                    '<span class="start">blo <b>bold blo</b></span>',
                    'bli '
                ]
            ),
            (
                '<blockquote>blu <u>underline blu</u></blockquote>',
                [
                    '<span class="start">blo <b>bold blo</b></span>',
                    '<div>bli <i>italic bli</i></div>',
                ]
            ),
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