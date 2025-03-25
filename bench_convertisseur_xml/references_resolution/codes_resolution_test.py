import unittest

from bs4 import BeautifulSoup

from .codes_resolution import resolve_code_articles_legifrance_ids, resolve_code_legifrance_ids


class TestResolveSectionsDocuments(unittest.TestCase):
    def test_simple_article(self):
        # Arrange
        soup = BeautifulSoup(
            '<a class="dsr-section_reference" data-is_resolvable="false" data-uri="dsr://code_LEGITEXT000006074220___/article__R541-15__">article R541-15</a>', 
            features='html.parser'
        )
        children = list(soup.children)

        # Act
        result = resolve_code_articles_legifrance_ids(soup, children)

        # Assert
        assert str(result[0]) == '<a class="dsr-section_reference" data-is_resolvable="true" data-uri="dsr://code_LEGITEXT000006074220___/article_LEGIARTI000032728274_R541-15__" href="https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000032728274">article R541-15</a>'

    def test_article_range(self):
        # Arrange
        soup = BeautifulSoup(
            '<a class="dsr-section_reference" data-is_resolvable="false" data-uri="dsr://code_LEGITEXT000006074220___/article__R541-15__R541-20">articles R541-15 à R541-20</a>', 
            features='html.parser'
        )
        children = list(soup.children)

        # Act
        result = resolve_code_articles_legifrance_ids(soup, children)

        # Assert
        assert str(result[0]) == '<a class="dsr-section_reference" data-is_resolvable="true" data-uri="dsr://code_LEGITEXT000006074220___/article_LEGIARTI000032728274_R541-15_LEGIARTI000028249688_R541-20" href="https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000032728274">articles R541-15 à R541-20</a>'


class TestResolveCodeDocuments(unittest.TestCase):
    def test_resolve_code(self):
        # Arrange
        soup = BeautifulSoup(
            '<a class="dsr-document_reference" data-is_resolvable="false" data-uri="dsr://code____Code%20de%20l%27environnement">code de l\'environnemenent</a>', 
            features='html.parser'
        )
        children = list(soup.children)

        # Act
        result = resolve_code_legifrance_ids(soup, children)

        # Assert
        assert str(result[0]) == '<a class="dsr-document_reference" data-is_resolvable="true" data-uri="dsr://code_LEGITEXT000006074220___Code%20de%20l%27environnement" href="https://www.legifrance.gouv.fr/codes/texte_lc/LEGITEXT000006074220">code de l\'environnemenent</a>'