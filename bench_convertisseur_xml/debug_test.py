import unittest
import re
from typing import Dict

from bs4 import BeautifulSoup

from .debug import insert_debug_keywords


class TestParseTargetPositionReferences(unittest.TestCase):

    def test_simple(self):
        soup = BeautifulSoup("Premier alinéa et 2ème alinéa du présent article", features='html.parser')
        children = insert_debug_keywords(soup, soup.children, 'alinéa')
        expected_children = [
            'Premier ',
            '<span class="dsr-debug_keyword" data-query="alinéa">alinéa</span>',
            ' et 2ème ',
            '<span class="dsr-debug_keyword" data-query="alinéa">alinéa</span>',
            ' du présent article'
        ]
        assert [str(child) for child in children] == expected_children

    def test_with_accent(self):
        soup = BeautifulSoup("Premier alinea du présent article", features='html.parser')
        children = insert_debug_keywords(soup, soup.children, 'alinéa')
        expected_children = [
            'Premier ',
            '<span class="dsr-debug_keyword" data-query="alinéa">alinea</span>',
            ' du présent article',
        ]
        assert [str(child) for child in children] == expected_children