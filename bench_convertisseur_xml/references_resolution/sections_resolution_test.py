import unittest

from bench_convertisseur_xml.utils.testing import (
    make_testing_function_for_children_list,
    normalized_html_str,
)
from .sections_resolution import match_sections_with_documents

process_sections_and_documents = make_testing_function_for_children_list(
    match_sections_with_documents
)


class TestResolveSectionsDocuments(unittest.TestCase):
    def test_unknown_arrete(self):
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
                    data-is_resolvable="false"
                    data-uri="dsr://arrete___2016-05-23_/article__5__"
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
            </span>
            """
                )
            ]
        )

    def test_code(self):
        assert (
            process_sections_and_documents(
                """
            <a
                class="dsr-section_reference"
                data-is_resolvable="false"
                data-uri="dsr://unknown____/article__R.181-48__"
            >
                article R.181-48
            </a>
            et suivants du
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
                <a
                    class="dsr-section_reference"
                    data-is_resolvable="false"
                    data-uri="dsr://code____Code%20de%20l%27environnement/article__R.181-48__"
                >
                    article R.181-48
                </a>
                et suivants du
                <a
                    class="dsr-document_reference"
                    data-is_resolvable="false"
                    data-uri="dsr://code____Code%20de%20l%27environnement"
                >
                    code de l'environnement
                </a>
            </span>
            """
                )
            ]
        )

    def test_too_many_words_connector(self):
        assert (
            process_sections_and_documents(
                """
                <a
                    class="dsr-section_reference"
                    data-is_resolvable="false"
                    data-uri="dsr://unknown____/article__R.181-48__"
                >
                    article R.181-48
                </a>
                et suivants, parce que bla bla bla du
                <a
                    class="dsr-document_reference"
                    data-is_resolvable="false"
                    data-uri="dsr://code____Code%20de%20l%27environnement"
                >
                    code de l'environnement
                </a>
                """
            )[0]
            == normalized_html_str(
                """
            <a
                class="dsr-section_reference"
                data-is_resolvable="false"
                data-uri="dsr://unknown____/article__R.181-48__"
            >
                article R.181-48
            </a>
            """
            )
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
                        data-is_resolvable="false"
                        data-uri="dsr://code____Code%20de%20l%27environnement/article__R.%20512%20-%2074__"
                    >
                        articles R. 512 - 74
                    </a>
                    et
                    <a
                        class="dsr-section_reference"
                        data-is_resolvable="false"
                        data-uri="dsr://code____Code%20de%20l%27environnement/article__R.%20512%2039-1__R.512-39-3"
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
            </span>
            """
                )
            ]
        )
