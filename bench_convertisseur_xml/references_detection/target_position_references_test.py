import unittest
import re
from typing import Dict, List

from bs4 import BeautifulSoup

from .target_position_references import parse_target_position_references


class TestHandleArticleRange(unittest.TestCase):

    def test_article_num(self):
        assert _parsed_elements("article 4.1.b") == ['<a class="dsr-target_position_reference" data-article_start="4.1.b">article 4.1.b</a>']
        assert _parsed_elements("article 8") == ['<a class="dsr-target_position_reference" data-article_start="8">article 8</a>']
        assert _parsed_elements("article 1er") == ['<a class="dsr-target_position_reference" data-article_start="1">article 1er</a>']
        assert _parsed_elements("article 111è") == ['<a class="dsr-target_position_reference" data-article_start="111">article 111è</a>']
        assert _parsed_elements("article 2ème") == ['<a class="dsr-target_position_reference" data-article_start="2">article 2ème</a>']

    def test_code_article(self):
        assert _parsed_elements("article R. 511-9") == ['<a class="dsr-target_position_reference" data-article_start="R. 511-9">article R. 511-9</a>']
        assert _parsed_elements("article D.12") == ['<a class="dsr-target_position_reference" data-article_start="D.12">article D.12</a>']
        assert _parsed_elements("article L181-3") == ['<a class="dsr-target_position_reference" data-article_start="L181-3">article L181-3</a>']

    def test_ordinal(self):
        assert _parsed_elements("article premier") == ['<a class="dsr-target_position_reference" data-article_start="1">article premier</a>']
        assert _parsed_elements("article quatrième") == ['<a class="dsr-target_position_reference" data-article_start="4">article quatrième</a>']

    def test_article_num_range(self):
        assert _parsed_elements("articles 3 à 11") == ['<a class="dsr-target_position_reference" data-article_end="11" data-article_start="3">articles 3 à 11</a>']
        assert _parsed_elements("articles 6.18.1 à 6.18.7") == ['<a class="dsr-target_position_reference" data-article_end="6.18.7" data-article_start="6.18.1">articles 6.18.1 à 6.18.7</a>']
        assert _parsed_elements("articles 6.18.a à 6.18.c") == ['<a class="dsr-target_position_reference" data-article_end="6.18.c" data-article_start="6.18.a">articles 6.18.a à 6.18.c</a>']

    def test_ordinal_range(self):
        assert _parsed_elements("de l'article premier à l'article troisième") == [
            'de l\'',
            '<a class="dsr-target_position_reference" data-article_end="3" data-article_start="1">article premier à l\'article troisième</a>',
        ]
        assert _parsed_elements("des articles second à 10ème") == [
            'des ',
            '<a class="dsr-target_position_reference" data-article_end="10" data-article_start="2">articles second à 10ème</a>',
        ]

    def test_code_article_range(self):
        assert _parsed_elements("de l'article R. 511-9 à l'article D.512") == [
            'de l\'',
            '<a class="dsr-target_position_reference" data-article_end="D.512" data-article_start="R. 511-9">article R. 511-9 à l\'article D.512</a>',
        ]
        assert _parsed_elements("l' article R.543-137 à R.543-151") == [
            'l\' ',
            '<a class="dsr-target_position_reference" data-article_end="R.543-151" data-article_start="R.543-137">article R.543-137 à R.543-151</a>',
        ]


class TestArticlePluralRegex(unittest.TestCase):

    def test_article_num(self):
        assert _parsed_elements('articles 5.1.9, 9.2.1, 10.2.1 et 10.2.5') == [
            '<a class="dsr-target_position_reference" data-article_start="5.1.9">articles 5.1.9</a>',
            ', ',
            '<a class="dsr-target_position_reference" data-article_start="9.2.1">9.2.1</a>',
            ', ',
            '<a class="dsr-target_position_reference" data-article_start="10.2.1">10.2.1</a>',
            ' et ',
            '<a class="dsr-target_position_reference" data-article_start="10.2.5">10.2.5</a>',
        ]

    def test_ordinal(self):
        assert _parsed_elements('articles premier,9.a') == [
            '<a class="dsr-target_position_reference" data-article_start="1">articles premier</a>',
            ',',
            '<a class="dsr-target_position_reference" data-article_start="9.a">9.a</a>',
        ]
        assert _parsed_elements('articles premier et second') == [
            '<a class="dsr-target_position_reference" data-article_start="1">articles premier</a>',
            ' et ',
            '<a class="dsr-target_position_reference" data-article_start="2">second</a>',
        ]

    def test_article_code(self):
        assert _parsed_elements('articles R. 511-9 et L. 111') == [
            '<a class="dsr-target_position_reference" data-article_start="R. 511-9">articles R. 511-9</a>',
            ' et ',
            '<a class="dsr-target_position_reference" data-article_start="L. 111">L. 111</a>',
        ]

    def test_article_range(self):
        assert _parsed_elements('articles R. 512 - 74 et R. 512 39-1 à R.512-39-3') == [
            '<a class="dsr-target_position_reference" data-article_start="R. 512 - 74">articles R. 512 - 74</a>',
            ' et ',
            '<a class="dsr-target_position_reference" data-article_end="R.512-39-3" data-article_start="R. 512 39-1">R. 512 39-1 à R.512-39-3</a>',
        ]

    def test_range_first(self):
        assert _parsed_elements('articles R.541-49 à R.541-64 et R.541-79') == [
            '<a class="dsr-target_position_reference" data-article_end="R.541-64" data-article_start="R.541-49">articles R.541-49 à R.541-64</a>',
            ' et ',
            '<a class="dsr-target_position_reference" data-article_start="R.541-79">R.541-79</a>',
        ]


class TestParseAlineaRegex(unittest.TestCase):

    def test_alinea_num_before(self):
        assert _parsed_elements("2ème alinéa de l'article 1") == [
            '<a class="dsr-target_position_reference" data-alinea_start="2" data-article_start="1">2ème alinéa de l\'article 1</a>'
        ]

    def test_alinea_num_after(self):
        assert _parsed_elements("alinéa 3 de l'article 2") == [
            '<a class="dsr-target_position_reference" data-alinea_start="3" data-article_start="2">alinéa 3 de l\'article 2</a>'
        ]
        assert _parsed_elements("alinéa second de l'article 3") == [
            '<a class="dsr-target_position_reference" data-alinea_start="2" data-article_start="3">alinéa second de l\'article 3</a>'
        ]
        assert _parsed_elements("alinéa neuvième de l'article 4") == [
            '<a class="dsr-target_position_reference" data-alinea_start="9" data-article_start="4">alinéa neuvième de l\'article 4</a>'
        ]

    def test_alinea_symbol(self):
        assert _parsed_elements("5° de l'article 5") == [
            '<a class="dsr-target_position_reference" data-alinea_start="5" data-article_start="5">5° de l\'article 5</a>'
        ]


class TestParseTargetPositionReferences(unittest.TestCase):

    def test_simple_singular(self):
        assert _parsed_elements(
            "2ème alinéa de l'article 4.1.b de l'arrêté 90/IC/035"
        ) == [
            '<a class="dsr-target_position_reference" data-alinea_start="2" data-article_start="4.1.b">2ème alinéa de l\'article 4.1.b</a>',
            ' de l\'arrêté 90/IC/035'
        ]

    def test_singular_range(self):
        assert _parsed_elements(
            'aux dispositions des articles R. 515-60 à R. 515-84 du code'
        ) == [
            'aux dispositions des ',
            '<a class="dsr-target_position_reference" data-article_end="R. 515-84" data-article_start="R. 515-60">articles R. 515-60 à R. 515-84</a>',
            ' du code'
        ]

    def test_plural_articles(self):
        assert _parsed_elements(
            "articles premier, 9 et 10.a"
        ) == [
            '<a class="dsr-target_position_reference" data-article_start="1">articles premier</a>',
            ', ',
            '<a class="dsr-target_position_reference" data-article_start="9">9</a>',
            ' et ',
            '<a class="dsr-target_position_reference" data-article_start="10.a">10.a</a>',
        ]

    def test_plural_articles_with_range(self):
        assert _parsed_elements(
            "articles R. 512 - 74 et R. 512 39-1 à R.512-39-3"
        ) == [
            '<a class="dsr-target_position_reference" data-article_start="R. 512 - 74">articles R. 512 - 74</a>',
            ' et ',
            '<a class="dsr-target_position_reference" data-article_end="R.512-39-3" data-article_start="R. 512 39-1">R. 512 39-1 à R.512-39-3</a>',
        ]

    def test_plural_range_first(self):
        assert _parsed_elements(
            "les dispositions des articles R.541-49 à R.541-64 et R.541-79 du code"
        ) == [
            'les dispositions des ',
            '<a class="dsr-target_position_reference" data-article_end="R.541-64" data-article_start="R.541-49">articles R.541-49 à R.541-64</a>',
            ' et ',
            '<a class="dsr-target_position_reference" data-article_start="R.541-79">R.541-79</a>',
            ' du code'
        ]

    def test_with_alinea(self):
        assert _parsed_elements(
            "du 5° de l'article 4.1.b de l'arrêté 90/IC/035"
        ) == [
            'du ',
            '<a class="dsr-target_position_reference" data-alinea_start="5" data-article_start="4.1.b">5° de l\'article 4.1.b</a>',
            ' de l\'arrêté 90/IC/035'
        ]


def _parsed_elements(string: str):
    soup = BeautifulSoup(string, features='html.parser')
    elements = parse_target_position_references(soup, soup.children)
    return [str(element) for element in elements]