import unittest
from datetime import date

from .articles import _parse_articles, ArticleReference, ARTICLE_RE


class TestParseDateFunction(unittest.TestCase):

    def test_arrete_date1(self):
        articles, remainder = _parse_articles([ARTICLE_RE], ' prévues à l\'article 74.6 de l\'arrêté ')
        assert articles == [ArticleReference(
            number=[74, 6],
        )]
        assert remainder is None