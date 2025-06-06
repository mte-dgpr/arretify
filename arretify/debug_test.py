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

from .debug import insert_debug_keywords


class TestParseTargetPositionReferences(unittest.TestCase):

    def test_simple(self):
        soup = BeautifulSoup(
            "Premier alinéa et 2ème alinéa du présent article",
            features="html.parser",
        )
        children = insert_debug_keywords(soup, soup.children, "alinéa")
        expected_children = [
            "Premier ",
            '<span class="dsr-debug_keyword" data-query="alinéa">alinéa</span>',
            " et 2ème ",
            '<span class="dsr-debug_keyword" data-query="alinéa">alinéa</span>',
            " du présent article",
        ]
        assert [str(child) for child in children] == expected_children

    def test_with_accent(self):
        soup = BeautifulSoup(
            "Premier alinea du présent article",
            features="html.parser",
        )
        children = insert_debug_keywords(soup, soup.children, "alinéa")
        expected_children = [
            "Premier ",
            '<span class="dsr-debug_keyword" data-query="alinéa">alinea</span>',
            " du présent article",
        ]
        assert [str(child) for child in children] == expected_children
