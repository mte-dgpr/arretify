import unittest

from bs4 import BeautifulSoup

from . import html
from .html import make_ul, assign_element_id, is_tag_and_matches


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
            "<ul>" "<li>Existing Item 1</li>" "<li>Existing Item 2</li>" "<li>New Item</li>" "</ul>"
        )


class TestAssignElementId(unittest.TestCase):

    def setUp(self):
        html._ELEMENT_ID_COUNTER = 0

    def test_simple(self):
        # Arrange
        soup = BeautifulSoup("", "html.parser")
        tag = soup.new_tag("div")

        # Act
        assign_element_id(tag)

        # Assert
        assert tag["data-element_id"] == "1"

    def test_already_has_element_id(self):
        # Arrange
        soup = BeautifulSoup("", "html.parser")
        tag = soup.new_tag("div")
        tag["data-element_id"] = "42"

        # Act
        assign_element_id(tag)

        # Assert
        assert tag["data-element_id"] == "42"


class TestIsTagAndMatches(unittest.TestCase):

    def test_has_class(self):
        # Arrange
        soup = BeautifulSoup("", "html.parser")
        tag = soup.new_tag("div")
        tag["class"] = ["test-class"]
        tag["class"].append("other-class")

        # Act
        result = is_tag_and_matches(tag, css_classes_in=["test-class"])

        # Assert
        assert result is True

    def test_does_not_have_class(self):
        # Arrange
        soup = BeautifulSoup("", "html.parser")
        tag = soup.new_tag("div")
        tag["class"] = ["other-class"]
        tag["class"].append("another-class")

        # Act
        result = is_tag_and_matches(tag, css_classes_in=["test-class"])

        # Assert
        assert result is False

    def test_raise_error_with_invalid_class(self):
        # Arrange
        soup = BeautifulSoup("", "html.parser")
        tag = soup.new_tag("div")
        tag["class"] = "my-class my-other-class"

        # Act & Assert
        with self.assertRaises(RuntimeError):
            is_tag_and_matches(tag, css_classes_in=["my-class"])
