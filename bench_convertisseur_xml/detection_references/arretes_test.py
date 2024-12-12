import unittest
from datetime import date
from bs4 import BeautifulSoup

from .arretes import _parse_arretes, ARRETE_DATE1_RE


class TestParseDateFunction(unittest.TestCase):

    def test_arrete_date1(self):
        soup = BeautifulSoup()
        arretes = _parse_arretes(soup, [ARRETE_DATE1_RE], 'Vu l\'arrêté ministériel du 2 fevrier 1998, ')
        expected_elements = [
            'Vu l\'',
            '<span class="dsr-arrete" data-authority="ministeriel">arrete ministeriel du <time class="dsr-date" datetime="1998-02-02">2 fevrier 1998</time></span>',
            ', ',
        ]
        assert [str(element) for element in arretes] == expected_elements
