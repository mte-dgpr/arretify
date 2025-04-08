import unittest
from unittest.mock import patch, MagicMock

from bs4 import BeautifulSoup

from bench_convertisseur_xml.utils.testing import make_element_processor
from .eu_acts_resolution import resolve_eu_directive_eurlex_url, resolve_eu_decision_eurlex_url, resolve_eu_regulation_eurlex_url


process_eu_directive_document_reference = make_element_processor(resolve_eu_directive_eurlex_url)
process_eu_decision_document_reference = make_element_processor(resolve_eu_decision_eurlex_url)
process_eu_regulation_document_reference = make_element_processor(resolve_eu_regulation_eurlex_url)


class TestResolveEuActUrls(unittest.TestCase):
    def test_directive(self):
        process_eu_directive_document_reference(
            '<a class="dsr-document_reference" data-is_resolvable="false" data-uri="dsr://eu-directive__75_2010_">directive 2010/75/UE</a>',
        ) == '<a class="dsr-document_reference" data-is_resolvable="true" data-uri="dsr://eu-directive_https%3A%2F%2Feur-lex.europa.eu%2Flegal-content%2FFR%2FTXT%2FHTML%2F%3Furi%3Dcellar%3Ac7191b72-4e07-4712-86d6-d3ae5e4f0082_75_2010_" href="https://eur-lex.europa.eu/legal-content/FR/TXT/HTML/?uri=cellar:c7191b72-4e07-4712-86d6-d3ae5e4f0082">directive 2010/75/UE</a>'

    def test_decision(self):
        process_eu_decision_document_reference(
            '<a class="dsr-document_reference" data-is_resolvable="false" data-uri="dsr://eu-decision__2019_2020_">décision 2019/2020/UE</a>',
        ) == '<a class="dsr-document_reference" data-is_resolvable="true" data-uri="dsr://eu-decision_https%3A%2F%2Feur-lex.europa.eu%2Flegal-content%2FFR%2FTXT%2FHTML%2F%3Furi%3Dcellar%3A9b8a8b1b-7b3b-11e9-a1f8-01aa75ed71a1_2019_2020_" href="https://eur-lex.europa.eu/legal-content/FR/TXT/HTML/?uri=cellar:9b8a8b1b-7b3b-11e9-a1f8-01aa75ed71a1">décision 2019/2020/UE</a>'

    def test_regulation(self):
        process_eu_regulation_document_reference(
            '<a class="dsr-document_reference" data-is_resolvable="false" data-uri="dsr://eu-regulation__2019_2020_">règlement 2019/2020/UE</a>',
        ) == '<a class="dsr-document_reference" data-is_resolvable="true" data-uri="dsr://eu-regulation_https%3A%2F%2Feur-lex.europa.eu%2Flegal-content%2FFR%2FTXT%2FHTML%2F%3Furi%3Dcellar%3A9b8a8b1b-7b3b-11e9-a1f8-01aa75ed71a1_2019_2020_" href="https://eur-lex.europa.eu/legal-content/FR/TXT/HTML/?uri=cellar:9b8a8b1b-7b3b-11e9-a1f8-01aa75ed71a1">règlement 2019/2020/UE</a>'