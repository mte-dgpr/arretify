import unittest
from typing import List, Union

from bs4 import BeautifulSoup, Tag

from .html import make_ul

class TestMakeUl(unittest.TestCase):

    def setUp(self):
        self.soup = BeautifulSoup("", "html.parser")

    def test_make_ul_with_strings(self):
        # Arrange
        elements = ["Item 1", "Item 2", "Item 3"]

        # Act
        ul = make_ul(self.soup, elements)

        # Assert
        assert str(ul) == "<ul><li>Item 1</li><li>Item 2</li><li>Item 3</li></ul>"

    def test_make_ul_with_tags(self):
        # Arrange
        li1 = self.soup.new_tag("li")
        li1.string = "Existing Item 1"
        li2 = self.soup.new_tag("li")
        li2.string = "Existing Item 2"
        elements = [li1, li2, "New Item"]

        # Act
        ul = make_ul(self.soup, elements)

        # Assert
        assert str(ul) == (
            "<ul>"
            "<li>Existing Item 1</li>"
            "<li>Existing Item 2</li>"
            "<li>New Item</li>"
            "</ul>"
        )
