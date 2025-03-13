import unittest

from bs4 import BeautifulSoup

from .sections import match_sections_with_documents


class TestResolveSectionsDocuments(unittest.TestCase):
    def test_unknown_arrete(self):
        # Arrange
        soup = BeautifulSoup(
            '<a class="dsr-section_reference" data-is_resolvable="false" data-uri="dsr://unknown____/article__5__">article 5</a>'
            'de l’'
            '<a class="dsr-document_reference" data-is_resolvable="false" data-uri="dsr://arrete___2016-05-23_">'
            'arrêté du'
            '<time class="dsr-date" datetime="2016-05-23">'
            '23 mai 2016'
           '</time>'
          '</a>', features='html.parser'
        )
        children = list(soup.children)

        # Act
        result = match_sections_with_documents(soup, children)

        # Assert
        assert str(result[0]) == '<a class="dsr-section_reference" data-is_resolvable="false" data-uri="dsr://arrete___2016-05-23_/article__5__">article 5</a>'

    def test_code(self):
        # Arrange
        soup = BeautifulSoup(
            '<a class="dsr-section_reference" data-is_resolvable="false" data-uri="dsr://unknown____/article__R.181-48__">'
            'article R.181-48'
            '</a>'
            'et suivants du'
            '<a class="dsr-document_reference" data-is_resolvable="false" data-uri="dsr://code____Code%20de%20l%27environnement">'
            'code de l\'environnement'
            '</a>', features='html.parser'
        )
        children = list(soup.children)

        # Act
        result = match_sections_with_documents(soup, children)

        # Assert
        assert str(result[0]) == '<a class="dsr-section_reference" data-is_resolvable="false" data-uri="dsr://code____Code%20de%20l%27environnement/article__R.181-48__">article R.181-48</a>'

    def test_too_many_words_connector(self):
        # Arrange
        soup = BeautifulSoup(
            '<a class="dsr-section_reference" data-is_resolvable="false" data-uri="dsr://unknown____/article__R.181-48__">'
            'article R.181-48'
            '</a>'
            'et suivants, parce que bla bla bla du'
            '<a class="dsr-document_reference" data-is_resolvable="false" data-uri="dsr://code____Code%20de%20l%27environnement">'
            'code de l\'environnement'
            '</a>', features='html.parser'
        )
        children = list(soup.children)

        # Act
        result = match_sections_with_documents(soup, children)

        # Assert
        assert str(result[0]) == '<a class="dsr-section_reference" data-is_resolvable="false" data-uri="dsr://unknown____/article__R.181-48__">article R.181-48</a>'

    def test_multiple_sections(self):
        # Arrange
        soup = BeautifulSoup(
            '<span class="dsr-section_reference_multiple">'
            '<a class="dsr-section_reference" data-is_resolvable="false" data-uri="dsr://unknown____/article__R.%20512%20-%2074__">articles R. 512 - 74</a>'
            ' et '
            '<a class="dsr-section_reference" data-is_resolvable="false" data-uri="dsr://unknown____/article__R.%20512%2039-1__R.512-39-3">R. 512 39-1 à R.512-39-3</a>'
            '</span>'
            ' du '
            '<a class="dsr-document_reference" data-is_resolvable="false" data-uri="dsr://code____Code%20de%20l%27environnement">'
            'code de l\'environnement'
            '</a>'
            , features='html.parser'
        )
        children = list(soup.children)

        # Act
        result = match_sections_with_documents(soup, children)

        # Assert
        assert str(result[0]) == (
            '<span class="dsr-section_reference_multiple">'
            '<a class="dsr-section_reference" data-is_resolvable="false" data-uri="dsr://code____Code%20de%20l%27environnement/article__R.%20512%20-%2074__">articles R. 512 - 74</a>'
            ' et '
            '<a class="dsr-section_reference" data-is_resolvable="false" data-uri="dsr://code____Code%20de%20l%27environnement/article__R.%20512%2039-1__R.512-39-3">R. 512 39-1 à R.512-39-3</a>'
            '</span>'
        )