import unittest

from bs4 import BeautifulSoup

from .self_detection import parse_self_references


class TestParseSelfReferences(unittest.TestCase):

    def test_simple(self):
        assert _parsed_elements('l\'article 8 du présent arrêté remplace') == [
            "l'article 8 du ",
            '<a class="dsr-document_reference" data-is_resolvable="true" data-uri="dsr://self____">présent arrêté</a>',
            ' remplace',
        ]


def _parsed_elements(string: str):
    soup = BeautifulSoup(string, features='html.parser')
    elements = parse_self_references(soup, soup.children)
    return [str(element) for element in elements]