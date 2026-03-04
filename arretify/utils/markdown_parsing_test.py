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

from arretify.utils.testing import BaseTestCaseHtml

from .markdown_parsing import is_table_description, parse_markdown_element


class TestIsTableDescription(BaseTestCaseHtml):

    def test_is_table_description(self):
        # Arrange
        table = self.make_tag(
            "table",
            contents=[
                self.make_tag(
                    "tr",
                    contents=[
                        self.make_tag("th", contents=["Rubrique"]),
                        self.make_tag("th", contents=["Régime (*)"]),
                        self.make_tag("th", contents=["Libellé de la rubrique (activité)"]),
                        self.make_tag("th", contents=["Nature de l'installation"]),
                        self.make_tag("th", contents=["Volume autorisé"]),
                    ],
                ),
            ],
        )

        # Assert

        assert not is_table_description("Some description", table)
        assert is_table_description("** Some other description", table)
        assert is_table_description("(1) Yet another description", table)
        assert is_table_description("(*) A (Autorisation) - D (Déclaration)", table)
        assert is_table_description("Volume autorisé : blablabla.", table)


class TestParseMarkdownElement(unittest.TestCase):

    def test_parse_image(self):
        element = parse_markdown_element("![alt text](image.png)", "img")
        assert element["src"] == "image.png"
        assert element["alt"] == "alt text"

    def test_parse_link(self):
        element = parse_markdown_element("[label](https://example.com)", "a")
        assert element["href"] == "https://example.com"
        assert element.get_text() == "label"
