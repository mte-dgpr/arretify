import unittest
from datetime import date
from bs4 import BeautifulSoup

from .arretes_references import (
    _parse_arretes_references, parse_arretes_references, ARRETE_DATE1_RE,
    ARRETE_PLURAL_RE, ARRETE_BASE_PLURAL_RES, ARRETE_PLURAL_RES_LIST, ET_VIRGULE
)
from bench_convertisseur_xml.utils.regex import without_named_groups


class TestParseArreteReferencesSingleRegex(unittest.TestCase):

    def test_arrete_date1(self):
        soup = BeautifulSoup()
        string = 'Vu l\'arrêté ministériel du 2 février 1998, '
        arretes = _parse_arretes_references(soup, string, ARRETE_DATE1_RE)
        expected_elements = [
            'Vu l\'',
            '<a class="dsr-arrete_reference" data-authority="ministériel">arrêté ministériel du <time class="dsr-date" datetime="1998-02-02">2 février 1998</time></a>',
            ', ',
        ]
        assert [str(element) for element in arretes] == expected_elements

    def test_arrete_date1_end_modifiant(self):
        soup = BeautifulSoup()
        string = 'arrêté ministériel du 23 mai 2016 modifiant relatif aux installations de production de chaleur'
        arretes = _parse_arretes_references(soup, string, ARRETE_DATE1_RE)
        expected_elements = [
            '<a class="dsr-arrete_reference" data-authority="ministériel">arrêté ministériel du <time class="dsr-date" datetime="2016-05-23">23 mai 2016</time> modifiant</a>',
            ' relatif aux installations de production de chaleur',
        ]
        assert [str(element) for element in arretes] == expected_elements


class TestParseArreteReferencesAll(unittest.TestCase):

    def test_several_references(self):
        soup = BeautifulSoup('Bla bla arrêté ministériel du 23 mai 2016 relatif aux installations de production de chaleur et arrêté préfectoral n° 1234-567/01.', features='html.parser')
        arretes = parse_arretes_references(soup, soup.children)
        expected_elements = [
            'Bla bla ',
            '<a class="dsr-arrete_reference" data-authority="ministériel">arrêté ministériel du <time class="dsr-date" datetime="2016-05-23">23 mai 2016</time></a>',
            ' relatif aux installations de production de chaleur et ',
            '<a class="dsr-arrete_reference" data-authority="préfectoral" data-code="1234-567/01.">arrêté préfectoral n° 1234-567/01.</a>',
        ]
        assert [str(element) for element in arretes] == expected_elements

    def test_references_plural(self):
        soup = BeautifulSoup('Les arrêtés préfectoraux n° 5213 du 28 octobre 1988 et n° 1636 du 24/03/95 blabla.', features='html.parser')
        arretes = parse_arretes_references(soup, soup.children)
        expected_elements = [
            'Les ', 
            'arrêtés préfectoraux ',
            '<a class="dsr-arrete_reference" data-authority="préfectoral" data-code="5213">n° 5213 du <time class="dsr-date" datetime="1988-10-28">28 octobre 1988</time></a>',
            ' et ',
            '<a class="dsr-arrete_reference" data-authority="préfectoral" data-code="1636">n° 1636 du <time class="dsr-date" datetime="1995-03-24">24/03/95</time></a>',
            ' blabla.'
        ]
        print([str(element) for element in arretes])
        assert [str(element) for element in arretes] == expected_elements


class TestRegex(unittest.TestCase):

    def test_arrete_plural_re(self):
        match = ARRETE_PLURAL_RE.search('Les arrêtés préfectoraux n° 5213 du 28 octobre 1988 et n° 1636 du 24/03/95 blabla.')
        assert match.group(0) == 'arrêtés préfectoraux n° 5213 du 28 octobre 1988 et n° 1636 du 24/03/95'