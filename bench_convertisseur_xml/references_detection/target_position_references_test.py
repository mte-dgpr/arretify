import unittest
import re
from typing import Dict

from bs4 import BeautifulSoup

from .target_position_references import (
    ARTICLE_PATTERN_S, ARTICLE_RANGE_PATTERN_S, _handle_article_range_match_groupdict,
    ALINEA_NUM_BEFORE_PATTERN_S, ALINEA_NUM_AFTER_PATTERN_S, _handle_alinea_match_groupdict,
    parse_target_position_references, ARTICLE_PLURAL_PATTERN, ALINEA_SYMBOL_PATTERN_S
)
from bench_convertisseur_xml.utils.regex import search_groupdict


class TestHandleArticleRange(unittest.TestCase):

    def test_article_num(self):
        assert _handle_article_range_match_groupdict(search_groupdict(
            ARTICLE_PATTERN_S, "de l'article 4.1.b de")) == dict(article_start='4.1.b', article_end=None)
        assert _handle_article_range_match_groupdict(search_groupdict(
            ARTICLE_PATTERN_S, "l'article 8 de")) == dict(article_start='8', article_end=None)
        assert _handle_article_range_match_groupdict(search_groupdict(
            ARTICLE_PATTERN_S, "article 1er de")) == dict(article_start='1', article_end=None)
        assert _handle_article_range_match_groupdict(search_groupdict(
            ARTICLE_PATTERN_S, "article 111è de")) == dict(article_start='111', article_end=None)
        assert _handle_article_range_match_groupdict(search_groupdict(
            ARTICLE_PATTERN_S, "de l'article 2ème")) == dict(article_start='2', article_end=None)

    def test_code_article(self):
        assert _handle_article_range_match_groupdict(search_groupdict(
            ARTICLE_PATTERN_S, "de l'article R. 511-9")) == dict(article_start='R. 511-9', article_end=None)
        assert _handle_article_range_match_groupdict(search_groupdict(
            ARTICLE_PATTERN_S, "de l'article D.12")) == dict(article_start='D.12', article_end=None)
        assert _handle_article_range_match_groupdict(search_groupdict(
            ARTICLE_PATTERN_S, "article L181-3")) == dict(article_start='L181-3', article_end=None)

    def test_ordinal(self):
        assert _handle_article_range_match_groupdict(search_groupdict(
            ARTICLE_PATTERN_S, "article premier de")) == dict(article_start='1', article_end=None)
        assert _handle_article_range_match_groupdict(search_groupdict(
            ARTICLE_PATTERN_S, "article quatrieme de")) == dict(article_start='4', article_end=None)

    def test_article_num_range(self):
        assert _handle_article_range_match_groupdict(search_groupdict(
            ARTICLE_RANGE_PATTERN_S, "articles 3 à 11 de")) == dict(article_start='3', article_end='11')
        assert _handle_article_range_match_groupdict(search_groupdict(
            ARTICLE_RANGE_PATTERN_S, "articles 6.18.1 à 6.18.7 de")) == dict(article_start='6.18.1', article_end='6.18.7')
        assert _handle_article_range_match_groupdict(search_groupdict(
            ARTICLE_RANGE_PATTERN_S, "articles 6.18.a à 6.18.c de")) == dict(article_start='6.18.a', article_end='6.18.c')

    def test_ordinal_range(self):
        assert _handle_article_range_match_groupdict(search_groupdict(
            ARTICLE_RANGE_PATTERN_S, "de l'article premier à l'article troisième")) == dict(article_start='1', article_end='3')
        assert _handle_article_range_match_groupdict(search_groupdict(
            ARTICLE_RANGE_PATTERN_S, "des articles second à 10ème")) == dict(article_start='2', article_end='10')

    def test_code_article_range(self):
        assert _handle_article_range_match_groupdict(search_groupdict(
            ARTICLE_RANGE_PATTERN_S, "de l'article R. 511-9 à l'article D.512")) == dict(article_start='R. 511-9', article_end='D.512')
        assert _handle_article_range_match_groupdict(search_groupdict(
            ARTICLE_RANGE_PATTERN_S, "l' article R.543-137 à R.543-151")) == dict(article_start='R.543-137', article_end='R.543-151')


class TestArticlePluralRegex(unittest.TestCase):

    def test_article_num(self):
        string = 'articles 5.1.9, 9.2.1, 10.2.1 et 10.2.5'
        match = ARTICLE_PLURAL_PATTERN.search(string)
        assert match.group(0) == string

    def test_ordinal(self):
        string = 'articles premier,9.a'
        match = ARTICLE_PLURAL_PATTERN.search(string)
        assert match.group(0) == string
        string = 'articles premier et second'
        match = ARTICLE_PLURAL_PATTERN.search(string)
        assert match.group(0) == string

    def test_article_code(self):
        string = 'articles premier,9.a'
        match = ARTICLE_PLURAL_PATTERN.search(string)
        assert match.group(0) == string
        string = 'articles R. 511-9 et L. 111'
        match = ARTICLE_PLURAL_PATTERN.search(string)
        assert match.group(0) == string

    def test_article_range(self):
        string = 'articles R. 512 - 74 et R. 512 39-1 à R.512-39-3'
        match = ARTICLE_PLURAL_PATTERN.search(string)
        assert match.group(0) == string

    def test_range_first(self):
        string = 'articles R.541-49 à R.541-64 et R.541-79'
        match = ARTICLE_PLURAL_PATTERN.search(string)
        assert match.group(0) == string

    def test_negative_cases(self):
        assert ARTICLE_PLURAL_PATTERN.search('articles L. 342-1 et suivants') is None


class TestParseAlineaRegex(unittest.TestCase):

    def test_alinea_num_before(self):
        assert _handle_alinea_match_groupdict(search_groupdict(
            ALINEA_NUM_BEFORE_PATTERN_S, "2ème alinéa")) == dict(alinea_start="2", alinea_end=None)
        assert _handle_alinea_match_groupdict(search_groupdict(
            ALINEA_NUM_BEFORE_PATTERN_S, "premier alinéa")) == dict(alinea_start="1", alinea_end=None)
        assert _handle_alinea_match_groupdict(search_groupdict(
            ALINEA_NUM_BEFORE_PATTERN_S, "11ème alinéa")) == dict(alinea_start="11", alinea_end=None)

    def test_alinea_num_after(self):
        assert _handle_alinea_match_groupdict(search_groupdict(
            ALINEA_NUM_AFTER_PATTERN_S, "alinéa 3")) == dict(alinea_start="3", alinea_end=None)
        assert _handle_alinea_match_groupdict(search_groupdict(
            ALINEA_NUM_AFTER_PATTERN_S, "alinéa second")) == dict(alinea_start="2", alinea_end=None)
        assert _handle_alinea_match_groupdict(search_groupdict(
            ALINEA_NUM_AFTER_PATTERN_S, "alinéa neuvième")) == dict(alinea_start="9", alinea_end=None)

    def test_alinea_symbol(self):
        assert _handle_alinea_match_groupdict(search_groupdict(
            ALINEA_SYMBOL_PATTERN_S, "5°")) == dict(alinea_start="5", alinea_end=None)
        


class TestParseTargetPositionReferences(unittest.TestCase):

    def test_simple_singular(self):
        soup = BeautifulSoup("2ème alinéa de l'article 4.1.b de l'arrêté 90/IC/035", features='html.parser')
        elements = parse_target_position_references(soup, soup.children)
        expected_elements = [
            '<a class="dsr-target_position_reference" data-alinea_start="2" data-article_start="4.1.b">2ème alinéa de l\'article 4.1.b</a>',
            ' de l\'arrêté 90/IC/035'
        ]
        assert [str(element) for element in elements] == expected_elements

    def test_singular_range(self):
        soup = BeautifulSoup('aux dispositions des articles R. 515-60 à R. 515-84 du code', features='html.parser')
        elements = parse_target_position_references(soup, soup.children)
        expected_elements = [
            'aux dispositions des ',
            '<a class="dsr-target_position_reference" data-article_end="R. 515-84" data-article_start="R. 515-60">articles R. 515-60 à R. 515-84</a>',
            ' du code'
        ]
        assert [str(element) for element in elements] == expected_elements

    def test_plural_articles(self):
        soup = BeautifulSoup("articles premier, 9 et 10.a", features='html.parser')
        elements = parse_target_position_references(soup, soup.children)
        expected_elements = [
            '<a class="dsr-target_position_reference" data-article_start="1">articles premier</a>',
            ', ',
            '<a class="dsr-target_position_reference" data-article_start="9">9</a>',
            ' et ',
            '<a class="dsr-target_position_reference" data-article_start="10.a">10.a</a>',
        ]
        assert [str(element) for element in elements] == expected_elements

    def test_plural_articles_with_range(self):
        soup = BeautifulSoup("articles R. 512 - 74 et R. 512 39-1 à R.512-39-3", features='html.parser')
        elements = parse_target_position_references(soup, soup.children)
        expected_elements = [
            '<a class="dsr-target_position_reference" data-article_start="R. 512 - 74">articles R. 512 - 74</a>',
            ' et ',
            '<a class="dsr-target_position_reference" data-article_end="R.512-39-3" data-article_start="R. 512 39-1">R. 512 39-1 à R.512-39-3</a>',
        ]
        assert [str(element) for element in elements] == expected_elements

    def test_plural_range_first(self):
        soup = BeautifulSoup("les dispositions des articles R.541-49 à R.541-64 et R.541-79 du code", features='html.parser')
        elements = parse_target_position_references(soup, soup.children)
        expected_elements = [
            'les dispositions des ',
            '<a class="dsr-target_position_reference" data-article_end="R.541-64" data-article_start="R.541-49">articles R.541-49 à R.541-64</a>',
            ' et ',
            '<a class="dsr-target_position_reference" data-article_start="R.541-79">R.541-79</a>',
            ' du code'
        ]
        assert [str(element) for element in elements] == expected_elements

    def test_with_alinea(self):
        soup = BeautifulSoup("du 5° de l'article 4.1.b de l'arrêté 90/IC/035", features='html.parser')
        elements = parse_target_position_references(soup, soup.children)
        expected_elements = [
            'du ',
            '<a class="dsr-target_position_reference" data-alinea_start="5" data-article_start="4.1.b">5° de l\'article 4.1.b</a>',
            ' de l\'arrêté 90/IC/035'
        ]
        assert [str(element) for element in elements] == expected_elements