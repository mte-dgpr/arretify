import unittest

from bs4 import BeautifulSoup

from .sections_unknown_uris import resolve_sections_unknown_uris


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
        result = resolve_sections_unknown_uris(soup, children)

        # Assert
        assert str(result[0]) == '<a class="dsr-section_reference" data-uri="unknown://arrete_2016-05-23/article_5_">article 5</a>'

    def test_code(self):
        # Arrange
        soup = BeautifulSoup(
            '<a class="dsr-section_reference" data-uri="unknown://unknown/article_R.181-48_">'
            'article R.181-48'
            '</a>'
            'et suivants du'
            '<a class="dsr-document_reference" data-uri="code://Code%20de%20l%27environnement">'
            'code de l\'environnement'
            '</a>', features='html.parser'
        )
        children = list(soup.children)

        # Act
        result = resolve_sections_unknown_uris(soup, children)

        # Assert
        assert str(result[0]) == '<a class="dsr-section_reference" data-uri="code://Code%20de%20l%27environnement/article_R.181-48_">article R.181-48</a>'

    def test_too_many_words_connector(self):
        # Arrange
        soup = BeautifulSoup(
            '<a class="dsr-section_reference" data-uri="unknown://unknown/article_R.181-48_">'
            'article R.181-48'
            '</a>'
            'et suivants, parce que bla bla bla du'
            '<a class="dsr-document_reference" data-uri="code://Code%20de%20l%27environnement">'
            'code de l\'environnement'
            '</a>', features='html.parser'
        )
        children = list(soup.children)

        # Act
        result = resolve_sections_unknown_uris(soup, children)

        # Assert
        assert str(result[0]) == '<a class="dsr-section_reference" data-uri="unknown://unknown/article_R.181-48_">article R.181-48</a>'

    def test_multiple_sections(self):
        # Arrange
        soup = BeautifulSoup(
            '<span class="dsr-section_reference_multiple">'
            '<a class="dsr-section_reference" data-uri="unknown://unknown/article_R.%20512%20-%2074_">articles R. 512 - 74</a>'
            ' et '
            '<a class="dsr-section_reference" data-uri="unknown://unknown/article_R.%20512%2039-1_R.512-39-3">R. 512 39-1 à R.512-39-3</a>'
            '</span>'
            ' du '
            '<a class="dsr-document_reference" data-uri="code://Code%20de%20l%27environnement">'
            'code de l\'environnement'
            '</a>'
            , features='html.parser'
        )
        children = list(soup.children)

        # Act
        result = resolve_sections_unknown_uris(soup, children)

        # Assert
        assert str(result[0]) == (
            '<span class="dsr-section_reference_multiple">'
            '<a class="dsr-section_reference" data-uri="code://Code%20de%20l%27environnement/article_R.%20512%20-%2074_">articles R. 512 - 74</a>'
            ' et '
            '<a class="dsr-section_reference" data-uri="code://Code%20de%20l%27environnement/article_R.%20512%2039-1_R.512-39-3">R. 512 39-1 à R.512-39-3</a>'
            '</span>'
        )