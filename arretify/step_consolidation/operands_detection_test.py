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

from arretify.semantic_tag_specs import OperationSpec
from arretify.utils.html_semantic import css_selector
from arretify.utils.testing import create_document_context, normalized_html_str

from .operands_detection import resolve_references_and_operands


class TestParseOperations(unittest.TestCase):

    def test_several_references_no_operand(self):
        # Arrange
        document_context = create_document_context(
            normalized_html_str(
                """
                <div data-spec="alinea">
                    Les
                    <a
                        data-group_id="11"
                        data-parent_reference="123"
                        data-spec="section_reference"
                    >
                        paragraphes 3
                    </a>
                    et
                    <a
                        data-group_id="11"
                        data-parent_reference="123"
                        data-spec="section_reference"
                    >
                        4
                    </a>
                    de l'
                    <a
                        data-tag_id="123"
                        data-parent_reference="456"
                        data-spec="section_reference"
                    >
                        article 8.5.1.1
                    </a>
                    de l'
                    <a
                        data-spec="document_reference"
                        data-tag_id="456"
                    >
                        arrêté préfectoral du
                        <time data-spec="date" datetime="2008-12-10">
                            10 décembre 2008
                        </time>
                    </a>
                    <span
                        data-direction="rtl"
                        data-keyword="supprimés"
                        data-operand=""
                        data-operation_type="delete"
                        data-spec="operation"
                    >
                        sont
                        <b>
                            supprimés
                        </b>
                    </span>
                </div>
                """  # noqa: E501
            )
        )
        tag = document_context.protected_soup.select_one(css_selector(OperationSpec))

        # Act
        resolve_references_and_operands(document_context, tag)

        # Assert
        assert str(document_context.protected_soup) == normalized_html_str(
            # Check that tag_id was added to both references, and that the references were
            # added to the operation
            """
            <div data-spec="alinea">
                Les
                <a
                    data-tag_id="1"
                    data-group_id="11"
                    data-parent_reference="123"
                    data-spec="section_reference"
                >
                    paragraphes 3
                </a>
                et
                <a
                    data-tag_id="2"
                    data-group_id="11"
                    data-parent_reference="123"
                    data-spec="section_reference"
                >
                    4
                </a>
                de l'
                <a
                    data-tag_id="123"
                    data-parent_reference="456"
                    data-spec="section_reference"
                >
                    article 8.5.1.1
                </a>
                de l'
                <a
                    data-tag_id="456"
                    data-spec="document_reference"
                >
                    arrêté préfectoral du
                    <time data-spec="date" datetime="2008-12-10">
                        10 décembre 2008
                    </time>
                </a>
                <span
                    data-direction="rtl"
                    data-keyword="supprimés"
                    data-operand=""
                    data-operation_type="delete"
                    data-references="1,2"
                    data-spec="operation"
                >
                    sont
                    <b>
                        supprimés
                    </b>
                </span>
            </div>
            """  # noqa: E501
        )

    def test_one_reference_one_operand(self):
        # Arrange
        document_context = create_document_context(
            normalized_html_str(
                """
                <div data-spec="alinea">
                    La dernière phrase de l'
                    <a
                        data-parent_reference="123"
                        data-spec="section_reference"
                    >
                        article 8.1.1.2
                    </a>
                    de l'
                    <a
                        data-spec="document_reference"
                        data-tag_id="123"
                    >
                        arrêté préfectoral du
                        <time
                            datetime="2008-12-10"
                            data-spec="date"
                        >
                                10 décembre 2008
                        </time>
                    </a>
                    <span
                        data-direction="rtl"
                        data-has_operand="true"
                        data-keyword="remplacée"
                        data-operand=""
                        data-operation_type="replace"
                        data-spec="operation"
                    >
                        est
                        <b>
                            remplacée
                        </b>
                        par la disposition suivante :
                    </span>
                    <q>
                        Un relevé hebdomadaire de chacun des compteurs d'eau est réalisé par l'exploitant
                    </q>
                    .
                </div>
                """  # noqa: E501
            )
        )
        tag = document_context.protected_soup.select_one(css_selector(OperationSpec))

        # Act
        resolve_references_and_operands(document_context, tag)

        # Assert
        assert str(document_context.protected_soup) == normalized_html_str(
            """
            <div data-spec="alinea">
                La dernière phrase de l'
                <a
                    data-tag_id="1"
                    data-parent_reference="123"
                    data-spec="section_reference"
                >
                    article 8.1.1.2
                </a>
                de l'
                <a
                    data-tag_id="123"
                    data-spec="document_reference"
                >
                    arrêté préfectoral du
                    <time
                        datetime="2008-12-10"
                        data-spec="date"
                    >
                            10 décembre 2008
                    </time>
                </a>
                <span
                    data-direction="rtl"
                    data-has_operand="true"
                    data-keyword="remplacée"
                    data-operand="2"
                    data-operation_type="replace"
                    data-references="1"
                    data-spec="operation"
                >
                    est
                    <b>
                        remplacée
                    </b>
                    par la disposition suivante :
                </span>
                <q
                    data-tag_id="2"
                >
                    Un relevé hebdomadaire de chacun des compteurs d'eau est réalisé par l'exploitant
                </q>
                .
            </div>
            """  # noqa: E501
        )

    def test_with_single_document_reference(self):
        # Arrange
        document_context = create_document_context(
            normalized_html_str(
                """
                <div data-spec="alinea">
                    Les prescriptions de l'
                    <a data-spec="document_reference">
                        arrêté préfectoral du
                        <time
                            datetime="2008-12-10"
                            data-spec="date"
                        >
                                10 décembre 2008
                        </time>
                    </a>
                    <span
                        data-direction="rtl"
                        data-keyword="abrogées"
                        data-operand=""
                        data-operation_type="delete"
                        data-spec="operation"
                    >
                        sont
                        <b>
                            abrogées
                        </b>
                        .
                    </span>
                </div>
                """  # noqa: E501
            )
        )
        tag = document_context.protected_soup.select_one(css_selector(OperationSpec))

        # Act
        resolve_references_and_operands(document_context, tag)

        # Assert
        assert str(document_context.protected_soup) == normalized_html_str(
            """
            <div data-spec="alinea">
                Les prescriptions de l'
                <a
                    data-tag_id="1"
                    data-spec="document_reference"
                >
                    arrêté préfectoral du
                    <time
                        datetime="2008-12-10"
                        data-spec="date"
                    >
                            10 décembre 2008
                    </time>
                </a>
                <span
                    data-direction="rtl"
                    data-keyword="abrogées"
                    data-operand=""
                    data-operation_type="delete"
                    data-references="1"
                    data-spec="operation"
                >
                    sont
                    <b>
                        abrogées
                    </b>
                    .
                </span>
            </div>
            """  # noqa: E501
        )

    def test_with_inline_tag_between_operands(self):
        # Arrange
        document_context = create_document_context(
            normalized_html_str(
                """
                <div data-spec="alinea">
                    Les dispositions de l'
                    <a data-spec="document_reference">
                        arrêté préfectoral du
                        <time
                            datetime="2008-12-10"
                            data-spec="date"
                        >
                                10 décembre 2008
                        </time>
                    </a>
                    <a data-spec="page_separator"></a>
                    <span
                        data-direction="rtl"
                        data-has_operand="true"
                        data-keyword="remplacées"
                        data-operand=""
                        data-operation_type="replace"
                        data-spec="operation"
                    >
                        sont
                        <b>
                            remplacées
                        </b>
                        par la disposition suivante :
                    </span>
                    <a data-spec="page_separator"></a>
                    <q>
                        Un relevé hebdomadaire de chacun des compteurs d'eau est réalisé par l'exploitant
                    </q>
                </div>
                """  # noqa: E501
            )
        )
        tag = document_context.protected_soup.select_one(css_selector(OperationSpec))

        # Act
        resolve_references_and_operands(document_context, tag)

        # Assert
        assert str(document_context.protected_soup) == normalized_html_str(
            """
            <div data-spec="alinea">
                Les dispositions de l'
                <a
                    data-tag_id="1"
                    data-spec="document_reference"
                >
                    arrêté préfectoral du
                    <time
                        datetime="2008-12-10"
                        data-spec="date"
                    >
                            10 décembre 2008
                    </time>
                </a>
                <a data-spec="page_separator"></a>
                <span
                    data-direction="rtl"
                    data-has_operand="true"
                    data-keyword="remplacées"
                    data-operand="2"
                    data-operation_type="replace"
                    data-references="1"
                    data-spec="operation"
                >
                    sont
                    <b>
                        remplacées
                    </b>
                    par la disposition suivante :
                </span>
                <a data-spec="page_separator"></a>
                <q data-tag_id="2">
                    Un relevé hebdomadaire de chacun des compteurs d'eau est réalisé par l'exploitant
                </q>
            </div>
            """  # noqa: E501
        )
