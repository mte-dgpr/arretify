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

from arretify.utils.testing import normalized_html_str, create_document_context
from arretify.utils import html

from .operands_detection import resolve_references_and_operands


class TestParseOperations(unittest.TestCase):

    def setUp(self):
        html._ELEMENT_ID_COUNTER = 0
        html._GROUP_ID_COUNTER = 0

    def test_several_references_no_operand(self):
        # Arrange
        document_context = create_document_context(
            normalized_html_str(
                """
                <div class="dsr-alinea">
                    Les
                    <a
                        class="dsr-section_reference"
                        data-group_id="11"
                        data-parent_reference="123"
                    >
                        paragraphes 3
                    </a>
                    et
                    <a
                        class="dsr-section_reference"
                        data-group_id="11"
                        data-parent_reference="123"
                    >
                        4
                    </a>
                    de l'
                    <a
                        class="dsr-section_reference"
                        data-element_id="123"
                        data-parent_reference="456"
                    >
                        article 8.5.1.1
                    </a>
                    de l'
                    <a
                        class="dsr-document_reference"
                        data-element_id="456"
                    >
                        arrêté préfectoral du
                        <time class="dsr-date" datetime="2008-12-10">
                            10 décembre 2008
                        </time>
                    </a>
                    <span
                        class="dsr-operation"
                        data-direction="rtl"
                        data-has_operand=""
                        data-keyword="supprimés"
                        data-operand=""
                        data-operation_type="delete"
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
        tag = document_context.soup.select_one(".dsr-operation")

        # Act
        resolve_references_and_operands(document_context, tag)

        # Assert
        assert str(document_context.soup) == normalized_html_str(
            # Check that element_id was added to both references, and that the references were
            # added to the operation
            """
            <div class="dsr-alinea">
                Les
                <a
                    class="dsr-section_reference"
                    data-element_id="1"
                    data-group_id="11"
                    data-parent_reference="123"
                >
                    paragraphes 3
                </a>
                et
                <a
                    class="dsr-section_reference"
                    data-element_id="2"
                    data-group_id="11"
                    data-parent_reference="123"
                >
                    4
                </a>
                de l'
                <a
                    class="dsr-section_reference"
                    data-element_id="123"
                    data-parent_reference="456"
                >
                    article 8.5.1.1
                </a>
                de l'
                <a
                    class="dsr-document_reference"
                    data-element_id="456"
                >
                    arrêté préfectoral du
                    <time class="dsr-date" datetime="2008-12-10">
                        10 décembre 2008
                    </time>
                </a>
                <span
                    class="dsr-operation"
                    data-direction="rtl"
                    data-has_operand=""
                    data-keyword="supprimés"
                    data-operand=""
                    data-operation_type="delete"
                    data-references="1,2"
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
                <div class="dsr-alinea">
                    La dernière phrase de l'
                    <a
                        class="dsr-section_reference"
                        data-parent_reference="123"
                    >
                        article 8.1.1.2
                    </a>
                    de l'
                    <a
                        class="dsr-document_reference"
                        data-element_id="123"
                    >
                        arrêté préfectoral du
                        <time class="dsr-date" datetime="2008-12-10">
                                10 décembre 2008
                        </time>
                    </a>
                    <span
                        class="dsr-operation"
                        data-direction="rtl"
                        data-has_operand="true"
                        data-keyword="remplacée"
                        data-operand=""
                        data-operation_type="replace"
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
        tag = document_context.soup.select_one(".dsr-operation")

        # Act
        resolve_references_and_operands(document_context, tag)

        # Assert
        assert str(document_context.soup) == normalized_html_str(
            """
            <div class="dsr-alinea">
                La dernière phrase de l'
                <a
                    class="dsr-section_reference"
                    data-element_id="1"
                    data-parent_reference="123"
                >
                    article 8.1.1.2
                </a>
                de l'
                <a
                    class="dsr-document_reference"
                    data-element_id="123"
                >
                    arrêté préfectoral du
                    <time class="dsr-date" datetime="2008-12-10">
                            10 décembre 2008
                    </time>
                </a>
                <span
                    class="dsr-operation"
                    data-direction="rtl"
                    data-has_operand="true"
                    data-keyword="remplacée"
                    data-operand="2"
                    data-operation_type="replace"
                    data-references="1"
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
                <div class="dsr-alinea">
                    Les prescriptions de l'
                    <a class="dsr-document_reference">
                        arrêté préfectoral du
                        <time class="dsr-date" datetime="2008-12-10">
                                10 décembre 2008
                        </time>
                    </a>
                    <span class="dsr-operation" data-direction="rtl" data-has_operand="" data-keyword="abrogées" data-operand="" data-operation_type="delete">
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
        tag = document_context.soup.select_one(".dsr-operation")

        # Act
        resolve_references_and_operands(document_context, tag)

        # Assert
        assert str(document_context.soup) == normalized_html_str(
            """
            <div class="dsr-alinea">
                Les prescriptions de l'
                <a class="dsr-document_reference" data-element_id="1">
                    arrêté préfectoral du
                    <time class="dsr-date" datetime="2008-12-10">
                            10 décembre 2008
                    </time>
                </a>
                <span class="dsr-operation" data-direction="rtl" data-has_operand="" data-keyword="abrogées" data-operand="" data-operation_type="delete" data-references="1">
                    sont
                    <b>
                        abrogées
                    </b>
                    .
                </span>
            </div>
            """  # noqa: E501
        )
