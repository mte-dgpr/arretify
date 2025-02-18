import re
import unittest
from typing import Pattern, Iterator

from bs4 import BeautifulSoup, Tag

from bench_convertisseur_xml.types import OperationType
from .operations import parse_operations


class TestParseOperations(unittest.TestCase):

    def test_simple(self):
        assert _parsed_elements(
            "sont remplacées par celles définies par le présent arrêté."
        ) == [
            '<span class="dsr-operation" data-keyword="remplacées" data-operation_type="replace">sont <b>remplacées</b></span>',
            ' par celles définies par le présent arrêté.',
        ]

    def test_has_right_operand(self):
        assert _parsed_elements(
            "sont remplacées comme suit :"
        ) == [
            '<span class="dsr-operation" data-has_right_operand="true" data-keyword="remplacées" data-operation_type="replace">sont <b>remplacées</b> comme suit :</span>',
        ]


def _parsed_elements(string: str):
    soup = BeautifulSoup(string, features='html.parser')
    elements = parse_operations(soup, soup.children)
    return [str(element) for element in elements]