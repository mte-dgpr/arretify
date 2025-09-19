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

from .html_create import make_new_tag


class TestMakeNewTag(unittest.TestCase):

    def setUp(self):
        self.soup = BeautifulSoup("", features="html.parser")

    def test_make_new_tag_from_dynamically_mutated_list_of_children(self):
        """
        When passing an element as `contents` to `make_new_tag`, that element
        is moved to another parent during the call, and that shouldn't affect
        iteration over the original list.
        """
        # Arrange
        soup = BeautifulSoup("<span>bla</span><span>blo</span>", features="html.parser")

        # Act
        elements = []
        for child in soup.contents:
            elements.append(make_new_tag(self.soup, "div", contents=[child]))

        # Assert
        assert len(elements) == 2
        assert str(elements[0]) == "<div><span>bla</span></div>"
        assert str(elements[1]) == "<div><span>blo</span></div>"
