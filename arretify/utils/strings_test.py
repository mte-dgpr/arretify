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
import re
import unittest

from .strings import merge_strings, split_on_newlines


class TestMergeStrings(unittest.TestCase):

    def test_simple(self):
        # Arrange
        elements = [
            "abc",
            "def",
            "ghi",
        ]

        # Act
        result = merge_strings(elements)

        # Assert
        assert result == "abcdefghi"

    def test_merge_strings_with_non_string(self):
        # Arrange
        match_mock = re.match(r"dummy", "dummy")
        elements = ["abc", match_mock, "def"]

        # Act
        with self.assertRaises(ValueError):
            merge_strings(elements, strip_other_types=False)

    def test_merge_strings_ignore_others(self):
        # Arrange
        elements = [
            "abc",
            123,
            "def",
        ]

        # Act
        result = merge_strings(elements, strip_other_types=True)
        # Assert
        assert result == "abcdef"


class TestSplitLines(unittest.TestCase):

    def test_simple(self):
        # Arrange
        text = "Line 1\nLine 2\nLine 3"

        # Act
        result = split_on_newlines(text)

        # Assert
        assert result == [
            "Line 1",
            "Line 2",
            "Line 3",
        ]

    def test_empty_last_line(self):
        # Arrange
        text = "Line 1\nLine 2\n"

        # Act
        result = split_on_newlines(text)

        # Assert
        assert result == [
            "Line 1",
            "Line 2",
        ]
