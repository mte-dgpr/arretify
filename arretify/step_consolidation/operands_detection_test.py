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

from arretify.semantic_tag_schemas import OPERATION_SCHEMA
from arretify.utils.html_semantic import css_selector
from arretify.utils.testing import normalized_html_str, create_document_context

from .operands_detection import resolve_references_and_operands


class TestParseOperations(unittest.TestCase):

    def test_several_references_no_operand(self):
        # Arrange
        document_context = create_document_context(
            normalized_html_str(
                """
                <div data-schema="alinea">
                    Les
                    <a
                        data-group_id="11"
                        data-parent_reference="123"
                        data-schema="section_reference"
                    >
                        paragraphes 3
                    </a>
                    et
                    <a
                        data-group_id="11"
                        data-parent_reference="123"
                        data-schema="section_reference"
                    >
                        4
                    </a>
                    de l'
                    <a
                        data-element_id="123"
                        data-parent_reference="456"
                        data-schema="section_reference"
                    >
                        article 8.5.1.1
                    </a>
                    de l'
                    <a
                        data-schema="document_reference"
                        data-element_id="456"
                    >
                        arrêté préfectoral du
                        <time data-schema="date" datetime="2008-12-10">
                            10 décembre 2008
                        </time>
                    </a>
                    <span
                        data-direction="rtl"
                        data-has_operand=""
                        data-keyword="supprimés"
                        data-operand=""
                        data-operation_type="delete"
                        data-schema="operation"
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
        tag = document_context.soup.select_one(css_selector(OPERATION_SCHEMA))

        # Act
        resolve_references_and_operands(document_context, tag)

        # Assert
        assert str(document_context.soup) == normalized_html_str(
            # Check that element_id was added to both references, and that the references were
            # added to the operation
            """
            <div data-schema="alinea">
                Les
                <a
                    data-element_id="1"
                    data-group_id="11"
                    data-parent_reference="123"
                    data-schema="section_reference"
                >
                    paragraphes 3
                </a>
                et
                <a
                    data-element_id="2"
                    data-group_id="11"
                    data-parent_reference="123"
                    data-schema="section_reference"
                >
                    4
                </a>
                de l'
                <a
                    data-element_id="123"
                    data-parent_reference="456"
                    data-schema="section_reference"
                >
                    article 8.5.1.1
                </a>
                de l'
                <a
                    data-element_id="456"
                    data-schema="document_reference"
                >
                    arrêté préfectoral du
                    <time data-schema="date" datetime="2008-12-10">
                        10 décembre 2008
                    </time>
                </a>
                <span
                    data-direction="rtl"
                    data-has_operand=""
                    data-keyword="supprimés"
                    data-operand=""
                    data-operation_type="delete"
                    data-references="1,2"
                    data-schema="operation"
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
                <div data-schema="alinea">
                    La dernière phrase de l'
                    <a
                        data-parent_reference="123"
                        data-schema="section_reference"
                    >
                        article 8.1.1.2
                    </a>
                    de l'
                    <a
                        data-schema="document_reference"
                        data-element_id="123"
                    >
                        arrêté préfectoral du
                        <time
                            datetime="2008-12-10"
                            data-schema="date"
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
                        data-schema="operation"
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
        tag = document_context.soup.select_one(css_selector(OPERATION_SCHEMA))

        # Act
        resolve_references_and_operands(document_context, tag)

        # Assert
        assert str(document_context.soup) == normalized_html_str(
            """
            <div data-schema="alinea">
                La dernière phrase de l'
                <a
                    data-element_id="1"
                    data-parent_reference="123"
                    data-schema="section_reference"
                >
                    article 8.1.1.2
                </a>
                de l'
                <a
                    data-element_id="123"
                    data-schema="document_reference"
                >
                    arrêté préfectoral du
                    <time
                        datetime="2008-12-10"
                        data-schema="date"
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
                    data-schema="operation"
                >
                    est
                    <b>
                        remplacée
                    </b>
                    par la disposition suivante :
                </span>
                <q
                    data-element_id="2"
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
                <div data-schema="alinea">
                    Les prescriptions de l'
                    <a data-schema="document_reference">
                        arrêté préfectoral du
                        <time
                            datetime="2008-12-10"
                            data-schema="date"
                        >
                                10 décembre 2008
                        </time>
                    </a>
                    <span
                        data-direction="rtl"
                        data-has_operand=""
                        data-keyword="abrogées"
                        data-operand=""
                        data-operation_type="delete"
                        data-schema="operation"
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
        tag = document_context.soup.select_one(css_selector(OPERATION_SCHEMA))

        # Act
        resolve_references_and_operands(document_context, tag)

        # Assert
        assert str(document_context.soup) == normalized_html_str(
            """
            <div data-schema="alinea">
                Les prescriptions de l'
                <a
                    data-element_id="1"
                    data-schema="document_reference"
                >
                    arrêté préfectoral du
                    <time
                        datetime="2008-12-10"
                        data-schema="date"
                    >
                            10 décembre 2008
                    </time>
                </a>
                <span
                    data-direction="rtl"
                    data-has_operand=""
                    data-keyword="abrogées"
                    data-operand=""
                    data-operation_type="delete"
                    data-references="1"
                    data-schema="operation"
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
                <div data-schema="alinea">
                    Les dispositions de l'
                    <a data-schema="document_reference">
                        arrêté préfectoral du
                        <time
                            datetime="2008-12-10"
                            data-schema="date"
                        >
                                10 décembre 2008
                        </time>
                    </a>
                    <a data-schema="page_separator"></a>
                    <span
                        data-direction="rtl"
                        data-has_operand="true"
                        data-keyword="remplacées"
                        data-operand=""
                        data-operation_type="replace"
                        data-schema="operation"
                    >
                        sont
                        <b>
                            remplacées
                        </b>
                        par la disposition suivante :
                    </span>
                    <a data-schema="page_separator"></a>
                    <q>
                        Un relevé hebdomadaire de chacun des compteurs d'eau est réalisé par l'exploitant
                    </q>
                </div>
                """  # noqa: E501
            )
        )
        tag = document_context.soup.select_one(css_selector(OPERATION_SCHEMA))

        # Act
        resolve_references_and_operands(document_context, tag)

        # Assert
        assert str(document_context.soup) == normalized_html_str(
            """
            <div data-schema="alinea">
                Les dispositions de l'
                <a
                    data-element_id="1"
                    data-schema="document_reference"
                >
                    arrêté préfectoral du
                    <time
                        datetime="2008-12-10"
                        data-schema="date"
                    >
                            10 décembre 2008
                    </time>
                </a>
                <a data-schema="page_separator"></a>
                <span
                    data-direction="rtl"
                    data-has_operand="true"
                    data-keyword="remplacées"
                    data-operand="2"
                    data-operation_type="replace"
                    data-references="1"
                    data-schema="operation"
                >
                    sont
                    <b>
                        remplacées
                    </b>
                    par la disposition suivante :
                </span>
                <a data-schema="page_separator"></a>
                <q data-element_id="2">
                    Un relevé hebdomadaire de chacun des compteurs d'eau est réalisé par l'exploitant
                </q>
            </div>
            """  # noqa: E501
        )
