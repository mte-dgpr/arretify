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

from arretify.utils.testing import (
    make_testing_function_for_children_list,
    normalized_html_str,
)
from arretify.utils import html
from .sections_detection import parse_section_references

process_children = make_testing_function_for_children_list(parse_section_references)


class TestArticleRange(unittest.TestCase):

    def test_article_num(self):
        assert process_children("article 4.1.b") == [
            normalized_html_str(
                """
                <a
                    class="dsr-section_reference"
                    data-uri="dsr://unknown____/article__4.1.b__"
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
                    class="dsr-section_reference"
                    data-uri="dsr://unknown____/article__8__"
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
                    class="dsr-section_reference"
                    data-uri="dsr://unknown____/article__1__"
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
                    class="dsr-section_reference"
                    data-uri="dsr://unknown____/article__111__"
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
                    class="dsr-section_reference"
                    data-uri="dsr://unknown____/article__2__"
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
                    class="dsr-section_reference"
                    data-uri="dsr://unknown____/article__R511-9__"
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
                    class="dsr-section_reference"
                    data-uri="dsr://unknown____/article__D12__"
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
                    class="dsr-section_reference"
                    data-uri="dsr://unknown____/article__L181-3__"
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
                    class="dsr-section_reference"
                    data-uri="dsr://unknown____/article__1__"
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
                    class="dsr-section_reference"
                    data-uri="dsr://unknown____/article__4__"
                >
                    article quatrième
                </a>
                """
            )
        ]

    def test_article_num_range(self):
        assert process_children("articles 3 à 11") == [
            normalized_html_str(
                """
                <a
                    class="dsr-section_reference"
                    data-uri="dsr://unknown____/article__3__11"
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
                    class="dsr-section_reference"
                    data-uri="dsr://unknown____/article__6.18.1__6.18.7"
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
                    class="dsr-section_reference"
                    data-uri="dsr://unknown____/article__6.18.a__6.18.c"
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
                    class="dsr-section_reference"
                    data-uri="dsr://unknown____/article__1__3"
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
                    class="dsr-section_reference"
                    data-uri="dsr://unknown____/article__2__10"
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
                    class="dsr-section_reference"
                    data-uri="dsr://unknown____/article__R511-9__D512"
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
                    class="dsr-section_reference"
                    data-uri="dsr://unknown____/article__R543-137__R543-151"
                >
                    article R.543-137 à R.543-151
                </a>
                """
            ),
        ]


class TestArticleSingle(unittest.TestCase):
    def test_ambiguous_paragraph_use(self):
        assert process_children("Paragraphe 4.28") == [
            normalized_html_str(
                """
                <a
                    class="dsr-section_reference"
                    data-uri="dsr://unknown____/article__4.28__"
                >
                    Paragraphe 4.28
                </a>
                """
            )
        ]


class TestArticlePlural(unittest.TestCase):

    def setUp(self):
        html._GROUP_ID_COUNTER = 0

    def test_article_num(self):
        assert process_children("articles 5.1.9, 9.2.1, 10.2.1 et 10.2.5") == [
            normalized_html_str(
                """
                <a
                    class="dsr-section_reference"
                    data-group_id="1"
                    data-uri="dsr://unknown____/article__5.1.9__"
                >
                    articles 5.1.9
                </a>
            """
            ),
            ", ",
            normalized_html_str(
                """
                <a
                    class="dsr-section_reference"
                    data-group_id="1"
                    data-uri="dsr://unknown____/article__9.2.1__"
                >
                    9.2.1
                </a>
            """
            ),
            ", ",
            normalized_html_str(
                """
                <a
                    class="dsr-section_reference"
                    data-group_id="1"
                    data-uri="dsr://unknown____/article__10.2.1__"
                >
                    10.2.1
                </a>
            """
            ),
            " et ",
            normalized_html_str(
                """
                <a
                    class="dsr-section_reference"
                    data-group_id="1"
                    data-uri="dsr://unknown____/article__10.2.5__"
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
                    class="dsr-section_reference"
                    data-group_id="1"
                    data-uri="dsr://unknown____/article__1__"
                >
                    articles premier
                </a>
            """
            ),
            ",",
            normalized_html_str(
                """
                <a
                    class="dsr-section_reference"
                    data-group_id="1"
                    data-uri="dsr://unknown____/article__9.a__"
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
                    class="dsr-section_reference"
                    data-group_id="2"
                    data-uri="dsr://unknown____/article__1__"
                >
                    articles premier
                </a>
            """
            ),
            " et ",
            normalized_html_str(
                """
                <a
                    class="dsr-section_reference"
                    data-group_id="2"
                    data-uri="dsr://unknown____/article__2__"
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
                    class="dsr-section_reference"
                    data-group_id="1"
                    data-uri="dsr://unknown____/article__R511-9__"
                >
                    articles R. 511-9
                </a>
            """
            ),
            " et ",
            normalized_html_str(
                """
                <a
                    class="dsr-section_reference"
                    data-group_id="1"
                    data-uri="dsr://unknown____/article__L111__"
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
                    class="dsr-section_reference"
                    data-group_id="1"
                    data-uri="dsr://unknown____/article__R512-74__"
                >
                    articles R. 512 - 74
                </a>
            """
            ),
            " et ",
            normalized_html_str(
                """
                <a
                    class="dsr-section_reference"
                    data-group_id="1"
                    data-uri="dsr://unknown____/article__R512-39-1__R512-39-3"
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
                    class="dsr-section_reference"
                    data-group_id="1"
                    data-uri="dsr://unknown____/article__R541-49__R541-64"
                >
                    articles R.541-49 à R.541-64
                </a>
            """
            ),
            " et ",
            normalized_html_str(
                """
                <a
                    class="dsr-section_reference"
                    data-group_id="1"
                    data-uri="dsr://unknown____/article__R541-79__"
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
                class="dsr-section_reference"
                data-uri="dsr://unknown____/alinea__2__"
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
                class="dsr-section_reference"
                data-uri="dsr://unknown____/alinea__3__"
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
                class="dsr-section_reference"
                data-uri="dsr://unknown____/alinea__2__"
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
                class="dsr-section_reference"
                data-uri="dsr://unknown____/alinea__9__"
            >
                alinéa neuvième
            </a>
            """
            )
        ]


class TestAlineaMultiple(unittest.TestCase):

    def setUp(self):
        html._GROUP_ID_COUNTER = 0

    def test_alinea_list(self):
        assert process_children("Les alinéas 3 et 4") == [
            "Les ",
            normalized_html_str(
                """
                <a
                    class="dsr-section_reference"
                    data-group_id="1"
                    data-uri="dsr://unknown____/alinea__3__"
                >
                    alinéas 3
                </a>
            """
            ),
            " et ",
            normalized_html_str(
                """
                <a
                    class="dsr-section_reference"
                    data-group_id="1"
                    data-uri="dsr://unknown____/alinea__4__"
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
                    class="dsr-section_reference"
                    data-uri="dsr://unknown____/unknown__3__"
                >
                    paragraphe 3
                </a>
                """
            )
        ]


class TestUnknownMultiple(unittest.TestCase):

    def setUp(self):
        html._GROUP_ID_COUNTER = 0

    def test_paragraphe_list(self):
        assert process_children("Les paragraphes 3è, 5 et quatrième") == [
            "Les ",
            normalized_html_str(
                """
                <a
                    class="dsr-section_reference"
                    data-group_id="1"
                    data-uri="dsr://unknown____/unknown__3__"
                >
                    paragraphes 3è
                </a>
            """
            ),
            ", ",
            normalized_html_str(
                """
                <a
                    class="dsr-section_reference"
                    data-group_id="1"
                    data-uri="dsr://unknown____/unknown__5__"
                >
                    5
                </a>
            """
            ),
            " et ",
            normalized_html_str(
                """
                <a
                    class="dsr-section_reference"
                    data-group_id="1"
                    data-uri="dsr://unknown____/unknown__4__"
                >
                    quatrième
                </a>
            """
            ),
        ]


# Détection de référence de paragraphe
class TestParagraphReference(unittest.TestCase):

    def test_paragraph_reference(self):
        assert process_children("Paragraphe 4.28") == [
            normalized_html_str(
                """
                <a
                    class="dsr-section_reference"
                    data-is_resolvable="false"
                    data-uri="dsr://unknown____/alinea__4.28__"
                >
                    Paragraphe 4.28
                </a>
                """
            )
        ]
