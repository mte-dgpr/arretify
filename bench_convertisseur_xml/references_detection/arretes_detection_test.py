import unittest
from datetime import date
from bs4 import BeautifulSoup

from .arretes_detection import parse_arretes_references, _parse_arretes_references, _parse_multiple_arretes_references


class TestParseArreteReferences(unittest.TestCase):

    def test_arrete_date1(self):
        assert _parsed_elements('Vu l\'arrêté ministériel du 2 février 1998, ') == [
            'Vu l\'',
            '<a class="dsr-document_reference" data-is_resolvable="false" data-uri="dsr://arrete-ministeriel___1998-02-02_">arrêté ministériel du <time class="dsr-date" datetime="1998-02-02">2 février 1998</time></a>',
            ', '
        ]

    def test_arrete_date1_end_modifiant(self):
        assert _parsed_elements('arrêté ministériel du 23 mai 2016 modifiant relatif aux installations de production de chaleur') == [
            '<a class="dsr-document_reference" data-is_resolvable="false" data-uri="dsr://arrete-ministeriel___2016-05-23_">arrêté ministériel du <time class="dsr-date" datetime="2016-05-23">23 mai 2016</time> modifiant</a>',
            ' relatif aux installations de production de chaleur'
        ]

    def test_arrete_unknown(self):
        assert _parsed_elements('Vu l\'arrêté du 2 février 1998, ') == [
            'Vu l\'',
            '<a class="dsr-document_reference" data-is_resolvable="false" data-uri="dsr://arrete___1998-02-02_">arrêté du <time class="dsr-date" datetime="1998-02-02">2 février 1998</time></a>',
            ', '
        ]


class TestParseArretePluralReferences(unittest.TestCase):

    def test_references_multiple(self):
        assert _parsed_elements('Les arrêtés préfectoraux n° 5213 du 28 octobre 1988 et n° 1636 du 24/03/95 blabla.') == [
            'Les ', 
            'arrêtés préfectoraux ',
            '<a class="dsr-document_reference" data-is_resolvable="false" data-uri="dsr://arrete-prefectoral__5213_1988-10-28_">n° 5213 du <time class="dsr-date" datetime="1988-10-28">28 octobre 1988</time></a>',
            ' et ',
            '<a class="dsr-document_reference" data-is_resolvable="false" data-uri="dsr://arrete-prefectoral__1636_1995-03-24_">n° 1636 du <time class="dsr-date" datetime="1995-03-24">24/03/95</time></a>',
            ' blabla.'
        ]


class TestParseArreteReferencesAll(unittest.TestCase):

    def test_several_references(self):
        assert _parsed_elements('Bla bla arrêté ministériel du 23 mai 2016 relatif aux installations de production de chaleur et arrêté préfectoral n° 1234-567/01.') == [
            'Bla bla ',
            '<a class="dsr-document_reference" data-is_resolvable="false" data-uri="dsr://arrete-ministeriel___2016-05-23_">arrêté ministériel du <time class="dsr-date" datetime="2016-05-23">23 mai 2016</time></a>',
            ' relatif aux installations de production de chaleur et ',
            '<a class="dsr-document_reference" data-is_resolvable="false" data-uri="dsr://arrete-prefectoral__1234-567%2F01.__">arrêté préfectoral n° 1234-567/01.</a>',
        ]


def _parsed_elements(string: str):
    soup = BeautifulSoup(string, features='html.parser')
    elements = parse_arretes_references(soup, soup.children)
    return [str(element) for element in elements]