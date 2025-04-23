import unittest

from arretify.utils.testing import (
    make_testing_function_for_children_list,
    normalized_html_str,
)
from .circulaires_detection import parse_circulaires_references

process_children = make_testing_function_for_children_list(parse_circulaires_references)


class TestParseCirculairesReferences(unittest.TestCase):

    def test_only_date(self):
        assert process_children("Bla bla circulaire du 30 mai 2005 relative à") == [
            "Bla bla ",
            normalized_html_str(
                """
                <a
                    class="dsr-document_reference"
                    data-is_resolvable="false"
                    data-uri="dsr://circulaire___2005-05-30_"
                >
                    circulaire du
                    <time class="dsr-date" datetime="2005-05-30">
                        30 mai 2005
                    </time>
                </a>
                """
            ),
            " relative à",
        ]

    def test_with_ministerielle(self):
        assert process_children("Bla bla circulaire ministérielle du 30 mai 2005 relative à") == [
            "Bla bla ",
            normalized_html_str(
                """
                <a
                    class="dsr-document_reference"
                    data-is_resolvable="false"
                    data-uri="dsr://circulaire___2005-05-30_"
                >
                    circulaire ministérielle du
                    <time class="dsr-date" datetime="2005-05-30">
                        30 mai 2005
                    </time>
                </a>
                """
            ),
            " relative à",
        ]

    def test_with_random_acronym(self):
        assert process_children("Bla bla circulaire DPPR/DE du 30 mai 2005 relative à") == [
            "Bla bla ",
            normalized_html_str(
                """
                <a
                    class="dsr-document_reference"
                    data-is_resolvable="false"
                    data-uri="dsr://circulaire___2005-05-30_"
                >
                    circulaire DPPR/DE du
                    <time class="dsr-date" datetime="2005-05-30">
                        30 mai 2005
                    </time>
                </a>
                """
            ),
            " relative à",
        ]

    def test_with_identifier_and_date(self):
        assert process_children("Bla bla circulaire n°2005-12 du 30 mai 2005 relative à") == [
            "Bla bla ",
            normalized_html_str(
                """
                <a
                    class="dsr-document_reference"
                    data-is_resolvable="false"
                    data-uri="dsr://circulaire__2005-12_2005-05-30_"
                >
                    circulaire n°2005-12 du
                    <time class="dsr-date" datetime="2005-05-30">
                        30 mai 2005
                    </time>
                </a>
                """
            ),
            " relative à",
        ]
