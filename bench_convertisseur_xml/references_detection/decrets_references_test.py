import unittest

from bs4 import BeautifulSoup

from .decrets_references import parse_decrets_references


class TestParseDecretsReferences(unittest.TestCase):

    def test_simple(self):
        assert _parsed_elements('Bla bla décret n°2005-635 du 30 mai 2005 relatif à') == [
            'Bla bla ',
            '<a class="dsr-document_reference" data-uri="decret://2005-05-30_2005-635">décret n°2005-635 du <time class="dsr-date" datetime="2005-05-30">30 mai 2005</time></a>',
            ' relatif à',
        ]


def _parsed_elements(string: str):
    soup = BeautifulSoup(string, features='html.parser')
    elements = parse_decrets_references(soup, soup.children)
    return [str(element) for element in elements]