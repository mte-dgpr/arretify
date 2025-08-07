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

from .split import split_at_first_verb


class TestSplitAtFirstVerb(unittest.TestCase):

    def test_simple(self):
        # Arrange
        line = ":"

        # Act
        result = split_at_first_verb(line)

        # Assert
        assert result is None

    def test_title_only(self):
        # Arrange
        line = "Date d'ouverture, durée et modalités :"

        # Act
        result = split_at_first_verb(line)

        # Assert
        assert result is None

    def test_alinea_only(self):
        # Arrange
        line = "L'enquête se déroulera pendant 33 jours."

        # Act
        result = split_at_first_verb(line)

        # Assert
        assert result[0] == ""
        assert result[1] == "L'enquête se déroulera pendant 33 jours."

    def test_title_and_alinea(self):
        # Arrange
        line = "Date d'ouverture, durée et modalités : L'enquête se déroulera pendant 33 jours."

        # Act
        result = split_at_first_verb(line)

        # Assert
        assert result[0] == "Date d'ouverture, durée et modalités :"
        assert result[1] == "L'enquête se déroulera pendant 33 jours."

    def test_title_and_alinea_colon(self):
        # Arrange
        line = "Les itinéraires suivants sont interdits :"

        # Act
        result = split_at_first_verb(line)

        # Assert
        assert result[0] == ""
        assert result[1] == "Les itinéraires suivants sont interdits :"

    def test_title_and_alinea_colon_both(self):
        # Arrange
        line = "Date d'ouverture, durée et modalités : Les itinéraires suivants sont interdits :"

        # Act
        result = split_at_first_verb(line)

        # Assert
        assert result[0] == "Date d'ouverture, durée et modalités :"
        assert result[1] == "Les itinéraires suivants sont interdits :"
