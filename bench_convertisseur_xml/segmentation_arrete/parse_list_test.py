import re
import unittest

from bs4 import BeautifulSoup

from .parse_list import list_indentation, parse_list


class TestParseList(unittest.TestCase):

    def setUp(self):
        self.soup = BeautifulSoup("", "html.parser")

    def test_simple_list(self):
        # Arrange
        lines = ["- Item 1", "- Item 2", "- Item 3", "END"]

        # Act
        remaining_lines, ul = parse_list(self.soup, lines)

        # Assert
        assert remaining_lines == ["END"]
        assert str(ul) == "<ul><li>Item 1</li><li>Item 2</li><li>Item 3</li></ul>"

    def test_nested_list(self):
        # Arrange
        lines = ["- Item 1", "  - Subitem 1.1", "  - Subitem 1.2", "- Item 2"]

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
