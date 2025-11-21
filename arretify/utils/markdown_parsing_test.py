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

from .markdown_parsing import (
    TABLE_HEADER_SEPARATOR_PATTERN,
    TABLE_LINE_PATTERN,
    is_table_description,
)


class TestTableDetection(unittest.TestCase):

    TABLE_MD_1 = """Blabla blabla blabla.

| Rubrique | Régime (*) | Libellé de la rubrique (activité) | Nature de l'installation | Volume autorisé |
|----------|------------|-----------------------------------|-------------------------|-----------------|
| 2771    | A          | bla | 70 MW |
| 4511.2  | D          | blo | 117 t |

(*) A (Autorisation) - D (Déclaration)

** Some other description

Volume autorisé : blablabla.
"""  # noqa: E501

    def test_table_line_pattern(self):
        # Arrange
        lines = self.TABLE_MD_1.split("\n")

        # Assert
        for line in lines[0:2]:
            assert not bool(TABLE_LINE_PATTERN.match(line))
        for line in lines[2:6]:
            assert bool(TABLE_LINE_PATTERN.match(line))
        for line in lines[6:]:
            assert not bool(TABLE_LINE_PATTERN.match(line))

    def test_table_line_pattern_single_column(self):
        # Arrange
        line = "| Column |"

        # Assert
        assert bool(TABLE_LINE_PATTERN.match(line))

    def test_is_table_description(self):
        # Arrange
        lines = self.TABLE_MD_1.split("\n")
        pile = lines[2:6]

        # Assert
        for line in lines[0:7]:
            assert not is_table_description(line, pile)
        assert is_table_description(lines[7], pile)
        assert not is_table_description(lines[8], pile)
        assert is_table_description(lines[9], pile)
        assert not is_table_description(lines[10], pile)
        assert is_table_description(lines[11], pile)

    def test_table_header_separator_pattern(self):
        # Arrange
        line = "| :--: | :--: | :--: | :--: | :--: | :--: |"

        # Assert
        assert bool(TABLE_HEADER_SEPARATOR_PATTERN.match(line)) is True
