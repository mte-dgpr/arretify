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

from .core import PatternProxy
from .merge import merge_matches_with_siblings
from .split import split_string_with_regex


class TestMergeMatchWithSiblingString(unittest.TestCase):

    def test_split_with_matches(self):
        # Arrange
        pattern = PatternProxy(r"\d+")
        string = "abc123def456ghi"

        # Act
        result = list(
            merge_matches_with_siblings(
                split_string_with_regex(
                    pattern,
                    string,
                ),
                "following",
            )
        )

        # Assert
        assert result == ["abc", "123def", "456ghi"]

    def test_split_with_matches_after(self):
        # Arrange
        pattern = PatternProxy(r"\d+")
        string = "abc123def456ghi"

        # Act
        result = list(
            merge_matches_with_siblings(
                split_string_with_regex(
                    pattern,
                    string,
                ),
                "previous",
            )
        )

        # Assert
        assert result == ["abc123", "def456", "ghi"]

    def test_split_with_no_matches(self):
        # Arrange
        pattern = PatternProxy(r"\d+")
        string = "abcdef"

        # Act
        result = list(
            merge_matches_with_siblings(
                split_string_with_regex(
                    pattern,
                    string,
                ),
                "following",
            )
        )

        # Assert
        assert result == ["abcdef"]

    def test_split_with_match_at_start(self):
        # Arrange
        pattern = PatternProxy(r"\d+")
        string = "123abc456"

        # Act
        result = list(
            merge_matches_with_siblings(
                split_string_with_regex(
                    pattern,
                    string,
                ),
                "following",
            )
        )

        # Assert
        assert result == ["123abc", "456"]

    def test_split_with_match_at_end(self):
        # Arrange
        pattern = PatternProxy(r"\d+")
        string = "abc123"

        # Act
        result = list(
            merge_matches_with_siblings(
                split_string_with_regex(
                    pattern,
                    string,
                ),
                "following",
            )
        )

        # Assert
        assert result == ["abc", "123"]
