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
from .functional import flat_map_string, chain_functions


class TestFlatMapString(unittest.TestCase):

    def test_flat_map_string(self):
        # Arrange
        elements = ["hello", 1, "world", 2]

        def map_func(x):
            return [x.upper()]

        # Act
        result = list(flat_map_string(elements, map_func))

        # Assert
        assert result == [
            "HELLO",
            1,
            "WORLD",
            2,
        ], "Should apply the map function to string elements"


class TestChainFunctions(unittest.TestCase):

    def test_chain_functions(self):
        # Arrange
        def add_one(x):
            return x + 1

        def multiply_by_two(x):
            return x * 2

        functions = [add_one, multiply_by_two]

        # Assert
        assert chain_functions(3, functions) == 8
