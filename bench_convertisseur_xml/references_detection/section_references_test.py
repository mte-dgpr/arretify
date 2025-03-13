import unittest
import re
from typing import Dict, List

from bs4 import BeautifulSoup

from .section_references import parse_section_references


class TestHandleArticleRange(unittest.TestCase):

    def test_article_num(self):
        assert _parsed_elements("article 4.1.b") == ['<a class="dsr-section_reference" data-is_resolvable="false" data-uri="dsr://unknown____/article__4.1.b__">article 4.1.b</a>']
        assert _parsed_elements("article 8") == ['<a class="dsr-section_reference" data-is_resolvable="false" data-uri="dsr://unknown____/article__8__">article 8</a>']
        assert _parsed_elements("article 1er") == ['<a class="dsr-section_reference" data-is_resolvable="false" data-uri="dsr://unknown____/article__1__">article 1er</a>']
        assert _parsed_elements("article 111è") == ['<a class="dsr-section_reference" data-is_resolvable="false" data-uri="dsr://unknown____/article__111__">article 111è</a>']
        assert _parsed_elements("article 2ème") == ['<a class="dsr-section_reference" data-is_resolvable="false" data-uri="dsr://unknown____/article__2__">article 2ème</a>']

    def test_code_article(self):
        assert _parsed_elements("article R. 511-9") == ['<a class="dsr-section_reference" data-is_resolvable="false" data-uri="dsr://unknown____/article__R.%20511-9__">article R. 511-9</a>']
        assert _parsed_elements("article D.12") == ['<a class="dsr-section_reference" data-is_resolvable="false" data-uri="dsr://unknown____/article__D.12__">article D.12</a>']
        assert _parsed_elements("article L181-3") == ['<a class="dsr-section_reference" data-is_resolvable="false" data-uri="dsr://unknown____/article__L181-3__">article L181-3</a>']

    def test_ordinal(self):
        assert _parsed_elements("article premier") == ['<a class="dsr-section_reference" data-is_resolvable="false" data-uri="dsr://unknown____/article__1__">article premier</a>']
        assert _parsed_elements("article quatrième") == ['<a class="dsr-section_reference" data-is_resolvable="false" data-uri="dsr://unknown____/article__4__">article quatrième</a>']

    def test_article_num_range(self):
        assert _parsed_elements("articles 3 à 11") == ['<a class="dsr-section_reference" data-is_resolvable="false" data-uri="dsr://unknown____/article__3__11">articles 3 à 11</a>']
        assert _parsed_elements("articles 6.18.1 à 6.18.7") == ['<a class="dsr-section_reference" data-is_resolvable="false" data-uri="dsr://unknown____/article__6.18.1__6.18.7">articles 6.18.1 à 6.18.7</a>']
        assert _parsed_elements("articles 6.18.a à 6.18.c") == ['<a class="dsr-section_reference" data-is_resolvable="false" data-uri="dsr://unknown____/article__6.18.a__6.18.c">articles 6.18.a à 6.18.c</a>']

    def test_ordinal_range(self):
        assert _parsed_elements("de l'article premier à l'article troisième") == [
            'de l\'',
            '<a class="dsr-section_reference" data-is_resolvable="false" data-uri="dsr://unknown____/article__1__3">article premier à l\'article troisième</a>',
        ]
        assert _parsed_elements("des articles second à 10ème") == [
            'des ',
            '<a class="dsr-section_reference" data-is_resolvable="false" data-uri="dsr://unknown____/article__2__10">articles second à 10ème</a>',
        ]

    def test_code_article_range(self):
        assert _parsed_elements("de l'article R. 511-9 à l'article D.512") == [
            'de l\'',
            '<a class="dsr-section_reference" data-is_resolvable="false" data-uri="dsr://unknown____/article__R.%20511-9__D.512">article R. 511-9 à l\'article D.512</a>',
        ]
        assert _parsed_elements("l' article R.543-137 à R.543-151") == [
            'l\' ',
            '<a class="dsr-section_reference" data-is_resolvable="false" data-uri="dsr://unknown____/article__R.543-137__R.543-151">article R.543-137 à R.543-151</a>',
        ]


class TestArticlePluralRegex(unittest.TestCase):

    def test_article_num(self):
        assert _parsed_elements('articles 5.1.9, 9.2.1, 10.2.1 et 10.2.5') == [
            ('<span class="dsr-section_reference_multiple">'
            '<a class="dsr-section_reference" data-is_resolvable="false" data-uri="dsr://unknown____/article__5.1.9__">articles 5.1.9</a>'
            ', '
            '<a class="dsr-section_reference" data-is_resolvable="false" data-uri="dsr://unknown____/article__9.2.1__">9.2.1</a>'
            ', '
            '<a class="dsr-section_reference" data-is_resolvable="false" data-uri="dsr://unknown____/article__10.2.1__">10.2.1</a>'
            ' et '
            '<a class="dsr-section_reference" data-is_resolvable="false" data-uri="dsr://unknown____/article__10.2.5__">10.2.5</a>'
            '</span>')
        ]

    def test_ordinal(self):
        assert _parsed_elements('articles premier,9.a') == [
            ('<span class="dsr-section_reference_multiple">'
            '<a class="dsr-section_reference" data-is_resolvable="false" data-uri="dsr://unknown____/article__1__">articles premier</a>'
            ','
            '<a class="dsr-section_reference" data-is_resolvable="false" data-uri="dsr://unknown____/article__9.a__">9.a</a>'
            '</span>')
        ]
        assert _parsed_elements('articles premier et second') == [
            ('<span class="dsr-section_reference_multiple">'
            '<a class="dsr-section_reference" data-is_resolvable="false" data-uri="dsr://unknown____/article__1__">articles premier</a>'
            ' et '
            '<a class="dsr-section_reference" data-is_resolvable="false" data-uri="dsr://unknown____/article__2__">second</a>'
            '</span>')
        ]

    def test_article_code(self):
        assert _parsed_elements('articles R. 511-9 et L. 111') == [
            ('<span class="dsr-section_reference_multiple">'
            '<a class="dsr-section_reference" data-is_resolvable="false" data-uri="dsr://unknown____/article__R.%20511-9__">articles R. 511-9</a>'
            ' et '
            '<a class="dsr-section_reference" data-is_resolvable="false" data-uri="dsr://unknown____/article__L.%20111__">L. 111</a>'
            '</span>')
        ]

    def test_article_range(self):
        assert _parsed_elements('articles R. 512 - 74 et R. 512 39-1 à R.512-39-3') == [
            ('<span class="dsr-section_reference_multiple">'
            '<a class="dsr-section_reference" data-is_resolvable="false" data-uri="dsr://unknown____/article__R.%20512%20-%2074__">articles R. 512 - 74</a>'
            ' et '
            '<a class="dsr-section_reference" data-is_resolvable="false" data-uri="dsr://unknown____/article__R.%20512%2039-1__R.512-39-3">R. 512 39-1 à R.512-39-3</a>'
            '</span>')
        ]

    def test_range_first(self):
        assert _parsed_elements('articles R.541-49 à R.541-64 et R.541-79') == [
            ('<span class="dsr-section_reference_multiple">'
            '<a class="dsr-section_reference" data-is_resolvable="false" data-uri="dsr://unknown____/article__R.541-49__R.541-64">articles R.541-49 à R.541-64</a>'
            ' et '
            '<a class="dsr-section_reference" data-is_resolvable="false" data-uri="dsr://unknown____/article__R.541-79__">R.541-79</a>'
            '</span>')
        ]


class TestParseAlineaRegex(unittest.TestCase):

    def test_alinea_num_before(self):
        assert _parsed_elements("2ème alinéa de l'article 1") == [
            '<a class="dsr-section_reference" data-is_resolvable="false" data-uri="dsr://unknown____/article__1__/alinea__2__">2ème alinéa de l\'article 1</a>'
        ]
        assert _parsed_elements("5° de l'article 5") == [
            '<a class="dsr-section_reference" data-is_resolvable="false" data-uri="dsr://unknown____/article__5__/alinea__5__">5° de l\'article 5</a>'
        ]

    def test_alinea_num_after(self):
        assert _parsed_elements("alinéa 3 de l'article 2") == [
            '<a class="dsr-section_reference" data-is_resolvable="false" data-uri="dsr://unknown____/article__2__/alinea__3__">alinéa 3 de l\'article 2</a>'
        ]
        assert _parsed_elements("alinéa second de l'article 3") == [
            '<a class="dsr-section_reference" data-is_resolvable="false" data-uri="dsr://unknown____/article__3__/alinea__2__">alinéa second de l\'article 3</a>'
        ]
        assert _parsed_elements("alinéa neuvième de l'article 4") == [
            '<a class="dsr-section_reference" data-is_resolvable="false" data-uri="dsr://unknown____/article__4__/alinea__9__">alinéa neuvième de l\'article 4</a>'
        ]


class TestParseAlineaMultipleRegex(unittest.TestCase):

    def test_alinea_list(self):
        assert _parsed_elements("Les paragraphes 3 et 4 de l'article 8.5.1.1") == [
            'Les ',
            ('<span class="dsr-section_reference_multiple">'
            '<a class="dsr-section_reference" data-is_resolvable="false" data-uri="dsr://unknown____/article__8.5.1.1__/alinea__3__">paragraphes 3</a>'
            ' et '
            '<a class="dsr-section_reference" data-is_resolvable="false" data-uri="dsr://unknown____/article__8.5.1.1__/alinea__4__">4 de l\'article 8.5.1.1</a>'
            '</span>')
        ]


def _parsed_elements(string: str):
    soup = BeautifulSoup(string, features='html.parser')
    elements = parse_section_references(soup, soup.children)
    return [str(element) for element in elements]