import unittest

from bs4 import BeautifulSoup

from bench_convertisseur_xml.utils.testing import make_testing_function_for_children_list
from .codes_detection import parse_codes_references


process_children = make_testing_function_for_children_list(parse_codes_references)


class TestParseCodesReferences(unittest.TestCase):

    def test_simple(self):
        assert process_children('Bla bla code de l’environnement') == [
            'Bla bla ',
            '<a class="dsr-document_reference" data-is_resolvable="false" data-uri="dsr://code____Code%20de%20l%27environnement">code de l’environnement</a>',
        ]
