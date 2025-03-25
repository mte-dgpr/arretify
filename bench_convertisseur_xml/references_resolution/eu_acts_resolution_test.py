import unittest
from unittest.mock import patch, MagicMock

from bs4 import BeautifulSoup

from .eu_acts_resolution import resolve_eu_acts_eurlex_urls


class TestResolveEuActUrls(unittest.TestCase):
    def test_simple_directive(self):
        # Arrange
        soup = BeautifulSoup(
            '<a class="dsr-document_reference" data-is_resolvable="false" data-uri="dsr://eu-directive__75_2010_">directive 2010/75/UE</a>',
            features='html.parser'
        )
        children = list(soup.children)

        # Act
        result = resolve_eu_acts_eurlex_urls(soup, children)

        # Assert
        assert str(result[0]) == '<a class="dsr-document_reference" data-is_resolvable="true" data-uri="dsr://eu-directive_https%3A%2F%2Feur-lex.europa.eu%2Flegal-content%2FFR%2FTXT%2FHTML%2F%3Furi%3Dcellar%3Ac7191b72-4e07-4712-86d6-d3ae5e4f0082_75_2010_" href="https://eur-lex.europa.eu/legal-content/FR/TXT/HTML/?uri=cellar:c7191b72-4e07-4712-86d6-d3ae5e4f0082">directive 2010/75/UE</a>'
