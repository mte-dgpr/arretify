import unittest
from dataclasses import dataclass
from typing import List

from .source_mapping import TextSegment, combine_text_segments


class TestCombinedSegments(unittest.TestCase):
    def test_single_segment(self):
        # Arrange
        combined_contents = "hello"
        segments = [TextSegment(contents="hello", start=0, end=5)]

        # Act
        result = combine_text_segments(combined_contents, segments)

        # Assert
        result.contents == "hello"
        result.start == 0
        result.end == 5

    def test_multiple_segments(self):
        # Arrange
        combined_contents = "hello world"
        segments = [
            TextSegment(contents="hello", start=0, end=5),
            TextSegment(contents="world", start=6, end=11)
        ]

        # Act
        result = combine_text_segments(combined_contents, segments)

        # Assert
        result.contents == "hello world"
        result.start == 0
        result.end == 11

    def test_overlapping_segments(self):
        # Arrange
        combined_contents = "overlap"
        segments = [
            TextSegment(contents="over", start=0, end=4),
            TextSegment(contents="lap", start=4, end=7)
        ]

        # Act
        result = combine_text_segments(combined_contents, segments)

        # Assert
        result.contents == "overlap"
        result.start == 0
        result.end == 7

    def test_non_overlapping_segments(self):
        # Arrange
        combined_contents = "non-overlapping"
        segments = [
            TextSegment(contents="non", start=0, end=3),
            TextSegment(contents="overlapping", start=4, end=15)
        ]

        # Act
        result = combine_text_segments(combined_contents, segments)

        # Assert
        result.contents == "non-overlapping"
        result.start == 0
        result.end == 15