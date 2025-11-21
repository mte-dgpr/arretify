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

from .split_merge import (
    SplitMatch,
    SplitNotAMatch,
    make_single_line_splitter,
    make_while_splitter,
    negate,
    split_and_map_elements,
    split_before_match,
    split_elements,
)


class TestSplitBeforeMatch(unittest.TestCase):

    def test_no_match(self):
        # Arrange
        elements = [
            123,
            "a",
            "b",
            "c",
            456,
        ]

        def is_matching(elements, i):
            return isinstance(elements[i], str) and elements[i] == "d"

        # Act
        before, after = split_before_match(elements, is_matching)

        # Assert
        assert before == elements
        assert after == []

    def test_match_first_line(self):
        # Arrange
        elements = ["match", "b", "c"]

        def is_matching(elements, i):
            return isinstance(elements[i], str) and elements[i] == "match"

        # Act
        before, after = split_before_match(elements, is_matching)

        # Assert
        assert before == []
        assert after == ["match", "b", "c"]

    def test_match_middle_line(self):
        # Arrange
        elements = [
            123,
            "a",
            "match",
            "c",
            True,
            456,
        ]

        def is_matching(elements, i):
            return isinstance(elements[i], str) and elements[i] == "match"

        # Act
        before, after = split_before_match(elements, is_matching)

        # Assert
        assert before == [123, "a"]
        assert after == ["match", "c", True, 456]

    def test_match_last_line(self):
        # Arrange
        elements = ["a", "b", "match"]

        def is_matching(elements, i):
            return isinstance(elements[i], str) and elements[i] == "match"

        # Act
        before, after = split_before_match(elements, is_matching)

        # Assert
        assert before == ["a", "b"]
        assert after == ["match"]


class TestSplitElements(unittest.TestCase):

    def test_no_matches(self):
        # Arrange
        elements = ["a", "b", "c"]

        def splitter(elements):
            return None

        # Act
        result = list(split_elements(elements, splitter))

        # Assert
        assert result == [SplitNotAMatch(elements)]

    def test_all_match_start(self):
        # Arrange
        elements = ["start1", "start2"]

        def splitter(elements):
            return ([], elements, [])

        # Act
        result = list(split_elements(elements, splitter))

        # Assert
        assert result == [SplitMatch(elements)]

    def test_mixed_match(self):
        # Arrange
        elements = ["a", "b", "c", "d", "e", "f", "g"]

        def splitter(elements):
            return (
                (elements[0:1], elements[1:3], elements[3:]) if len(elements) >= 3 else None
            )  # Matches [b, c] and [e, f]

        # Act
        result = list(split_elements(elements, splitter))

        # Assert
        expected = [
            SplitNotAMatch(elements[:1]),  # 'a' does not match
            SplitMatch(elements[1:3]),  # 'b', 'c' matches
            SplitNotAMatch(elements[3:4]),  # 'd' does not match
            SplitMatch(elements[4:6]),  # 'e', 'f' matches
            SplitNotAMatch(elements[6:]),  # 'g' does not match
        ]
        assert result == expected

    def test_contiguous_matching_segments(self):
        # Arrange
        elements = ["start1", "start2", "start3"]

        def splitter(elements):
            return ([], elements[0:1], elements[1:])

        # Act
        result = list(split_elements(elements, splitter))

        # Assert
        expected = [
            SplitMatch(elements[0:1]),
            SplitMatch(elements[1:2]),
            SplitMatch(elements[2:3]),
        ]
        assert result == expected


class TestSplitAndMapElements(unittest.TestCase):

    def test_split_and_map(self):
        # Arrange
        some_numbers = [1, 3, 11, 10, 6, 23]

        def multiple_of_3(elements):
            for i, element in enumerate(elements):
                if element % 3 == 0:
                    return elements[:i], element, elements[i + 1 :]
            return None

        def map_func(n):
            return f"Number {n} is multiple of 3"

        # Act
        result = list(
            split_and_map_elements(
                some_numbers,
                multiple_of_3,
                map_func,
            )
        )
        # Assert
        assert result == [
            1,
            "Number 3 is multiple of 3",
            11,
            10,
            "Number 6 is multiple of 3",
            23,
        ]


class TestMakeSingleLineSplitter(unittest.TestCase):

    def test_match_found(self):
        # Arrange
        splitter = make_single_line_splitter(lambda elements, index: elements[index] == "match")
        elements = ["no match", "match", "no match"]

        # Act
        result = splitter(elements)

        # Assert
        assert result == (elements[:1], elements[1:2], elements[2:])

    def test_match_found_first_line(self):
        # Arrange
        splitter = make_single_line_splitter(lambda elements, index: elements[index] == "match")
        elements = ["match", "no match", "no match"]

        # Act
        result = splitter(elements)

        # Assert
        assert result == (elements[:0], elements[0:1], elements[1:])

    def test_no_match(self):
        # Arrange
        splitter = make_single_line_splitter(lambda elements, index: elements[index] == "match")
        elements = ["no match", "also no match"]

        # Act
        result = splitter(elements)

        # Assert
        assert result is None


class TestMakeWhileSplitter(unittest.TestCase):

    def test_match_found(self):
        # Arrange
        def start_condition(elements, index):
            return elements[index].startswith("match1")

        def while_condition(elements, index):
            return elements[index].startswith("match")

        splitter = make_while_splitter(
            start_condition,
            while_condition,
        )
        elements = ["no match", "match1", "match2", "no match", "match3"]

        # Act
        result = splitter(elements)

        # Assert
        assert result == (elements[:1], elements[1:3], elements[3:])

    def test_match_found_first_line(self):
        # Arrange
        def start_condition(elements, index):
            return elements[index].startswith("match1")

        def while_condition(elements, index):
            return elements[index].startswith("match")

        splitter = make_while_splitter(
            start_condition,
            while_condition,
        )
        elements = ["match1", "match2", "no match", "match3"]

        # Act
        result = splitter(elements)

        # Assert
        assert result == (elements[:0], elements[0:2], elements[2:])

    def test_match_found_last_line(self):
        # Arrange
        def start_condition(elements, index):
            return elements[index].startswith("match1")

        def while_condition(elements, index):
            return elements[index].startswith("match")

        splitter = make_while_splitter(
            start_condition,
            while_condition,
        )
        elements = ["no match", "match1", "match2"]

        # Act
        result = splitter(elements)

        # Assert
        assert result == (elements[:1], elements[1:3], [])

    def test_no_match(self):
        # Arrange
        def start_condition(elements, index):
            return elements[index].startswith("match1")

        def while_condition(elements, index):
            return elements[index].startswith("match")

        splitter = make_while_splitter(
            start_condition,
            while_condition,
        )
        elements = ["no match", "also no match"]

        # Act
        result = splitter(elements)

        # Assert
        assert result is None


class TestMakeNegatedProbe(unittest.TestCase):

    def test_negated_probe(self):
        # Arrange
        probe = negate(lambda elements, index: elements[index].startswith("match"))
        elements = ["no match", "also no match", "match this"]

        # Assert
        assert probe(elements, 0) is True  # "no match"
        assert probe(elements, 1) is True  # "also no match"
        assert probe(elements, 2) is False  # "match this"
