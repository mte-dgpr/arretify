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

from arretify.types import TextSegment
from .source_mapping import initialize_pages


class TestInitializePages(unittest.TestCase):
    def test_initialize_pages(self):
        # Arrange
        pages = [("Line 1\n" "Line 2\n" "Line 3"), ("Line A\n" "Line AA\n" "Line AAA")]

        # Act
        lines = initialize_pages(pages)

        # Assert
        assert lines == [
            TextSegment(contents="Line 1", start=(0, 0, 0), end=(0, 0, 6)),
            TextSegment(contents="Line 2", start=(0, 1, 0), end=(0, 1, 6)),
            TextSegment(contents="Line 3", start=(0, 2, 0), end=(0, 2, 6)),
            TextSegment(contents="Line A", start=(1, 0, 0), end=(1, 0, 6)),
            TextSegment(contents="Line AA", start=(1, 1, 0), end=(1, 1, 7)),
            TextSegment(contents="Line AAA", start=(1, 2, 0), end=(1, 2, 8)),
        ]
