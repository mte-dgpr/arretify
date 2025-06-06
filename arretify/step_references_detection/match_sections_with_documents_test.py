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

from bs4 import BeautifulSoup

from arretify.utils.testing import (
    make_testing_function_for_children_list,
    normalized_html_str,
)
from arretify.utils import html
from .match_sections_with_documents import match_sections_to_parents, build_reference_tree

process_sections_and_documents = make_testing_function_for_children_list(match_sections_to_parents)


class TestConnectParentSections(unittest.TestCase):
    def setUp(self):
        html._ELEMENT_ID_COUNTER = 0
        html._GROUP_ID_COUNTER = 0

    def test_single_section_to_section(self):
        assert (
            process_sections_and_documents(
                """
            <a
                class="dsr-section_reference"
                data-is_resolvable="false"
                data-uri="dsr://unknown____/alinea__2__"
            >
                2ème alinéa
            </a>
            de l'
            <a
                class="dsr-document_reference"
                data-is_resolvable="false"
                data-uri="dsr://unknown____/article__1__"
            >
                article 1
            </a>
            """
            )
            == [
                normalized_html_str(
                    """
                <a
                    class="dsr-section_reference"
                    data-parent_reference="1"
                    data-is_resolvable="false"
                    data-uri="dsr://unknown____/alinea__2__"
                >
                    2ème alinéa
                </a>
                """
                ),
                " de l' ",
                normalized_html_str(
                    """
                <a
                    class="dsr-document_reference"
                    data-element_id="1"
                    data-is_resolvable="false"
                    data-uri="dsr://unknown____/article__1__"
                >
                    article 1
                </a>
                """
                ),
            ]
        )

    def test_single_section_to_document(self):
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
                    <a
                        class="dsr-section_reference"
                        data-parent_reference="1"
                        data-is_resolvable="false"
                        data-uri="dsr://unknown____/article__5__"
                    >
                        article 5
                    </a>
                    """
                ),
                " de l’ ",
                normalized_html_str(
                    """
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
                    """
                ),
            ]
        )

    def test_multiple_sections_to_document(self):
        assert (
            process_sections_and_documents(
                """
                <a
                    class="dsr-section_reference"
                    data-group_id="111"
                    data-is_resolvable="false"
                    data-uri="dsr://unknown____/article__R.%20512%20-%2074__"
                >
                    articles R. 512 - 74
                </a>
                et
                <a
                    class="dsr-section_reference"
                    data-group_id="111"
                    data-is_resolvable="false"
                    data-uri="dsr://unknown____/article__R.%20512%2039-1__R.512-39-3"
                >
                    R. 512 39-1 à R.512-39-3
                </a>
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
                    <a
                        class="dsr-section_reference"
                        data-parent_reference="1"
                        data-group_id="111"
                        data-is_resolvable="false"
                        data-uri="dsr://unknown____/article__R.%20512%20-%2074__"
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
                        data-parent_reference="1"
                        data-group_id="111"
                        data-is_resolvable="false"
                        data-uri="dsr://unknown____/article__R.%20512%2039-1__R.512-39-3"
                    >
                        R. 512 39-1 à R.512-39-3
                    </a>
                    """
                ),
                " du ",
                normalized_html_str(
                    """
                    <a
                        class="dsr-document_reference"
                        data-is_resolvable="false"
                        data-element_id="1"
                        data-uri="dsr://code____Code%20de%20l%27environnement"
                    >
                        code de l'environnement
                    </a>
                    """
                ),
            ]
        )

    def test_section_to_section_to_document(self):
        assert (
            process_sections_and_documents(
                """
                <a
                    class="dsr-section_reference"
                    data-is_resolvable="false"
                    data-uri="dsr://unknown____/alinea__3__"
                >
                    alinéa 3
                </a>
                de l'
                <a
                    class="dsr-section_reference"
                    data-is_resolvable="false"
                    data-uri="dsr://unknown____/article__R121-1__"
                >
                    article R121-1
                </a>
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
                    <a
                        class="dsr-section_reference"
                        data-is_resolvable="false"
                        data-parent_reference="1"
                        data-uri="dsr://unknown____/alinea__3__"
                    >
                        alinéa 3
                    </a>
                    """
                ),
                " de l' ",
                normalized_html_str(
                    """
                    <a
                        class="dsr-section_reference"
                        data-element_id="1"
                        data-is_resolvable="false"
                        data-parent_reference="2"
                        data-uri="dsr://unknown____/article__R121-1__"
                    >
                        article R121-1
                    </a>
                    """
                ),
                " du ",
                normalized_html_str(
                    """
                    <a
                        class="dsr-document_reference"
                        data-element_id="2"
                        data-is_resolvable="false"
                        data-uri="dsr://code____Code%20de%20l%27environnement"
                    >
                        code de l'environnement
                    </a>
                    """
                ),
            ]
        )


class TestBuildReferenceTree(unittest.TestCase):

    def test_get_all_branches(self):
        # Arrange
        soup = BeautifulSoup(
            """
            <div>
                <a
                    class="dsr-section_reference"
                    data-element_id="1"
                    data-parent_reference="3"
                >
                    Section 1.1
                </a>
                <a
                    class="dsr-section_reference"
                    data-element_id="2"
                    data-parent_reference="3"
                >
                    Section 1.2
                </a>
                <a
                    class="dsr-section_reference"
                    data-element_id="3"
                    data-parent_reference="4"
                >
                    Section 1
                </a>
                <a
                    class="dsr-document_reference"
                    data-element_id="4"
                >
                    Some Document
                </a>
            </div>
            """,
            features="html.parser",
        )
        section_reference_tag = soup.select_one("a[data-element_id='3']")

        # Act
        branches = build_reference_tree(section_reference_tag)

        # Assert
        assert len(branches) == 2
        assert [tag["data-element_id"] for tag in branches[0]] == ["4", "3", "1"]
        assert [tag["data-element_id"] for tag in branches[1]] == ["4", "3", "2"]

    def test_leaf_no_element_id(self):
        # Arrange
        soup = BeautifulSoup(
            """
            <div>
                <a
                    id="tag1"
                    class="dsr-section_reference"
                    data-parent_reference="1"
                >
                    Section 1.1
                </a>
                <a
                    id="tag2"
                    class="dsr-section_reference"
                    data-element_id="1"
                >
                    Section 1
                </a>
            </div>
            """,
            features="html.parser",
        )
        section_reference_tag = soup.select_one(".dsr-section_reference")

        # Act
        branches = build_reference_tree(section_reference_tag)

        # Assert
        assert len(branches) == 1
        assert [tag["id"] for tag in branches[0]] == ["tag2", "tag1"]
