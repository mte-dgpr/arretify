import unittest

from bs4 import BeautifulSoup

from bench_convertisseur_xml.utils.testing import make_testing_function_for_children_list
from .self_detection import parse_self_references


process_children = make_testing_function_for_children_list(parse_self_references)


class TestParseSelfReferences(unittest.TestCase):

    def test_simple(self):
        assert process_children('l\'article 8 du présent arrêté remplace') == [
            "l'article 8 du ",
            '<a class="dsr-document_reference" data-is_resolvable="true" data-uri="dsr://self____">présent arrêté</a>',
            ' remplace',
        ]