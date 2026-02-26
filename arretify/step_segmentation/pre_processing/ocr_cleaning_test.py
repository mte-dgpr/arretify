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

from .ocr_cleaning import recompose_words


class TestRecomposeWords(unittest.TestCase):

    def test_recompose_words(self):
        # Arrange
        text = "V U     hello v u  a r r ê t é bla n O T i n F R E N C H"

        expected = "VU     hello vu  arrêté bla n O T i n F R E N C H"

        # Act
        result = recompose_words(text)

        # Assert
        assert result == expected, f"Expected '{expected}', got '{result}'"
