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

from .match_sections_with_documents import match_sections_to_parents

process_match_sections_to_parents = make_testing_function_for_children_list(
    match_sections_to_parents
)


class TestConnectParentSections(unittest.TestCase):

    def test_single_section_to_section(self):
        assert (
            process_match_sections_to_parents(
                """
            <a
                data-spec="section_reference"
            >
                2ème alinéa
            </a>
            de l'
            <a
                data-spec="document_reference"
            >
                article 1
            </a>
            """
            )
            == [
                normalized_html_str(
                    """
                <a
                    data-parent_reference="1"
                    data-spec="section_reference"
                >
                    2ème alinéa
                </a>
                """
                ),
                " de l' ",
                normalized_html_str(
                    """
                <a
                    data-tag_id="1"
                    data-spec="document_reference"
                >
                    article 1
                </a>
                """
                ),
            ]
        )

    def test_single_section_to_document(self):
        assert (
            process_match_sections_to_parents(
                """
                <a
                    data-spec="section_reference"
                >
                    article 5
                </a>
                de l’
                <a
                    data-spec="document_reference"
                >
                    arrêté du
                    <time data-spec="date" datetime="2016-05-23">
                        23 mai 2016
                    </time>
                </a>
                """
            )
            == [
                normalized_html_str(
                    """
                    <a
                        data-parent_reference="1"
                        data-spec="section_reference"
                    >
                        article 5
                    </a>
                    """
                ),
                " de l’ ",
                normalized_html_str(
                    """
                    <a
                        data-tag_id="1"
                        data-spec="document_reference"
                    >
                        arrêté du
                        <time data-spec="date" datetime="2016-05-23">
                            23 mai 2016
                        </time>
                    </a>
                    """
                ),
            ]
        )

    def test_multiple_sections_to_document(self):
        assert (
            process_match_sections_to_parents(
                """
                <a
                    data-group_id="111"
                    data-spec="section_reference"
                >
                    articles R. 512 - 74
                </a>
                et
                <a
                    data-group_id="111"
                    data-spec="section_reference"
                >
                    R. 512 39-1 à R.512-39-3
                </a>
                du
                <a
                    data-spec="document_reference"
                >
                    code de l'environnement
                </a>
                """
            )
            == [
                normalized_html_str(
                    """
                    <a
                        data-group_id="111"
                        data-parent_reference="1"
                        data-spec="section_reference"
                    >
                        articles R. 512 - 74
                    </a>
                    """
                ),
                " et ",
                normalized_html_str(
                    """
                    <a
                        data-parent_reference="1"
                        data-group_id="111"
                        data-spec="section_reference"
                    >
                        R. 512 39-1 à R.512-39-3
                    </a>
                    """
                ),
                " du ",
                normalized_html_str(
                    """
                    <a
                        data-tag_id="1"
                        data-spec="document_reference"
                    >
                        code de l'environnement
                    </a>
                    """
                ),
            ]
        )

    def test_section_to_section_to_document(self):
        assert (
            process_match_sections_to_parents(
                """
                <a
                    data-spec="section_reference"
                >
                    alinéa 3
                </a>
                de l'
                <a
                    data-spec="section_reference"
                >
                    article R121-1
                </a>
                du
                <a
                    data-spec="document_reference"
                >
                    code de l'environnement
                </a>
                """
            )
            == [
                normalized_html_str(
                    """
                    <a
                        data-spec="section_reference"
                        data-parent_reference="1"
                    >
                        alinéa 3
                    </a>
                    """
                ),
                " de l' ",
                normalized_html_str(
                    """
                    <a
                        data-tag_id="1"
                        data-parent_reference="2"
                        data-spec="section_reference"
                    >
                        article R121-1
                    </a>
                    """
                ),
                " du ",
                normalized_html_str(
                    """
                    <a
                        data-tag_id="2"
                        data-spec="document_reference"
                    >
                        code de l'environnement
                    </a>
                    """
                ),
            ]
        )

    def test_section_separated_by_inline_element(self):
        assert (
            process_match_sections_to_parents(
                """
            <a
                data-tag_id="1"
                data-spec="section_reference"
            >
                annexe III
            </a>
            de <br/> l'
            <a
                data-spec="document_reference"
                data-tag_id="2"
            >
                arrêté ministériel du 23 mai 2016
            </a>
            """
            )
            == [
                normalized_html_str(
                    """
                <a
                    data-tag_id="1"
                    data-parent_reference="2"
                    data-spec="section_reference"
                >
                    annexe III
                </a>
                """
                ),
                " de ",
                "<br/>",
                " l' ",
                normalized_html_str(
                    """
                <a
                    data-tag_id="2"
                    data-spec="document_reference"
                >
                    arrêté ministériel du 23 mai 2016
                </a>
                """
                ),
            ]
        )
        # paragraphe 3 de <br/> l'annexe III de l'arrêté <br/> ministériel du 23 mai 2016
