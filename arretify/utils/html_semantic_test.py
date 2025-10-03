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

from arretify.types import SemanticTagSchema
from .html_semantic import is_semantic_tag


class TestIsSemanticTag(unittest.TestCase):

    def setUp(self):
        self.soup = BeautifulSoup("", "html.parser")
        self.schema_bla = SemanticTagSchema(
            name="bla",
            tag_name="div",
            data_keys=[],
        )
        self.schema_bli = SemanticTagSchema(
            name="bli",
            tag_name="div",
            data_keys=[],
        )

    def test_any_semantic_tag(self):
        # Arrange
        tag = self.soup.new_tag("div")
        tag["data-schema"] = "arretify-test"

        # Act
        result = is_semantic_tag(tag)

        # Assert
        assert result is True

    def test_is_not_tag(self):
        # Arrange
        not_a_tag = "just a string"

        # Act
        result = is_semantic_tag(not_a_tag)

        # Assert
        assert result is False

    def test_schema_name_in(self):
        # Arrange
        tag = self.soup.new_tag("div")
        tag["data-schema"] = "bla"

        # Act
        result1 = is_semantic_tag(tag, schema_in=[self.schema_bla])
        result2 = is_semantic_tag(tag, schema_in=[self.schema_bli])

        # Assert
        assert result1 is True
        assert result2 is False

    def test_tag_name_in(self):
        # Arrange
        tag = self.soup.new_tag("div")
        tag["data-schema"] = "bla"

        # Act
        result1 = is_semantic_tag(tag, tag_name_in=["div"])
        result2 = is_semantic_tag(tag, tag_name_in=["span"])

        # Assert
        assert result1 is True
        assert result2 is False
