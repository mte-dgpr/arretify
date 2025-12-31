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

from .testing import _normalize_html_multiline_str, assert_elements_equal, parse_element


class TestNormalizeHtmlMultilineStr(unittest.TestCase):

    def test_removes_indentation_and_newlines(self):
        # Arrange & Act
        result = _normalize_html_multiline_str(
            """
            <div>
                <span>content</span>
            </div>
            """
        )

        # Assert
        assert len(result.contents) == 1
        assert_elements_equal(result.contents[0], parse_element("<div><span>content</span></div>"))

    def test_handles_multiple_root_elements(self):
        # Arrange & Act
        result = _normalize_html_multiline_str(
            """
            <div>first</div>
            <div>second</div>
            """
        )

        # Assert
        assert len(result.contents) == 2
        assert_elements_equal(result.contents[0], parse_element("<div>first</div>"))
        assert_elements_equal(result.contents[1], parse_element("<div>second</div>"))
