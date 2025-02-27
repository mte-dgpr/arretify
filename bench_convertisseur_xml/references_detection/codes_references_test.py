import unittest

from bs4 import BeautifulSoup

from .codes_references import parse_codes_references


class TestParseCodesReferences(unittest.TestCase):

    def test_simple(self):
        assert _parsed_elements('Bla bla code de l’environnement') == [
            'Bla bla ',
            '<a class="dsr-document_reference" data-uri="code://Code%20de%20l%27environnement">code de l’environnement</a>',
        ]


def _parsed_elements(string: str):
    soup = BeautifulSoup(string, features='html.parser')
    elements = parse_codes_references(soup, soup.children)
    return [str(element) for element in elements]