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
)
from arretify.utils.testing import normalized_html_str
from .operations_detection import parse_operations

process_operations = make_testing_function_for_children_list(parse_operations)


class TestParseOperations(unittest.TestCase):
    def test_simple(self):
        assert process_operations("sont remplacées par celles définies par le présent arrêté.") == [
            normalized_html_str(
                """
                <span
                    class="dsr-operation"
                    data-direction="rtl"
                    data-has_operand="false"
                    data-keyword="remplacées"
                    data-operand=""
                    data-operation_type="replace"
                    data-references=""
                >
                    sont <b>remplacées</b>
                </span>
                """
            ),
            " par celles définies par le présent arrêté.",
        ]

    def test_has_operand(self):
        assert process_operations("sont remplacées comme suit :") == [
            normalized_html_str(
                """
                <span
                    class="dsr-operation"
                    data-direction="rtl"
                    data-has_operand="true"
                    data-keyword="remplacées"
                    data-operand=""
                    data-operation_type="replace"
                    data-references=""
                >
                    sont <b>remplacées</b> comme suit :
                </span>
                """
            ),
        ]

    def test_insert_operation(self):
        assert process_operations("Sont insérés après le") == [
            normalized_html_str(
                """
                <span
                    class="dsr-operation"
                    data-direction="rtl"
                    data-has_operand="true"
                    data-keyword="insérés"
                    data-operand=""
                    data-operation_type="add"
                    data-references=""
                >
                    Sont <b>insérés</b> après le
                </span>
                """
            ),
        ]

    def test_modification_operation(self):
        assert process_operations("susvisé sont ainsi modifiées :") == [
            normalized_html_str(
                """
                <span
                    class="dsr-operation"
                    data-direction="rtl"
                    data-has_operand="true"
                    data-keyword="modifiées"
                    data-operand=""
                    data-operation_type="replace"
                    data-references=""
                >
                    susvisé sont ainsi <b>modifiées</b> :
                </span>
                """
            ),
        ]

    def test_add_completed_as_follows(self):
        assert process_operations("est complété comme suit :") == [
            normalized_html_str(
                """
                <span
                    class="dsr-operation"
                    data-direction="rtl"
                    data-has_operand="true"
                    data-keyword="complété comme suit "
                    data-operand=""
                    data-operation_type="add"
                    data-references=""
                >
                    est <b>complété comme suit</b> :
                </span>
                """
            ),
        ]

    def test_replace_operation(self):
        assert process_operations("Blabla. Il est remplacé par :") == [
            normalized_html_str(
                """
                <span
                    class="dsr-operation"
                    data-direction="rtl"
                    data-has_operand="true"
                    data-keyword="remplacé"
                    data-operand=""
                    data-operation_type="replace"
                    data-references=""
                >
                    Blabla. Il est <b>remplacé</b> par :
                </span>
                """
            ),
        ]
