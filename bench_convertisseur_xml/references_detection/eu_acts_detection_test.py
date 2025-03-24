import unittest

from bs4 import BeautifulSoup

from .eu_acts_detection import parse_eu_acts_references


class TestParseEuActsReferences(unittest.TestCase):

    def test_domain_before(self):
        assert _parsed_elements('Bla bla de la directive (CE) n° 1013/2006 du 22 juin 2006') == [
            'Bla bla de la ',
            '<a class="dsr-document_reference" data-is_resolvable="false" data-uri="dsr://eu-directive__1013_2006_">directive (CE) n° 1013/2006</a>',
            ' du 22 juin 2006',
        ]

    def test_domain_after(self):
        assert _parsed_elements('VU la directive 2010/75/UE du 24 novembre 2010') == [
            'VU la ',
            '<a class="dsr-document_reference" data-is_resolvable="false" data-uri="dsr://eu-directive__75_2010_">directive 2010/75/UE</a>',
            ' du 24 novembre 2010',
        ]

    def test_domain_after_year_2digits(self):
        assert _parsed_elements('VU la directive 96/75/UE du 24 novembre 1996') == [
            'VU la ',
            '<a class="dsr-document_reference" data-is_resolvable="false" data-uri="dsr://eu-directive__75_1996_">directive 96/75/UE</a>',
            ' du 24 novembre 1996',
        ]

    def test_with_word_europeen(self):
        assert _parsed_elements('VU le règlement européen (CE) n° 1013/2006 du 22 juin 2006') == [
            'VU le ',
            '<a class="dsr-document_reference" data-is_resolvable="false" data-uri="dsr://eu-regulation__1013_2006_">règlement européen (CE) n° 1013/2006</a>',
            ' du 22 juin 2006',
        ]

    def test_parsing_2digit_year(self):
        assert _parsed_elements('Bla bla de la directive (CE) n° 1013/96 du 12 aout 1996') == [
            'Bla bla de la ',
            '<a class="dsr-document_reference" data-is_resolvable="false" data-uri="dsr://eu-directive__1013_1996_">directive (CE) n° 1013/96</a>',
            ' du 12 aout 1996',
        ]

    def test_ignore_if_malformed(self):
        assert _parsed_elements('VU la directive 96/75/POIPOI du 24 novembre 1996') == [
            'VU la directive 96/75/POIPOI du 24 novembre 1996',
        ]



def _parsed_elements(string: str):
    soup = BeautifulSoup(string, features='html.parser')
    elements = parse_eu_acts_references(soup, soup.children)
    return [str(element) for element in elements]