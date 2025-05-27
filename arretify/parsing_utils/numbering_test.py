import unittest

from .numbering import str_to_levels


class TestLevelList(unittest.TestCase):

    def test_title(self):
        # Arrange
        number = "I"

        # Act
        result = str_to_levels(number)

        # Assert
        assert result == [1]

    def test_simple_number(self):
        # Arrange
        number = "12"

        # Act
        result = str_to_levels(number)

        # Assert
        assert result == [12]

    def test_hierarchical_number(self):
        # Arrange
        number = "1.2.3"

        # Act
        result = str_to_levels(number)

        # Assert
        assert result == [1, 2, 3]

    def test_roman_numerals(self):
        # Arrange
        number = "X.II.IV"

        # Act
        result = str_to_levels(number)

        # Assert
        assert result == [10, 2, 4]

    def test_letter(self):
        # Arrange
        number = "A.B.C"

        # Act
        result = str_to_levels(number)

        # Assert
        assert result == [1, 2, 3]

    def test_first_number(self):
        # Arrange
        number = "1"

        # Act
        result = str_to_levels(number)

        # Assert
        assert result == [1]

    def test_sub_article(self):
        # Arrange
        number = "1.4"

        # Act
        result = str_to_levels(number)

        # Assert
        assert result == [1, 4]
