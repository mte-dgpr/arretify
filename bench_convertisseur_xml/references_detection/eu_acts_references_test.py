import unittest

from bs4 import BeautifulSoup

from .eu_acts_references import parse_eu_acts_references


class TestParseEuActsReferences(unittest.TestCase):

    def test_domain_before(self):
        assert _parsed_elements('Bla bla de la directive (CE) n° 1013/2006 du 22 juin 2006') == [
            'Bla bla de la ',
            '<a class="dsr-document_reference" data-is_resolvable="false" data-uri="dsr://eu-directive__1013%2F2006__">directive (CE) n° 1013/2006</a>',
            ' du 22 juin 2006',
        ]

    def test_domain_after(self):
        assert _parsed_elements('VU la directive 2010/75/UE du 24 novembre 2010') == [
            'VU la ',
            '<a class="dsr-document_reference" data-is_resolvable="false" data-uri="dsr://eu-directive__2010%2F75__">directive 2010/75/UE</a>',
            ' du 24 novembre 2010',
        ]

    def test_with_word_europeen(self):
        assert _parsed_elements('VU le règlement européen (CE) n° 1013/2006 du 22 juin 2006') == [
            'VU le ',
            '<a class="dsr-document_reference" data-is_resolvable="false" data-uri="dsr://eu-regulation__1013%2F2006__">règlement européen (CE) n° 1013/2006</a>',
            ' du 22 juin 2006',
        ]


def _parsed_elements(string: str):
    soup = BeautifulSoup(string, features='html.parser')
    elements = parse_eu_acts_references(soup, soup.children)
    return [str(element) for element in elements]