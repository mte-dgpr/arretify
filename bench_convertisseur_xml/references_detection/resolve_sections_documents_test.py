import unittest

from bs4 import BeautifulSoup

from .resolve_sections_documents import resolve_sections_documents


class TestResolveSectionsDocuments(unittest.TestCase):
    def test_unknown_arrete(self):
        # Arrange
        soup = BeautifulSoup(
            '<a class="dsr-section_reference" data-uri="unknown://unknown/article_5_">article 5</a>'
            'de l’'
            '<a class="dsr-document_reference" data-uri="unknown://arrete_2016-05-23">'
            'arrêté du'
            '<time class="dsr-date" datetime="2016-05-23">'
            '23 mai 2016'
           '</time>'
          '</a>', features='html.parser'
        )
        children = list(soup.children)

        # Act
        result = resolve_sections_documents(soup, children)

        # Assert
        assert str(result[0]) == '<a class="dsr-section_reference" data-uri="unknown://arrete_2016-05-23/article_5_">article 5</a>'

    def test_code(self):
        # Arrange
        soup = BeautifulSoup(
            '<a class="dsr-section_reference" data-uri="unknown://unknown/article_R.181-48_">'
            'article R.181-48'
            '</a>'
            'du'
            '<a class="dsr-document_reference" data-uri="code://Code%20de%20l%27environnement">'
            'code de l\'environnement'
            '</a>', features='html.parser'
        )
        children = list(soup.children)

        # Act
        result = resolve_sections_documents(soup, children)

        # Assert
        assert str(result[0]) == '<a class="dsr-section_reference" data-uri="code://Code%20de%20l%27environnement/article_R.181-48_">article R.181-48</a>'