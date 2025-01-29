import unittest
from datetime import date
from bs4 import BeautifulSoup

from .arretes_references import parse_arretes_references, _parse_arretes_references, _parse_plural_arretes_references


class TestParseArreteReferences(unittest.TestCase):

    def test_arrete_date1(self):
        assert _parsed_elements('Vu l\'arrêté ministériel du 2 février 1998, ') == [
            'Vu l\'',
            '<a class="dsr-arrete_reference" data-authority="ministériel">arrêté ministériel du <time class="dsr-date" datetime="1998-02-02">2 février 1998</time></a>',
            ', '
        ]

    def test_arrete_date1_end_modifiant(self):
        assert _parsed_elements('arrêté ministériel du 23 mai 2016 modifiant relatif aux installations de production de chaleur') == [
            '<a class="dsr-arrete_reference" data-authority="ministériel">arrêté ministériel du <time class="dsr-date" datetime="2016-05-23">23 mai 2016</time> modifiant</a>',
            ' relatif aux installations de production de chaleur'
        ]


class TestParseArretePluralReferences(unittest.TestCase):

    def test_references_plural(self):
        assert _parsed_elements('Les arrêtés préfectoraux n° 5213 du 28 octobre 1988 et n° 1636 du 24/03/95 blabla.') == [
            'Les ', 
            'arrêtés préfectoraux ',
            '<a class="dsr-arrete_reference" data-authority="préfectoral" data-code="5213">n° 5213 du <time class="dsr-date" datetime="1988-10-28">28 octobre 1988</time></a>',
            ' et ',
            '<a class="dsr-arrete_reference" data-authority="préfectoral" data-code="1636">n° 1636 du <time class="dsr-date" datetime="1995-03-24">24/03/95</time></a>',
            ' blabla.'
        ]


class TestParseArreteReferencesAll(unittest.TestCase):

    def test_several_references(self):
        assert _parsed_elements('Bla bla arrêté ministériel du 23 mai 2016 relatif aux installations de production de chaleur et arrêté préfectoral n° 1234-567/01.') == [
            'Bla bla ',
            '<a class="dsr-arrete_reference" data-authority="ministériel">arrêté ministériel du <time class="dsr-date" datetime="2016-05-23">23 mai 2016</time></a>',
            ' relatif aux installations de production de chaleur et ',
            '<a class="dsr-arrete_reference" data-authority="préfectoral" data-code="1234-567/01.">arrêté préfectoral n° 1234-567/01.</a>',
        ]


def _parsed_elements(string: str):
    soup = BeautifulSoup(string, features='html.parser')
    elements = parse_arretes_references(soup, soup.children)
    return [str(element) for element in elements]