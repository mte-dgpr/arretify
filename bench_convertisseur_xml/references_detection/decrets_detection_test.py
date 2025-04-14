import unittest

from bench_convertisseur_xml.utils.testing import (
    make_testing_function_for_children_list,
    normalized_html_str,
)
from .decrets_detection import parse_decrets_references

process_children = make_testing_function_for_children_list(parse_decrets_references)


class TestParseDecretsReferences(unittest.TestCase):

    def test_simple(self):
        assert process_children("Bla bla décret n°2005-635 du 30 mai 2005 relatif à") == [
            "Bla bla ",
            normalized_html_str(
                """
                <a
                    class="dsr-document_reference"
                    data-is_resolvable="false"
                    data-uri="dsr://decret__2005-635_2005-05-30_"
                >
                    décret n°2005-635 du
                    <time class="dsr-date" datetime="2005-05-30">
                        30 mai 2005
                    </time>
                </a>
                """
            ),
            " relatif à",
        ]
