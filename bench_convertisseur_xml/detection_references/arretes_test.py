import unittest
from datetime import date

from .arretes import parse_arretes, ArreteReference, ARRETE_DATE1_RE


class TestParseDateFunction(unittest.TestCase):

    def test_arrete_date1(self):
        arretes, remainder = parse_arretes([ARRETE_DATE1_RE], 'Vu l\'arrete ministeriel du 2 fevrier 1998, ')
        assert arretes == [ArreteReference(
            authority='ministeriel',
            date=date(year=1998, month=2, day=2),
            qualifier=None,
            code=None,
        )]
        assert remainder is None