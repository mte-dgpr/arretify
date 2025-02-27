import unittest
import re
from typing import Dict, List

from bs4 import BeautifulSoup

from .section_references import parse_section_references


class TestHandleArticleRange(unittest.TestCase):

    def test_article_num(self):
        assert _parsed_elements("article 4.1.b") == ['<a class="dsr-section_reference" data-uri="unknown://unknown/article_4.1.b_">article 4.1.b</a>']
        assert _parsed_elements("article 8") == ['<a class="dsr-section_reference" data-uri="unknown://unknown/article_8_">article 8</a>']
        assert _parsed_elements("article 1er") == ['<a class="dsr-section_reference" data-uri="unknown://unknown/article_1_">article 1er</a>']
        assert _parsed_elements("article 111è") == ['<a class="dsr-section_reference" data-uri="unknown://unknown/article_111_">article 111è</a>']
        assert _parsed_elements("article 2ème") == ['<a class="dsr-section_reference" data-uri="unknown://unknown/article_2_">article 2ème</a>']

    def test_code_article(self):
        assert _parsed_elements("article R. 511-9") == ['<a class="dsr-section_reference" data-uri="unknown://unknown/article_R.%20511-9_">article R. 511-9</a>']
        assert _parsed_elements("article D.12") == ['<a class="dsr-section_reference" data-uri="unknown://unknown/article_D.12_">article D.12</a>']
        assert _parsed_elements("article L181-3") == ['<a class="dsr-section_reference" data-uri="unknown://unknown/article_L181-3_">article L181-3</a>']

    def test_ordinal(self):
        assert _parsed_elements("article premier") == ['<a class="dsr-section_reference" data-uri="unknown://unknown/article_1_">article premier</a>']
        assert _parsed_elements("article quatrième") == ['<a class="dsr-section_reference" data-uri="unknown://unknown/article_4_">article quatrième</a>']

    def test_article_num_range(self):
        assert _parsed_elements("articles 3 à 11") == ['<a class="dsr-section_reference" data-uri="unknown://unknown/article_3_11">articles 3 à 11</a>']
        assert _parsed_elements("articles 6.18.1 à 6.18.7") == ['<a class="dsr-section_reference" data-uri="unknown://unknown/article_6.18.1_6.18.7">articles 6.18.1 à 6.18.7</a>']
        assert _parsed_elements("articles 6.18.a à 6.18.c") == ['<a class="dsr-section_reference" data-uri="unknown://unknown/article_6.18.a_6.18.c">articles 6.18.a à 6.18.c</a>']

    def test_ordinal_range(self):
        assert _parsed_elements("de l'article premier à l'article troisième") == [
            'de l\'',
            '<a class="dsr-section_reference" data-uri="unknown://unknown/article_1_3">article premier à l\'article troisième</a>',
        ]
        assert _parsed_elements("des articles second à 10ème") == [
            'des ',
            '<a class="dsr-section_reference" data-uri="unknown://unknown/article_2_10">articles second à 10ème</a>',
        ]

    def test_code_article_range(self):
        assert _parsed_elements("de l'article R. 511-9 à l'article D.512") == [
            'de l\'',
            '<a class="dsr-section_reference" data-uri="unknown://unknown/article_R.%20511-9_D.512">article R. 511-9 à l\'article D.512</a>',
        ]
        assert _parsed_elements("l' article R.543-137 à R.543-151") == [
            'l\' ',
            '<a class="dsr-section_reference" data-uri="unknown://unknown/article_R.543-137_R.543-151">article R.543-137 à R.543-151</a>',
        ]


class TestArticlePluralRegex(unittest.TestCase):

    def test_article_num(self):
        assert _parsed_elements('articles 5.1.9, 9.2.1, 10.2.1 et 10.2.5') == [
            '<a class="dsr-section_reference" data-uri="unknown://unknown/article_5.1.9_">articles 5.1.9</a>',
            ', ',
            '<a class="dsr-section_reference" data-uri="unknown://unknown/article_9.2.1_">9.2.1</a>',
            ', ',
            '<a class="dsr-section_reference" data-uri="unknown://unknown/article_10.2.1_">10.2.1</a>',
            ' et ',
            '<a class="dsr-section_reference" data-uri="unknown://unknown/article_10.2.5_">10.2.5</a>',
        ]

    def test_ordinal(self):
        assert _parsed_elements('articles premier,9.a') == [
            '<a class="dsr-section_reference" data-uri="unknown://unknown/article_1_">articles premier</a>',
            ',',
            '<a class="dsr-section_reference" data-uri="unknown://unknown/article_9.a_">9.a</a>',
        ]
        assert _parsed_elements('articles premier et second') == [
            '<a class="dsr-section_reference" data-uri="unknown://unknown/article_1_">articles premier</a>',
            ' et ',
            '<a class="dsr-section_reference" data-uri="unknown://unknown/article_2_">second</a>',
        ]

    def test_article_code(self):
        assert _parsed_elements('articles R. 511-9 et L. 111') == [
            '<a class="dsr-section_reference" data-uri="unknown://unknown/article_R.%20511-9_">articles R. 511-9</a>',
            ' et ',
            '<a class="dsr-section_reference" data-uri="unknown://unknown/article_L.%20111_">L. 111</a>',
        ]

    def test_article_range(self):
        assert _parsed_elements('articles R. 512 - 74 et R. 512 39-1 à R.512-39-3') == [
            '<a class="dsr-section_reference" data-uri="unknown://unknown/article_R.%20512%20-%2074_">articles R. 512 - 74</a>',
            ' et ',
            '<a class="dsr-section_reference" data-uri="unknown://unknown/article_R.%20512%2039-1_R.512-39-3">R. 512 39-1 à R.512-39-3</a>',
        ]

    def test_range_first(self):
        assert _parsed_elements('articles R.541-49 à R.541-64 et R.541-79') == [
            '<a class="dsr-section_reference" data-uri="unknown://unknown/article_R.541-49_R.541-64">articles R.541-49 à R.541-64</a>',
            ' et ',
            '<a class="dsr-section_reference" data-uri="unknown://unknown/article_R.541-79_">R.541-79</a>',
        ]


class TestParseAlineaRegex(unittest.TestCase):

    def test_alinea_num_before(self):
        assert _parsed_elements("2ème alinéa de l'article 1") == [
            '<a class="dsr-section_reference" data-uri="unknown://unknown/article_1_/alinea_2_">2ème alinéa de l\'article 1</a>'
        ]
        assert _parsed_elements("5° de l'article 5") == [
            '<a class="dsr-section_reference" data-uri="unknown://unknown/article_5_/alinea_5_">5° de l\'article 5</a>'
        ]

    def test_alinea_num_after(self):
        assert _parsed_elements("alinéa 3 de l'article 2") == [
            '<a class="dsr-section_reference" data-uri="unknown://unknown/article_2_/alinea_3_">alinéa 3 de l\'article 2</a>'
        ]
        assert _parsed_elements("alinéa second de l'article 3") == [
            '<a class="dsr-section_reference" data-uri="unknown://unknown/article_3_/alinea_2_">alinéa second de l\'article 3</a>'
        ]
        assert _parsed_elements("alinéa neuvième de l'article 4") == [
            '<a class="dsr-section_reference" data-uri="unknown://unknown/article_4_/alinea_9_">alinéa neuvième de l\'article 4</a>'
        ]

    def test_alinea_list(self):
        assert _parsed_elements("Les paragraphes 3 et 4 de l'article 8.5.1.1") == [
            'Les ',
            '<a class="dsr-section_reference" data-uri="unknown://unknown/article_8.5.1.1_/alinea_3_">paragraphes 3</a>',
            ' et ',
            '<a class="dsr-section_reference" data-uri="unknown://unknown/article_8.5.1.1_/alinea_4_">4 de l\'article 8.5.1.1</a>',
        ]


class TestParseTargetPositionReferences(unittest.TestCase):

    def test_simple_singular(self):
        assert _parsed_elements(
            "2ème alinéa de l'article 4.1.b de l'arrêté 90/IC/035"
        ) == [
            '<a class="dsr-section_reference" data-uri="unknown://unknown/article_4.1.b_/alinea_2_">2ème alinéa de l\'article 4.1.b</a>',
            ' de l\'arrêté 90/IC/035'
        ]

    def test_singular_range(self):
        assert _parsed_elements(
            'aux dispositions des articles R. 515-60 à R. 515-84 du code'
        ) == [
            'aux dispositions des ',
            '<a class="dsr-section_reference" data-uri="unknown://unknown/article_R.%20515-60_R.%20515-84">articles R. 515-60 à R. 515-84</a>',
            ' du code'
        ]

    def test_plural_articles(self):
        assert _parsed_elements(
            "articles premier, 9 et 10.a"
        ) == [
            '<a class="dsr-section_reference" data-uri="unknown://unknown/article_1_">articles premier</a>',
            ', ',
            '<a class="dsr-section_reference" data-uri="unknown://unknown/article_9_">9</a>',
            ' et ',
            '<a class="dsr-section_reference" data-uri="unknown://unknown/article_10.a_">10.a</a>',
        ]

    def test_plural_articles_with_range(self):
        assert _parsed_elements(
            "articles R. 512 - 74 et R. 512 39-1 à R.512-39-3"
        ) == [
            '<a class="dsr-section_reference" data-uri="unknown://unknown/article_R.%20512%20-%2074_">articles R. 512 - 74</a>',
            ' et ',
            '<a class="dsr-section_reference" data-uri="unknown://unknown/article_R.%20512%2039-1_R.512-39-3">R. 512 39-1 à R.512-39-3</a>',
        ]

    def test_plural_range_first(self):
        assert _parsed_elements(
            "les dispositions des articles R.541-49 à R.541-64 et R.541-79 du code"
        ) == [
            'les dispositions des ',
            '<a class="dsr-section_reference" data-uri="unknown://unknown/article_R.541-49_R.541-64">articles R.541-49 à R.541-64</a>',
            ' et ',
            '<a class="dsr-section_reference" data-uri="unknown://unknown/article_R.541-79_">R.541-79</a>',
            ' du code'
        ]

    def test_with_alinea(self):
        assert _parsed_elements(
            "du 5° de l'article 4.1.b de l'arrêté 90/IC/035"
        ) == [
            'du ',
            '<a class="dsr-section_reference" data-uri="unknown://unknown/article_4.1.b_/alinea_5_">5° de l\'article 4.1.b</a>',
            ' de l\'arrêté 90/IC/035'
        ]


def _parsed_elements(string: str):
    soup = BeautifulSoup(string, features='html.parser')
    elements = parse_section_references(soup, soup.children)
    return [str(element) for element in elements]