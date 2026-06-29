#
# Copyright (c) 2025 Direction générale de la prévention des risques (DGPR).
#
# This file is part of Arrêtify.
# See https://github.com/mte-dgpr/arretify for further info.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import unittest

from .numbering import ordinal_str_to_int, str_to_levels


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


class TestOrdinalStrToInt(unittest.TestCase):

    def test_no_accent(self):
        # Arrange
        ordinal = "troisieme"

        # Act
        result = ordinal_str_to_int(ordinal)

        # Assert
        assert result == 3

    def test_with_accent(self):
        # Arrange
        ordinal = "treizième"

        # Act
        result = ordinal_str_to_int(ordinal)

        # Assert
        assert result == 13
