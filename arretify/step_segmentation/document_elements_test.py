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

from .core import Node
from .document_elements import add_page_separators, parse_tables_of_contents
from .testing import _l, assert_elements_equal


class TestAddPageSeparators(unittest.TestCase):

    def test_page_separators_inserted(self):
        # Arrange
        lines = (
            _l(
                "Line 1",
                "Line 2",
                "Line 3",
            )
            + _l(
                "Line 4",
                "Line 5",
                page_index=1,
            )
            + _l(
                "Line 6",
                page_index=2,
            )
        )

        # Act
        result = list(add_page_separators(lines))

        # Assert
        assert_elements_equal(
            result,
            [
                Node(type="page_separator", data=dict(page_index=0), children=[]),
                *_l("Line 1", "Line 2", "Line 3"),
                Node(type="page_separator", data=dict(page_index=1), children=[]),
                *_l("Line 4", "Line 5"),
                Node(type="page_separator", data=dict(page_index=2), children=[]),
                *_l("Line 6"),
            ],
        )


class TestParseTablesOfContents(unittest.TestCase):

    def test_parse_tables_of_contents(self):
        # Arrange
        lines = _l("Line 1", "Sommaire", "bla ..... page 1", "blo ..... page 2", "Line 2")

        # Act
        elements = list(parse_tables_of_contents(lines))

        # Assert
        assert_elements_equal(
            elements,
            [
                *_l("Line 1"),
                Node(
                    type="table_of_contents",
                    data=dict(),
                    children=_l(
                        "Sommaire",
                        "bla ..... page 1",
                        "blo ..... page 2",
                    ),
                ),
                *_l("Line 2"),
            ],
        )
