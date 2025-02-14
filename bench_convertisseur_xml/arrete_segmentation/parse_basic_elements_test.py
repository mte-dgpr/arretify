import re
import unittest

from bs4 import BeautifulSoup

from .parse_basic_elements import list_indentation, parse_list, parse_table, parse_blockquote
from bench_convertisseur_xml.parsing_utils.source_mapping import initialize_lines

class TestParseTable(unittest.TestCase):

    def setUp(self):
        self.soup = BeautifulSoup("", "html.parser")

    def test_simple_table(self):
        # Arrange
        lines = initialize_lines([
            '| Polluant | Concentration maximale en mg/l |',
            '|---------|---------------------------------|',
            '| MES     | 35                               |',
            '| DCO     | 125                              |',
            '| Hydrocarbures totaux | 10                             |',
            "END",
        ])

        # Act
        remaining_lines, elements = parse_table(self.soup, lines)

        # Assert
        assert [line.contents for line in remaining_lines] == ["END"]
        assert [str(element) for element in elements] == [(
            '<table>\n'
            '<thead>\n'
            '<tr>\n'
            '<th>Polluant</th>\n'
            '<th>Concentration maximale en mg/l</th>\n'
            '</tr>\n'
            '</thead>\n'
            '<tbody>\n'
            '<tr>\n'
            '<td>MES</td>\n'
            '<td>35</td>\n'
            '</tr>\n'
            '<tr>\n'
            '<td>DCO</td>\n'
            '<td>125</td>\n'
            '</tr>\n'
            '<tr>\n'
            '<td>Hydrocarbures totaux</td>\n'
            '<td>10</td>\n'
            '</tr>\n'
            '</tbody>\n'
            '</table>'
        )]


class TestParseList(unittest.TestCase):

    def setUp(self):
        self.soup = BeautifulSoup("", "html.parser")

    def test_simple_list(self):
        # Arrange
        lines = initialize_lines(["- Item 1", "- Item 2", "- Item 3", "END"])

        # Act
        remaining_lines, ul = parse_list(self.soup, lines)

        # Assert
        assert [line.contents for line in remaining_lines] == ["END"]
        assert str(ul) == "<ul><li>Item 1</li><li>Item 2</li><li>Item 3</li></ul>"

    def test_nested_list(self):
        # Arrange
        lines = initialize_lines(["- Item 1", "  - Subitem 1.1", "  - Subitem 1.2", "- Item 2"])

        # Act
        remaining_lines, ul = parse_list(self.soup, lines)

        # Assert
        assert remaining_lines == [], "All lines should be parsed into the list"
        assert str(ul) == (
            "<ul>"
            "<li>Item 1"
            "<ul><li>Subitem 1.1</li><li>Subitem 1.2</li></ul>"
            "</li>"
            "<li>Item 2</li>"
            "</ul>"
        )


class TestListIndentation(unittest.TestCase):

    def test_correct_indentation(self):
        # Arrange
        line = "    - Item in list"

        # Act
        result = list_indentation(line)

        # Assert
        assert result == 4, "Should return the correct indentation level"

    def test_no_indentation(self):
        # Arrange
        line = "- Item in list"

        # Act
        result = list_indentation(line)

        # Assert
        assert result == 0, "Should return zero for no indentation"

    def test_not_a_list_element(self):
        # Arrange
        line = "This is not a list item"

        # Act / Assert
        with self.assertRaises(ValueError) as context:
            list_indentation(line)
        assert str(context.exception) == "Expected line to be a list element", "Should raise ValueError for non-list lines"


class TestParseBlockQuote(unittest.TestCase):

    def setUp(self):
        self.soup = BeautifulSoup("", "html.parser")

    def test_blockquote_nested(self):
        # Arrange
        lines = initialize_lines([
            '"bla bla',
            'blo blo :',
            '- Item 1',
            '- Item 2',
            'bli bli"',
            "END",
        ])

        # Act
        remaining_lines, blockquote = parse_blockquote(self.soup, lines)

        # Assert
        assert [line.contents for line in remaining_lines] == ["END"]
        assert str(blockquote) == (
            '<blockquote>'
            '<p>bla bla</p>'
            '<p>blo blo :</p>'
            "<ul><li>Item 1</li><li>Item 2</li></ul>"
            '<p>bli bli</p>'
            '</blockquote>'
        )
