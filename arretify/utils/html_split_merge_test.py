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

from .html_split_merge import pick_string


class TestPickStrings(unittest.TestCase):

    def setUp(self):
        self.soup = BeautifulSoup("", features="html.parser")

    def test_simple(self):
        # Arrange
        elements = [
            "text1",
            self.soup.new_tag("div"),
            "text2",
            "text3",
        ]

        def probe(elements, index):
            return elements[index].startswith("text")

        # Act
        text_segments_probe = pick_string(probe)

        # Assert
        assert text_segments_probe(elements, 0) is True
        # If pick_text_segment not used, this should raise an error
        assert text_segments_probe(elements, 1) is False
        assert text_segments_probe(elements, 2) is True
        assert text_segments_probe(elements, 3) is True
