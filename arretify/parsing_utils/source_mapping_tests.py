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

from .source_mapping import TextSegment, combine_text_segments


class TestCombinedSegments(unittest.TestCase):
    def test_single_segment(self):
        # Arrange
        combined_contents = "hello"
        segments = [TextSegment(contents="hello", start=0, end=5)]

        # Act
        result = combine_text_segments(combined_contents, segments)

        # Assert
        assert result.contents == "hello"
        assert result.start == 0
        assert result.end == 5

    def test_multiple_segments(self):
        # Arrange
        combined_contents = "hello world"
        segments = [
            TextSegment(contents="hello", start=0, end=5),
            TextSegment(contents="world", start=6, end=11),
        ]

        # Act
        result = combine_text_segments(combined_contents, segments)

        # Assert
        assert result.contents == "hello world"
        assert result.start == 0
        assert result.end == 11

    def test_overlapping_segments(self):
        # Arrange
        combined_contents = "overlap"
        segments = [
            TextSegment(contents="over", start=0, end=4),
            TextSegment(contents="lap", start=4, end=7),
        ]

        # Act
        result = combine_text_segments(combined_contents, segments)

        # Assert
        assert result.contents == "overlap"
        assert result.start == 0
        assert result.end == 7

    def test_non_overlapping_segments(self):
        # Arrange
        combined_contents = "non-overlapping"
        segments = [
            TextSegment(contents="non", start=0, end=3),
            TextSegment(contents="overlapping", start=4, end=15),
        ]

        # Act
        result = combine_text_segments(combined_contents, segments)

        # Assert
        assert result.contents == "non-overlapping"
        assert result.start == 0
        assert result.end == 15
