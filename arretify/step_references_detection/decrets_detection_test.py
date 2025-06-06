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

from arretify.utils.testing import (
    make_testing_function_for_children_list,
    normalized_html_str,
)
from .decrets_detection import parse_decrets_references

process_children = make_testing_function_for_children_list(parse_decrets_references)


class TestParseDecretsReferences(unittest.TestCase):

    def test_simple(self):
        assert process_children("Bla bla décret n°2005-635 du 30 mai 2005 relatif à") == [
            "Bla bla ",
            normalized_html_str(
                """
                <a
                    class="dsr-document_reference"
                    data-is_resolvable="false"
                    data-uri="dsr://decret__2005-635_2005-05-30_"
                >
                    décret n°2005-635 du
                    <time class="dsr-date" datetime="2005-05-30">
                        30 mai 2005
                    </time>
                </a>
                """
            ),
            " relatif à",
        ]
