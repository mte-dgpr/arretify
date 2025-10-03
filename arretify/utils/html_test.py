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

from bs4 import BeautifulSoup

from .html import ensure_element_id, is_tag
from arretify.types import IdCounters


class TestAssignElementId(unittest.TestCase):

    def test_simple(self):
        # Arrange
        soup = BeautifulSoup("", "html.parser")
        tag = soup.new_tag("div")
        id_counters = IdCounters()

        # Act
        ensure_element_id(id_counters, tag)

        # Assert
        assert tag["data-element_id"] == "1"

    def test_already_has_element_id(self):
        # Arrange
        soup = BeautifulSoup("", "html.parser")
        tag = soup.new_tag("div")
        id_counters = IdCounters()
        tag["data-element_id"] = "42"

        # Act
        ensure_element_id(id_counters, tag)

        # Assert
        assert tag["data-element_id"] == "42"


class TestIsTagAndMatches(unittest.TestCase):

    def test_tag_name_in(self):
        # Arrange
        soup = BeautifulSoup("", "html.parser")
        tag = soup.new_tag("span")

        # Act
        result1 = is_tag(tag, tag_name_in=["span"])
        result2 = is_tag(tag, tag_name_in=["div"])

        # Assert
        assert result1 is True
        assert result2 is False

    def test_not_a_tag(self):
        # Arrange
        text = "Hello, world!"

        # Act
        result = is_tag(text, tag_name_in=["span"])

        # Assert
        assert result is False
