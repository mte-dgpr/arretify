import unittest
from datetime import date
from bs4 import BeautifulSoup

from .arretes_references import _parse_arretes_references, ARRETE_DATE1_RE


class TestParseDateFunction(unittest.TestCase):

    def test_arrete_date1(self):
        soup = BeautifulSoup('Vu l\'arrêté ministériel du 2 février 1998, ', features="html.parser")
        arretes = _parse_arretes_references(soup, list(soup.children), ARRETE_DATE1_RE)
        expected_elements = [
            'Vu l\'',
            '<a class="dsr-arrete_reference" data-authority="ministériel">arrêté ministériel du <time class="dsr-date" datetime="1998-02-02">2 février 1998</time></a>',
            ', ',
        ]
        assert [str(element) for element in arretes] == expected_elements
