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
from arretify.semantic_tag_specs import (
    AlineaData,
    AlineaSpec,
    DocumentReferenceData,
    DocumentReferenceSpec,
    OperationData,
    OperationSpec,
    PageSeparatorData,
    PageSeparatorSpec,
    SectionReferenceData,
    SectionReferenceSpec,
)
from arretify.types import DocumentType
from arretify.utils.html_semantic import css_selector
from arretify.utils.testing import BaseTestCaseHtml, assert_elements_equal

from .operands_detection import resolve_references_and_operands


class TestResolveReferencesAndOperands(BaseTestCaseHtml):

    def test_several_references_no_operand(self):
        # Arrange
        self.soup_extend(
            [
                self.make_semantic_tag(
                    AlineaSpec,
                    data=AlineaData(number=1),
                    contents=[
                        "Les ",
                        self.make_semantic_tag(
                            SectionReferenceSpec,
                            data=SectionReferenceData(
                                parent_reference="123",
                            ),
                            contents=["paragraphes 3"],
                            reserved_data_attrs=dict(group_id="11"),
                        ),
                        " et ",
                        self.make_semantic_tag(
                            SectionReferenceSpec,
                            data=SectionReferenceData(
                                parent_reference="123",
                            ),
                            contents=["4"],
                            reserved_data_attrs=dict(group_id="11"),
                        ),
                        " de l' ",
                        self.make_semantic_tag(
                            SectionReferenceSpec,
                            data=SectionReferenceData(
                                parent_reference="456",
                            ),
                            contents=["article 8.5.1.1"],
                            reserved_data_attrs=dict(tag_id="123"),
                        ),
                        " de l' ",
                        self.make_semantic_tag(
                            DocumentReferenceSpec,
                            data=DocumentReferenceData(
                                type=DocumentType.arrete_prefectoral,
                                date="2008-12-10",
                            ),
                            contents=["arrêté préfectoral du 10 décembre 2008"],
                            reserved_data_attrs=dict(tag_id="456"),
                        ),
                        self.make_semantic_tag(
                            OperationSpec,
                            data=OperationData(
                                direction="rtl",
                                keyword="supprimés",
                                operand="",
                                operation_type="delete",
                            ),
                            contents=[
                                "sont ",
                                self.make_tag("b", contents=["supprimés"]),
                            ],
                        ),
                    ],
                )
            ]
        )
        operation_tag = self.soup.select_one(css_selector(OperationSpec))

        # Act
        resolve_references_and_operands(self.context, operation_tag)

        # Assert
        assert_elements_equal(
            self.soup.contents[0],
            self.make_semantic_tag(
                AlineaSpec,
                data=AlineaData(number=1),
                contents=[
                    "Les ",
                    self.make_semantic_tag(
                        SectionReferenceSpec,
                        data=SectionReferenceData(
                            parent_reference="123",
                        ),
                        contents=["paragraphes 3"],
                        reserved_data_attrs=dict(tag_id="1", group_id="11"),
                    ),
                    " et ",
                    self.make_semantic_tag(
                        SectionReferenceSpec,
                        data=SectionReferenceData(
                            parent_reference="123",
                        ),
                        contents=["4"],
                        reserved_data_attrs=dict(tag_id="2", group_id="11"),
                    ),
                    " de l' ",
                    self.make_semantic_tag(
                        SectionReferenceSpec,
                        data=SectionReferenceData(
                            parent_reference="456",
                        ),
                        contents=["article 8.5.1.1"],
                        reserved_data_attrs=dict(tag_id="123"),
                    ),
                    " de l' ",
                    self.make_semantic_tag(
                        DocumentReferenceSpec,
                        data=DocumentReferenceData(
                            type=DocumentType.arrete_prefectoral,
                            date="2008-12-10",
                        ),
                        contents=["arrêté préfectoral du 10 décembre 2008"],
                        reserved_data_attrs=dict(tag_id="456"),
                    ),
                    self.make_semantic_tag(
                        OperationSpec,
                        data=OperationData(
                            direction="rtl",
                            keyword="supprimés",
                            operand="",
                            operation_type="delete",
                            references="1,2",
                        ),
                        contents=[
                            "sont ",
                            self.make_tag("b", contents=["supprimés"]),
                        ],
                    ),
                ],
            ),
        )

    def test_one_reference_one_operand(self):
        # Arrange
        self.soup_extend(
            [
                self.make_semantic_tag(
                    AlineaSpec,
                    data=AlineaData(number=1),
                    contents=[
                        "La dernière phrase de l' ",
                        self.make_semantic_tag(
                            SectionReferenceSpec,
                            data=SectionReferenceData(
                                parent_reference="123",
                            ),
                            contents=["article 8.1.1.2"],
                        ),
                        " de l' ",
                        self.make_semantic_tag(
                            DocumentReferenceSpec,
                            data=DocumentReferenceData(
                                type=DocumentType.arrete_prefectoral,
                                date="2008-12-10",
                            ),
                            contents=["arrêté préfectoral du 10 décembre 2008"],
                            reserved_data_attrs=dict(tag_id="123"),
                        ),
                        self.make_semantic_tag(
                            OperationSpec,
                            data=OperationData(
                                direction="rtl",
                                has_operand=True,
                                keyword="remplacée",
                                operand="",
                                operation_type="replace",
                            ),
                            contents=[
                                "est ",
                                self.make_tag("b", contents=["remplacée"]),
                                " par la disposition suivante :",
                            ],
                        ),
                        self.make_tag(
                            "q",
                            contents=[
                                (
                                    "Un relevé hebdomadaire de chacun des compteurs "
                                    "d'eau est réalisé par l'exploitant"
                                )
                            ],
                        ),
                        ".",
                    ],
                )
            ]
        )
        operation_tag = self.soup.select_one(css_selector(OperationSpec))

        # Act
        resolve_references_and_operands(self.context, operation_tag)

        # Assert
        assert_elements_equal(
            self.soup.contents[0],
            self.make_semantic_tag(
                AlineaSpec,
                data=AlineaData(number=1),
                contents=[
                    "La dernière phrase de l' ",
                    self.make_semantic_tag(
                        SectionReferenceSpec,
                        data=SectionReferenceData(
                            parent_reference="123",
                        ),
                        contents=["article 8.1.1.2"],
                        reserved_data_attrs=dict(tag_id="1"),
                    ),
                    " de l' ",
                    self.make_semantic_tag(
                        DocumentReferenceSpec,
                        data=DocumentReferenceData(
                            type=DocumentType.arrete_prefectoral,
                            date="2008-12-10",
                        ),
                        contents=["arrêté préfectoral du 10 décembre 2008"],
                        reserved_data_attrs=dict(tag_id="123"),
                    ),
                    self.make_semantic_tag(
                        OperationSpec,
                        data=OperationData(
                            direction="rtl",
                            has_operand=True,
                            keyword="remplacée",
                            operand="2",
                            operation_type="replace",
                            references="1",
                        ),
                        contents=[
                            "est ",
                            self.make_tag("b", contents=["remplacée"]),
                            " par la disposition suivante :",
                        ],
                    ),
                    self.make_tag(
                        "q",
                        contents=[
                            (
                                "Un relevé hebdomadaire de chacun des compteurs "
                                "d'eau est réalisé par l'exploitant"
                            )
                        ],
                        reserved_data_attrs=dict(tag_id="2"),
                    ),
                    ".",
                ],
            ),
        )

    def test_with_single_document_reference(self):
        # Arrange
        self.soup_extend(
            [
                self.make_semantic_tag(
                    AlineaSpec,
                    data=AlineaData(number=1),
                    contents=[
                        "Les prescriptions de l' ",
                        self.make_semantic_tag(
                            DocumentReferenceSpec,
                            data=DocumentReferenceData(
                                type=DocumentType.arrete_prefectoral,
                                date="2008-12-10",
                            ),
                            contents=["arrêté préfectoral du 10 décembre 2008"],
                        ),
                        self.make_semantic_tag(
                            OperationSpec,
                            data=OperationData(
                                direction="rtl",
                                keyword="abrogées",
                                operand="",
                                operation_type="delete",
                            ),
                            contents=[
                                "sont ",
                                self.make_tag("b", contents=["abrogées"]),
                                " .",
                            ],
                        ),
                    ],
                )
            ]
        )
        operation_tag = self.soup.select_one(css_selector(OperationSpec))

        # Act
        resolve_references_and_operands(self.context, operation_tag)

        # Assert
        assert_elements_equal(
            self.soup.contents[0],
            self.make_semantic_tag(
                AlineaSpec,
                data=AlineaData(number=1),
                contents=[
                    "Les prescriptions de l' ",
                    self.make_semantic_tag(
                        DocumentReferenceSpec,
                        data=DocumentReferenceData(
                            type=DocumentType.arrete_prefectoral,
                            date="2008-12-10",
                        ),
                        contents=["arrêté préfectoral du 10 décembre 2008"],
                        reserved_data_attrs=dict(tag_id="1"),
                    ),
                    self.make_semantic_tag(
                        OperationSpec,
                        data=OperationData(
                            direction="rtl",
                            keyword="abrogées",
                            operand="",
                            operation_type="delete",
                            references="1",
                        ),
                        contents=[
                            "sont ",
                            self.make_tag("b", contents=["abrogées"]),
                            " .",
                        ],
                    ),
                ],
            ),
        )

    def test_with_inline_tag_between_operands(self):
        # Arrange
        self.soup_extend(
            [
                self.make_semantic_tag(
                    AlineaSpec,
                    data=AlineaData(number=1),
                    contents=[
                        "Les dispositions de l' ",
                        self.make_semantic_tag(
                            DocumentReferenceSpec,
                            data=DocumentReferenceData(
                                type=DocumentType.arrete_prefectoral,
                                date="2008-12-10",
                            ),
                            contents=["arrêté préfectoral du 10 décembre 2008"],
                        ),
                        self.make_semantic_tag(
                            PageSeparatorSpec,
                            data=PageSeparatorData(page_index=1),
                        ),
                        self.make_semantic_tag(
                            OperationSpec,
                            data=OperationData(
                                direction="rtl",
                                has_operand=True,
                                keyword="remplacées",
                                operand="",
                                operation_type="replace",
                            ),
                            contents=[
                                "sont ",
                                self.make_tag("b", contents=["remplacées"]),
                                " par la disposition suivante :",
                            ],
                        ),
                        self.make_semantic_tag(
                            PageSeparatorSpec,
                            data=PageSeparatorData(page_index=2),
                        ),
                        self.make_tag(
                            "q",
                            contents=[
                                (
                                    "Un relevé hebdomadaire de chacun des compteurs "
                                    "d'eau est réalisé par l'exploitant"
                                )
                            ],
                        ),
                    ],
                )
            ]
        )
        operation_tag = self.soup.select_one(css_selector(OperationSpec))

        # Act
        resolve_references_and_operands(self.context, operation_tag)

        # Assert
        assert_elements_equal(
            self.soup.contents[0],
            self.make_semantic_tag(
                AlineaSpec,
                data=AlineaData(number=1),
                contents=[
                    "Les dispositions de l' ",
                    self.make_semantic_tag(
                        DocumentReferenceSpec,
                        data=DocumentReferenceData(
                            type=DocumentType.arrete_prefectoral,
                            date="2008-12-10",
                        ),
                        contents=["arrêté préfectoral du 10 décembre 2008"],
                        reserved_data_attrs=dict(tag_id="1"),
                    ),
                    self.make_semantic_tag(
                        PageSeparatorSpec,
                        data=PageSeparatorData(page_index=1),
                    ),
                    self.make_semantic_tag(
                        OperationSpec,
                        data=OperationData(
                            direction="rtl",
                            has_operand=True,
                            keyword="remplacées",
                            operand="2",
                            operation_type="replace",
                            references="1",
                        ),
                        contents=[
                            "sont ",
                            self.make_tag("b", contents=["remplacées"]),
                            " par la disposition suivante :",
                        ],
                    ),
                    self.make_semantic_tag(
                        PageSeparatorSpec,
                        data=PageSeparatorData(page_index=2),
                    ),
                    self.make_tag(
                        "q",
                        contents=[
                            (
                                "Un relevé hebdomadaire de chacun des compteurs "
                                "d'eau est réalisé par l'exploitant"
                            )
                        ],
                        reserved_data_attrs=dict(tag_id="2"),
                    ),
                ],
            ),
        )
