import unittest
from .functional import flat_map_non_string, flat_map_string


class TestFlatMapNonString(unittest.TestCase):

    def test_flat_map_non_string(self):
        # Arrange
        elements = ["hello", 1, "world", 2]
        def map_func(x):
            return [x * 10]

        # Act
        result = list(flat_map_non_string(elements, map_func))

        # Assert
        assert result == ["hello", 10, "world", 20], "Should apply the map function to non-string elements"


class TestFlatMapString(unittest.TestCase):

    def test_flat_map_string(self):
        # Arrange
        elements = ["hello", 1, "world", 2]
        def map_func(x):
            return [x.upper()]

        # Act
        result = list(flat_map_string(elements, map_func))

        # Assert
        assert result == ["HELLO", 1, "WORLD", 2], "Should apply the map function to string elements"