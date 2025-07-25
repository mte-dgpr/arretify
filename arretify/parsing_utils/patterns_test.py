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

from .patterns import is_continuing_sentence


class TestIsContinuingSentencePattern(unittest.TestCase):

    def test_simple_continuing_sentence(self):
        # Arrange
        part1 = "This is a sentence that "
        part2 = "continues here."

        # Act
        result = is_continuing_sentence(part1, part2)

        # Assert
        assert result is True

    def test_non_continuing_sentence(self):
        # Arrange
        part1 = "This is a complete sentence."
        part2 = "This is another sentence."

        # Act
        result = is_continuing_sentence(part1, part2)

        # Assert
        assert result is False

    def test_continuing_sentence_accents_and_punctuation(self):
        # Arrange
        part1 = "Blablabla"
        part2 = "à la la."

        # Act
        result = is_continuing_sentence(part1, part2)

        # Assert
        assert result is True

    def test_non_continuing_sentence_accents_and_punctuation(self):
        # Arrange
        part1 = "Blablabla."
        part2 = "À la la."

        # Act
        result = is_continuing_sentence(part1, part2)

        # Assert
        assert result is False

    def test_non_continuing_sentence_if_not_capital_letter_followed_by_lowercase(self):
        # Arrange
        part1 = "This is a complete sentence "
        part2 = "SOMETHING STRANGE"

        # Act
        result = is_continuing_sentence(part1, part2)

        # Assert
        assert result is False
