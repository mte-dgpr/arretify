import unittest

from arretify.utils.testing import (
    make_testing_function_for_children_list,
    normalized_html_str,
)
from arretify.utils import html
from .match_sections_with_documents import match_sections_with_documents

process_sections_and_documents = make_testing_function_for_children_list(
    match_sections_with_documents
)


class TestResolveSectionsDocuments(unittest.TestCase):
    def setUp(self):
        html._ID_COUNTER = 0

    def test_single_section(self):
        assert (
            process_sections_and_documents(
                """
            <a
                class="dsr-section_reference"
                data-is_resolvable="false"
                data-uri="dsr://unknown____/article__5__"
            >
                article 5
            </a>
            de l’
            <a
                class="dsr-document_reference"
                data-is_resolvable="false"
                data-uri="dsr://arrete___2016-05-23_"
            >
                arrêté du
                <time class="dsr-date" datetime="2016-05-23">
                    23 mai 2016
                </time>
            </a>
            """
            )
            == [
                normalized_html_str(
                    """
            <span class="dsr-sections_and_document_references">
                <a
                    class="dsr-section_reference"
                    data-document_reference="1"
                    data-is_resolvable="false"
                    data-uri="dsr://unknown____/article__5__"
                >
                    article 5
                </a>
                de l’
                <a
                    class="dsr-document_reference"
                    data-element_id="1"
                    data-is_resolvable="false"
                    data-uri="dsr://arrete___2016-05-23_"
                >
                    arrêté du
                    <time class="dsr-date" datetime="2016-05-23">
                        23 mai 2016
                    </time>
                </a>
            </span>
            """
                )
            ]
        )

    def test_multiple_sections(self):
        assert (
            process_sections_and_documents(
                """
            <span class="dsr-section_reference_multiple">
                <a
                    class="dsr-section_reference"
                    data-is_resolvable="false"
                    data-uri="dsr://unknown____/article__R.%20512%20-%2074__"
                >
                    articles R. 512 - 74
                </a>
                et
                <a
                    class="dsr-section_reference"
                    data-is_resolvable="false"
                    data-uri="dsr://unknown____/article__R.%20512%2039-1__R.512-39-3"
                >
                    R. 512 39-1 à R.512-39-3
                </a>
            </span>
            du
            <a
                class="dsr-document_reference"
                data-is_resolvable="false"
                data-uri="dsr://code____Code%20de%20l%27environnement"
            >
                code de l'environnement
            </a>
            """
            )
            == [
                normalized_html_str(
                    """
            <span class="dsr-sections_and_document_references">
                <span class="dsr-section_reference_multiple">
                    <a
                        class="dsr-section_reference"
                        data-document_reference="1"
                        data-is_resolvable="false"
                        data-uri="dsr://unknown____/article__R.%20512%20-%2074__"
                    >
                        articles R. 512 - 74
                    </a>
                    et
                    <a
                        class="dsr-section_reference"
                        data-document_reference="1"
                        data-is_resolvable="false"
                        data-uri="dsr://unknown____/article__R.%20512%2039-1__R.512-39-3"
                    >
                        R. 512 39-1 à R.512-39-3
                    </a>
                </span>
                du
                <a
                    class="dsr-document_reference"
                    data-is_resolvable="false"
                    data-element_id="1"
                    data-uri="dsr://code____Code%20de%20l%27environnement"
                >
                    code de l'environnement
                </a>
            </span>
            """
                )
            ]
        )
