#
# Copyright (c) 2025 Direction générale de la prévention des risques (DGPR).
#
# This file is part of Arrêtify.
# See https://github.com/mte-dgpr/arretify for further info.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import unittest

from arretify.utils.testing import make_testing_function_for_children_list, normalized_html_str

from .sections_detection import parse_section_references

process_children = make_testing_function_for_children_list(parse_section_references)


class TestArticleSingle(unittest.TestCase):
    def test_article_num(self):
        assert process_children("article 4.1.b") == [
            normalized_html_str(
                """
                <a
                    data-spec="section_reference"
                    data-start_num="4.1.b"
                    data-type="article"
                >
                    article 4.1.b
                </a>
                """
            )
        ]
        assert process_children("article 8") == [
            normalized_html_str(
                """
                <a
                    data-spec="section_reference"
                    data-start_num="8"
                    data-type="article"
                >
                    article 8
                </a>
                """
            )
        ]
        assert process_children("article 1er") == [
            normalized_html_str(
                """
                <a
                    data-spec="section_reference"
                    data-start_num="1"
                    data-type="article"
                >
                    article 1er
                </a>
                """
            )
        ]
        assert process_children("article 111è") == [
            normalized_html_str(
                """
                <a
                    data-spec="section_reference"
                    data-start_num="111"
                    data-type="article"
                >
                    article 111è
                </a>
                """
            )
        ]
        assert process_children("article 2ème") == [
            normalized_html_str(
                """
                <a
                    data-spec="section_reference"
                    data-start_num="2"
                    data-type="article"
                >
                    article 2ème
                </a>
                """
            )
        ]

    def test_code_article(self):
        assert process_children("article R. 511-9") == [
            normalized_html_str(
                """
                <a
                    data-spec="section_reference"
                    data-start_num="R511-9"
                    data-type="article"
                >
                    article R. 511-9
                </a>
                """
            )
        ]
        assert process_children("article D.12") == [
            normalized_html_str(
                """
                <a
                    data-spec="section_reference"
                    data-start_num="D12"
                    data-type="article"
                >
                    article D.12
                </a>
                """
            )
        ]
        assert process_children("article L181-3") == [
            normalized_html_str(
                """
                <a
                    data-spec="section_reference"
                    data-start_num="L181-3"
                    data-type="article"
                >
                    article L181-3
                </a>
                """
            )
        ]

    def test_ordinal(self):
        assert process_children("article premier") == [
            normalized_html_str(
                """
                <a
                    data-spec="section_reference"
                    data-start_num="1"
                    data-type="article"
                >
                    article premier
                </a>
                """
            )
        ]
        assert process_children("article quatrième") == [
            normalized_html_str(
                """
                <a
                    data-spec="section_reference"
                    data-start_num="4"
                    data-type="article"
                >
                    article quatrième
                </a>
                """
            )
        ]

    def test_ambiguous_paragraph_use(self):
        assert process_children("Paragraphe L123") == [
            normalized_html_str(
                """
                <a
                    data-spec="section_reference"
                    data-start_num="L123"
                    data-type="article"
                >
                    Paragraphe L123
                </a>
                """
            )
        ]


class TestArticleRange(unittest.TestCase):

    def test_article_num_range(self):
        assert process_children("articles 3 à 11") == [
            normalized_html_str(
                """
                <a
                    data-spec="section_reference"
                    data-end_num="11"
                    data-start_num="3"
                    data-type="article"
                >
                    articles 3 à 11
                </a>
                """
            )
        ]
        assert process_children("articles 6.18.1 à 6.18.7") == [
            normalized_html_str(
                """
                <a
                    data-spec="section_reference"
                    data-end_num="6.18.7"
                    data-start_num="6.18.1"
                    data-type="article"
                >
                    articles 6.18.1 à 6.18.7
                </a>
                """
            )
        ]
        assert process_children("articles 6.18.a à 6.18.c") == [
            normalized_html_str(
                """
                <a
                    data-spec="section_reference"
                    data-end_num="6.18.c"
                    data-start_num="6.18.a"
                    data-type="article"
                >
                    articles 6.18.a à 6.18.c
                </a>
                """
            )
        ]

    def test_ordinal_range(self):
        assert process_children("de l'article premier à l'article troisième") == [
            "de l'",
            normalized_html_str(
                """
                <a
                    data-spec="section_reference"
                    data-end_num="3"
                    data-start_num="1"
                    data-type="article"
                >
                    article premier à l'article troisième
                </a>
                """
            ),
        ]
        assert process_children("des articles second à 10ème") == [
            "des ",
            normalized_html_str(
                """
                <a
                    data-spec="section_reference"
                    data-end_num="10"
                    data-start_num="2"
                    data-type="article"
                >
                    articles second à 10ème
                </a>
                """
            ),
        ]

    def test_code_article_range(self):
        assert process_children("de l'article R. 511-9 à l'article D.512") == [
            "de l'",
            normalized_html_str(
                """
                <a
                    data-spec="section_reference"
                    data-end_num="D512"
                    data-start_num="R511-9"
                    data-type="article"
                >
                    article R. 511-9 à l'article D.512
                </a>
                """
            ),
        ]
        assert process_children("l' article R.543-137 à R.543-151") == [
            "l' ",
            normalized_html_str(
                """
                <a
                    data-spec="section_reference"
                    data-end_num="R543-151"
                    data-start_num="R543-137"
                    data-type="article"
                >
                    article R.543-137 à R.543-151
                </a>
                """
            ),
        ]


class TestArticlePlural(unittest.TestCase):

    def test_article_num(self):
        assert process_children("articles 5.1.9, 9.2.1, 10.2.1 et 10.2.5") == [
            normalized_html_str(
                """
                <a
                    data-spec="section_reference"
                    data-group_id="1"
                    data-start_num="5.1.9"
                    data-type="article"
                >
                    articles 5.1.9
                </a>
            """
            ),
            ", ",
            normalized_html_str(
                """
                <a
                    data-spec="section_reference"
                    data-group_id="1"
                    data-start_num="9.2.1"
                    data-type="article"
                >
                    9.2.1
                </a>
            """
            ),
            ", ",
            normalized_html_str(
                """
                <a
                    data-spec="section_reference"
                    data-group_id="1"
                    data-start_num="10.2.1"
                    data-type="article"
                >
                    10.2.1
                </a>
            """
            ),
            " et ",
            normalized_html_str(
                """
                <a
                    data-spec="section_reference"
                    data-group_id="1"
                    data-start_num="10.2.5"
                    data-type="article"
                >
                    10.2.5
                </a>
            """
            ),
        ]

    def test_ordinal(self):
        assert process_children("articles premier,9.a") == [
            normalized_html_str(
                """
                <a
                    data-spec="section_reference"
                    data-group_id="1"
                    data-start_num="1"
                    data-type="article"
                >
                    articles premier
                </a>
            """
            ),
            ",",
            normalized_html_str(
                """
                <a
                    data-spec="section_reference"
                    data-group_id="1"
                    data-start_num="9.a"
                    data-type="article"
                >
                    9.a
                </a>
            """
            ),
        ]

        assert process_children("articles premier et second") == [
            normalized_html_str(
                """
                <a
                    data-spec="section_reference"
                    data-group_id="1"
                    data-start_num="1"
                    data-type="article"
                >
                    articles premier
                </a>
            """
            ),
            " et ",
            normalized_html_str(
                """
                <a
                    data-spec="section_reference"
                    data-group_id="1"
                    data-start_num="2"
                    data-type="article"
                >
                    second
                </a>
            """
            ),
        ]

    def test_article_code(self):
        assert process_children("articles R. 511-9 et L. 111") == [
            normalized_html_str(
                """
                <a
                    data-spec="section_reference"
                    data-group_id="1"
                    data-start_num="R511-9"
                    data-type="article"
                >
                    articles R. 511-9
                </a>
            """
            ),
            " et ",
            normalized_html_str(
                """
                <a
                    data-spec="section_reference"
                    data-group_id="1"
                    data-start_num="L111"
                    data-type="article"
                >
                    L. 111
                </a>
            """
            ),
        ]

    def test_article_range(self):
        assert process_children("articles R. 512 - 74 et R. 512-39-1 à R.512-39-3") == [
            normalized_html_str(
                """
                <a
                    data-spec="section_reference"
                    data-group_id="1"
                    data-start_num="R512-74"
                    data-type="article"
                >
                    articles R. 512 - 74
                </a>
            """
            ),
            " et ",
            normalized_html_str(
                """
                <a
                    data-spec="section_reference"
                    data-group_id="1"
                    data-end_num="R512-39-3"
                    data-start_num="R512-39-1"
                    data-type="article"
                >
                    R. 512-39-1 à R.512-39-3
                </a>
            """
            ),
        ]

    def test_range_first(self):
        assert process_children("articles R.541-49 à R.541-64 et R.541-79") == [
            normalized_html_str(
                """
                <a
                    data-spec="section_reference"
                    data-group_id="1"
                    data-end_num="R541-64"
                    data-start_num="R541-49"
                    data-type="article"
                >
                    articles R.541-49 à R.541-64
                </a>
            """
            ),
            " et ",
            normalized_html_str(
                """
                <a
                    data-spec="section_reference"
                    data-group_id="1"
                    data-start_num="R541-79"
                    data-type="article"
                >
                    R.541-79
                </a>
            """
            ),
        ]


class TestAlineaSingle(unittest.TestCase):

    def test_alinea_num_before(self):
        assert process_children("2ème alinéa") == [
            normalized_html_str(
                """
            <a
                data-spec="section_reference"
                data-start_num="2"
                data-type="alinea"
            >
                2ème alinéa
            </a>
            """
            )
        ]

    def test_alinea_num_after(self):
        assert process_children("alinéa 3") == [
            normalized_html_str(
                """
            <a
                data-spec="section_reference"
                data-start_num="3"
                data-type="alinea"
            >
                alinéa 3
            </a>
            """
            )
        ]
        assert process_children("alinéa second") == [
            normalized_html_str(
                """
            <a
                data-spec="section_reference"
                data-start_num="2"
                data-type="alinea"
            >
                alinéa second
            </a>
            """
            )
        ]
        assert process_children("alinéa neuvième") == [
            normalized_html_str(
                """
            <a
                data-spec="section_reference"
                data-start_num="9"
                data-type="alinea"
            >
                alinéa neuvième
            </a>
            """
            )
        ]


class TestAlineaRange(unittest.TestCase):

    def test_alinea_num_range(self):
        assert process_children("alinéas 3 à 5") == [
            normalized_html_str(
                """
                <a
                    data-spec="section_reference"
                    data-end_num="5"
                    data-start_num="3"
                    data-type="alinea"
                >
                    alinéas 3 à 5
                </a>
            """
            )
        ]

    def test_alinea_num_range_with_ordinal(self):
        assert process_children("alinéas premier à troisième") == [
            normalized_html_str(
                """
                <a
                    data-spec="section_reference"
                    data-end_num="3"
                    data-start_num="1"
                    data-type="alinea"
                >
                    alinéas premier à troisième
                </a>
            """
            )
        ]


class TestAlineaMultiple(unittest.TestCase):

    def test_alinea_list(self):
        assert process_children("Les alinéas 3 et 4") == [
            "Les ",
            normalized_html_str(
                """
                <a
                    data-spec="section_reference"
                    data-group_id="1"
                    data-start_num="3"
                    data-type="alinea"
                >
                    alinéas 3
                </a>
            """
            ),
            " et ",
            normalized_html_str(
                """
                <a
                    data-spec="section_reference"
                    data-group_id="1"
                    data-start_num="4"
                    data-type="alinea"
                >
                    4
                </a>
            """
            ),
        ]


class TestUnknownSingle(unittest.TestCase):

    def test_unknown_num(self):
        assert process_children("paragraphe 3") == [
            normalized_html_str(
                """
                <a
                    data-spec="section_reference"
                    data-start_num="3"
                    data-type="unknown"
                >
                    paragraphe 3
                </a>
                """
            )
        ]

    def test_paragraph_symbol(self):
        assert process_children("Dans le § a.4") == [
            "Dans le ",
            normalized_html_str(
                """
                <a
                    data-spec="section_reference"
                    data-start_num="a.4"
                    data-type="unknown"
                >
                    § a.4
                </a>
            """
            ),
        ]


class TestUnknownRange(unittest.TestCase):

    def test_unknown_num_range(self):
        assert process_children("paragraphes 3 à 5") == [
            normalized_html_str(
                """
                <a
                    data-spec="section_reference"
                    data-end_num="5"
                    data-start_num="3"
                    data-type="unknown"
                >
                    paragraphes 3 à 5
                </a>
            """
            )
        ]


class TestUnknownMultiple(unittest.TestCase):

    def test_paragraphe_list(self):
        assert process_children("Les paragraphes 3è, 5 et quatrième") == [
            "Les ",
            normalized_html_str(
                """
                <a
                    data-spec="section_reference"
                    data-group_id="1"
                    data-start_num="3"
                    data-type="unknown"
                >
                    paragraphes 3è
                </a>
            """
            ),
            ", ",
            normalized_html_str(
                """
                <a
                    data-spec="section_reference"
                    data-group_id="1"
                    data-start_num="5"
                    data-type="unknown"
                >
                    5
                </a>
            """
            ),
            " et ",
            normalized_html_str(
                """
                <a
                    data-spec="section_reference"
                    data-group_id="1"
                    data-start_num="4"
                    data-type="unknown"
                >
                    quatrième
                </a>
            """
            ),
        ]


class TestAppendixSingle(unittest.TestCase):

    def test_appendix_num(self):
        assert process_children("annexe 1") == [
            normalized_html_str(
                """
                <a
                    data-spec="section_reference"
                    data-start_num="1"
                    data-type="annexe"
                >
                    annexe 1
                </a>
                """
            )
        ]

    def test_appendix_roman(self):
        assert process_children("annexe IV") == [
            normalized_html_str(
                """
                <a
                    data-spec="section_reference"
                    data-start_num="4"
                    data-type="annexe"
                >
                    annexe IV
                </a>
                """
            )
        ]

    def test_appendix_no_number(self):
        assert process_children("en annexe de blabla") == [
            "en ",
            normalized_html_str(
                """
                <a
                    data-spec="section_reference"
                    data-type="annexe"
                >
                    annexe
                </a>
                """
            ),
            " de blabla",
        ]
