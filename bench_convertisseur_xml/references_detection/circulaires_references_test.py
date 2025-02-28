import unittest

from bs4 import BeautifulSoup

from .circulaires_references import parse_circulaires_references


class TestParseDecretsReferences(unittest.TestCase):

    def test_only_date(self):
        assert _parsed_elements('Bla bla circulaire du 30 mai 2005 relative à') == [
            'Bla bla ',
            '<a class="dsr-document_reference" data-uri="circulaire://2005-05-30_">circulaire du <time class="dsr-date" datetime="2005-05-30">30 mai 2005</time></a>',
            ' relative à',
        ]

    def test_with_ministerielle(self):
        assert _parsed_elements('Bla bla circulaire ministérielle du 30 mai 2005 relative à') == [
            'Bla bla ',
            '<a class="dsr-document_reference" data-uri="circulaire://2005-05-30_">circulaire ministérielle du <time class="dsr-date" datetime="2005-05-30">30 mai 2005</time></a>',
            ' relative à',
        ]

    def test_with_random_acronym(self):
        assert _parsed_elements('Bla bla circulaire DPPR/DE du 30 mai 2005 relative à') == [
            'Bla bla ',
            '<a class="dsr-document_reference" data-uri="circulaire://2005-05-30_">circulaire DPPR/DE du <time class="dsr-date" datetime="2005-05-30">30 mai 2005</time></a>',
            ' relative à',
        ]

    def test_with_identifier_and_date(self):
        assert _parsed_elements('Bla bla circulaire n°2005-12 du 30 mai 2005 relative à') == [
            'Bla bla ',
            '<a class="dsr-document_reference" data-uri="circulaire://2005-05-30_2005-12">circulaire n°2005-12 du <time class="dsr-date" datetime="2005-05-30">30 mai 2005</time></a>',
            ' relative à',
        ]


def _parsed_elements(string: str):
    soup = BeautifulSoup(string, features='html.parser')
    elements = parse_circulaires_references(soup, soup.children)
    return [str(element) for element in elements]