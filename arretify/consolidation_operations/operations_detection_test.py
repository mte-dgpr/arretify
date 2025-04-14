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

    def test_reject_match_when_dot_on_left(self):
        assert process_operations("BlaBla. Elle sont remplacées par autre chose.") == [
            "BlaBla. Elle sont remplacées par autre chose."
        ]
