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

from .core import (
    split_text_segments,
    make_single_line_splitter,
    make_while_splitter,
    split_before_match,
)
from .testing import _l


class TestSplitBeforeMatch(unittest.TestCase):

    def test_no_match(self):
        # Arrange
        lines = _l("a", "b", "c")

        def is_matching(line):
            return line.contents == "d"

        # Act
        before, after = split_before_match(lines, is_matching)

        # Assert
        assert before == lines
        assert after == []

    def test_match_first_line(self):
        # Arrange
        lines = _l("match", "b", "c")

        def is_matching(line):
            return line.contents == "match"

        # Act
        before, after = split_before_match(lines, is_matching)

        # Assert
        assert before == []
        assert after == lines[0:]

    def test_match_middle_line(self):
        # Arrange
        lines = _l("a", "match", "c")

        def is_matching(line):
            return line.contents == "match"

        # Act
        before, after = split_before_match(lines, is_matching)

        # Assert
        assert before == lines[:1]
        assert after == lines[1:]

    def test_match_last_line(self):
        # Arrange
        lines = _l("a", "b", "match")

        def is_matching(line):
            return line.contents == "match"

        # Act
        before, after = split_before_match(lines, is_matching)

        # Assert
        assert before == lines[:2]
        assert after == lines[2:3]


class TestSplitTextSegments(unittest.TestCase):

    def test_no_matches(self):
        # Arrange
        lines = _l("a", "b", "c")

        def splitter(lines):
            return None

        # Act
        result = list(split_text_segments(lines, splitter))

        # Assert
        assert result == [(False, lines)]

    def test_all_match_start(self):
        # Arrange
        lines = _l("start1", "start2")

        def splitter(lines):
            return ([], lines, [])

        # Act
        result = list(split_text_segments(lines, splitter))

        # Assert
        assert result == [(True, lines)]

    def test_mixed_match(self):
        # Arrange
        lines = _l("a", "b", "c", "d", "e", "f", "g")

        def splitter(lines):
            return (
                (lines[0:1], lines[1:3], lines[3:]) if len(lines) >= 3 else None
            )  # Matches [b, c] and [e, f]

        # Act
        result = list(split_text_segments(lines, splitter))

        # Assert
        expected = [
            (False, lines[:1]),  # 'a' does not match
            (True, lines[1:3]),  # 'b', 'c' matches
            (False, lines[3:4]),  # 'd' does not match
            (True, lines[4:6]),  # 'e', 'f' matches
            (False, lines[6:]),  # 'g' does not match
        ]
        assert result == expected

    def test_contiguous_matching_segments(self):
        # Arrange
        lines = _l("start1", "start2", "start3")

        def splitter(lines):
            return ([], lines[0:1], lines[1:])

        # Act
        result = list(split_text_segments(lines, splitter))

        # Assert
        expected = [
            (True, lines[0:1]),
            (True, lines[1:2]),
            (True, lines[2:3]),
        ]
        assert result == expected


class TestMakeSingleLineMatcher(unittest.TestCase):

    def test_match_found(self):
        # Arrange
        splitter = make_single_line_splitter(lambda line: line.contents == "match")
        lines = _l("no match", "match", "no match")

        # Act
        result = splitter(lines)

        # Assert
        assert result == (lines[:1], lines[1:2], lines[2:])

    def test_match_found_first_line(self):
        # Arrange
        splitter = make_single_line_splitter(lambda line: line.contents == "match")
        lines = _l("match", "no match", "no match")

        # Act
        result = splitter(lines)

        # Assert
        assert result == (lines[:0], lines[0:1], lines[1:])

    def test_no_match(self):
        # Arrange
        splitter = make_single_line_splitter(lambda line: line.contents == "match")
        lines = _l("no match", "also no match")

        # Act
        result = splitter(lines)

        # Assert
        assert result is None


class TestMakeWhileMatcher(unittest.TestCase):

    def test_match_found(self):
        # Arrange
        splitter = make_while_splitter(lambda line: line.contents.startswith("match"))
        lines = _l("no match", "match1", "match2", "no match", "match3")

        # Act
        result = splitter(lines)

        # Assert
        assert result == (lines[:1], lines[1:3], lines[3:])

    def test_match_found_first_line(self):
        # Arrange
        splitter = make_while_splitter(lambda line: line.contents.startswith("match"))
        lines = _l("match1", "match2", "no match", "match3")

        # Act
        result = splitter(lines)

        # Assert
        assert result == (lines[:0], lines[0:2], lines[2:])

    def test_match_found_last_line(self):
        # Arrange
        splitter = make_while_splitter(lambda line: line.contents.startswith("match"))
        lines = _l("no match", "match1", "match2")

        # Act
        result = splitter(lines)

        # Assert
        assert result == (lines[:1], lines[1:3], [])

    def test_no_match(self):
        # Arrange
        splitter = make_while_splitter(lambda line: line.contents.startswith("match"))
        lines = _l("no match", "also no match")

        # Act
        result = splitter(lines)

        # Assert
        assert result is None
