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

from quality_evaluation.math_utils import compute_average_score


class TestComputeAverageScore(unittest.TestCase):
    def test_compute_average_with_multiple_pairs(self):
        # Arrange
        pairs = [(1, 2), (3, 4), (5, 6)]

        def score_function(a, b):
            return a + b

        # Act
        result = compute_average_score(pairs, score_function)

        # Assert
        # (1+2) + (3+4) + (5+6) = 3 + 7 + 11 = 21, 21/3 = 7.0
        assert result == 7.0

    def test_compute_average_with_empty_list(self):
        # Arrange
        pairs = []

        def score_function(a, b):
            return a + b

        # Act
        result = compute_average_score(pairs, score_function)

        # Assert
        assert result == 0.0
