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
    DateSpec,
    DocumentReferenceData,
    DocumentReferenceSpec,
    SectionReferenceData,
    SectionReferenceSpec,
)
from arretify.utils.testing import BaseTestCaseHtml, assert_element_lists_equal

from .match_sections_with_documents import match_sections_to_parents


class TestConnectParentSections(BaseTestCaseHtml):

    def test_single_section_to_section(self):
        # Arrange
        self.soup_extend(
            [
                self.make_semantic_tag(
                    SectionReferenceSpec,
                    contents=["2ème alinéa"],
                ),
                " de l' ",
                self.make_semantic_tag(
                    DocumentReferenceSpec,
                    contents=["article 1"],
                    data=DocumentReferenceData(
                        type="self",
                    ),
                ),
            ]
        )

        # Act
        actual = match_sections_to_parents(self.context, self.soup.contents)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                self.make_semantic_tag(
                    SectionReferenceSpec,
                    contents=["2ème alinéa"],
                    data=SectionReferenceData(
                        parent_reference="1",
                    ),
                ),
                " de l' ",
                self.make_semantic_tag(
                    DocumentReferenceSpec,
                    contents=["article 1"],
                    data=DocumentReferenceData(
                        type="self",
                    ),
                    reserved_data_attrs=dict(tag_id="1"),
                ),
            ],
        )

    def test_single_section_to_document(self):
        # Arrange
        self.soup_extend(
            [
                self.make_semantic_tag(
                    SectionReferenceSpec,
                    contents=["article 5"],
                ),
                " de l' ",
                self.make_semantic_tag(
                    DocumentReferenceSpec,
                    contents=[
                        "arrêté du ",
                        self.make_semantic_tag(
                            DateSpec,
                            contents=["23 mai 2016"],
                            attrs=dict(datetime="2016-05-23"),
                        ),
                    ],
                    data=DocumentReferenceData(
                        type="arrete-ministeriel",
                    ),
                ),
            ]
        )

        # Act
        actual = match_sections_to_parents(self.context, self.soup.contents)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                self.make_semantic_tag(
                    SectionReferenceSpec,
                    contents=["article 5"],
                    data=SectionReferenceData(
                        parent_reference="1",
                    ),
                ),
                " de l' ",
                self.make_semantic_tag(
                    DocumentReferenceSpec,
                    contents=[
                        "arrêté du ",
                        self.make_semantic_tag(
                            DateSpec,
                            contents=["23 mai 2016"],
                            attrs=dict(datetime="2016-05-23"),
                        ),
                    ],
                    data=DocumentReferenceData(
                        type="arrete-ministeriel",
                    ),
                    reserved_data_attrs=dict(tag_id="1"),
                ),
            ],
        )

    def test_multiple_sections_to_document(self):
        # Arrange
        self.soup_extend(
            [
                self.make_semantic_tag(
                    SectionReferenceSpec,
                    contents=["articles R. 512 - 74"],
                    reserved_data_attrs=dict(group_id="111"),
                ),
                " et ",
                self.make_semantic_tag(
                    SectionReferenceSpec,
                    contents=["R. 512 39-1 à R.512-39-3"],
                    reserved_data_attrs=dict(group_id="111"),
                ),
                " du ",
                self.make_semantic_tag(
                    DocumentReferenceSpec,
                    contents=["code de l'environnement"],
                    data=DocumentReferenceData(
                        type="code",
                        title="Code de l'environnement",
                    ),
                ),
            ]
        )

        # Act
        actual = match_sections_to_parents(self.context, self.soup.contents)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                self.make_semantic_tag(
                    SectionReferenceSpec,
                    contents=["articles R. 512 - 74"],
                    data=SectionReferenceData(
                        parent_reference="1",
                    ),
                    reserved_data_attrs=dict(group_id="111"),
                ),
                " et ",
                self.make_semantic_tag(
                    SectionReferenceSpec,
                    contents=["R. 512 39-1 à R.512-39-3"],
                    data=SectionReferenceData(
                        parent_reference="1",
                    ),
                    reserved_data_attrs=dict(group_id="111"),
                ),
                " du ",
                self.make_semantic_tag(
                    DocumentReferenceSpec,
                    contents=["code de l'environnement"],
                    data=DocumentReferenceData(
                        type="code",
                        title="Code de l'environnement",
                    ),
                    reserved_data_attrs=dict(tag_id="1"),
                ),
            ],
        )

    def test_section_to_section_to_document(self):
        # Arrange
        self.soup_extend(
            [
                self.make_semantic_tag(
                    SectionReferenceSpec,
                    contents=["alinéa 3"],
                ),
                " de l' ",
                self.make_semantic_tag(
                    SectionReferenceSpec,
                    contents=["article R121-1"],
                ),
                " du ",
                self.make_semantic_tag(
                    DocumentReferenceSpec,
                    contents=["code de l'environnement"],
                    data=DocumentReferenceData(
                        type="code",
                        title="Code de l'environnement",
                    ),
                ),
            ]
        )

        # Act
        actual = match_sections_to_parents(self.context, self.soup.contents)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                self.make_semantic_tag(
                    SectionReferenceSpec,
                    contents=["alinéa 3"],
                    data=SectionReferenceData(
                        parent_reference="1",
                    ),
                ),
                " de l' ",
                self.make_semantic_tag(
                    SectionReferenceSpec,
                    contents=["article R121-1"],
                    data=SectionReferenceData(
                        parent_reference="2",
                    ),
                    reserved_data_attrs=dict(tag_id="1"),
                ),
                " du ",
                self.make_semantic_tag(
                    DocumentReferenceSpec,
                    contents=["code de l'environnement"],
                    data=DocumentReferenceData(
                        type="code",
                        title="Code de l'environnement",
                    ),
                    reserved_data_attrs=dict(tag_id="2"),
                ),
            ],
        )

    def test_section_separated_by_inline_element(self):
        # Arrange
        self.soup_extend(
            [
                self.make_semantic_tag(
                    SectionReferenceSpec,
                    contents=["annexe III"],
                    reserved_data_attrs=dict(tag_id="1"),
                ),
                " de ",
                self.make_tag("br"),
                " l' ",
                self.make_semantic_tag(
                    DocumentReferenceSpec,
                    contents=["arrêté ministériel du 23 mai 2016"],
                    data=DocumentReferenceData(
                        type="arrete-ministeriel",
                    ),
                    reserved_data_attrs=dict(tag_id="2"),
                ),
            ]
        )

        # Act
        actual = match_sections_to_parents(self.context, self.soup.contents)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                self.make_semantic_tag(
                    SectionReferenceSpec,
                    contents=["annexe III"],
                    data=SectionReferenceData(
                        parent_reference="2",
                    ),
                    reserved_data_attrs=dict(tag_id="1"),
                ),
                " de ",
                self.make_tag("br"),
                " l' ",
                self.make_semantic_tag(
                    DocumentReferenceSpec,
                    contents=["arrêté ministériel du 23 mai 2016"],
                    data=DocumentReferenceData(
                        type="arrete-ministeriel",
                    ),
                    reserved_data_attrs=dict(tag_id="2"),
                ),
            ],
        )

    def test_last_in_reference(self):
        # Arrange
        self.soup_extend(
            [
                self.make_semantic_tag(
                    SectionReferenceSpec,
                    contents=["dernier alinéa"],
                ),
                " de l' ",
                self.make_semantic_tag(
                    DocumentReferenceSpec,
                    contents=["article 3.4"],
                    data=DocumentReferenceData(
                        type="self",
                    ),
                ),
            ]
        )

        # Act
        actual = match_sections_to_parents(self.context, self.soup.contents)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                self.make_semantic_tag(
                    SectionReferenceSpec,
                    contents=["dernier alinéa"],
                    data=SectionReferenceData(
                        parent_reference="1",
                    ),
                ),
                " de l' ",
                self.make_semantic_tag(
                    DocumentReferenceSpec,
                    contents=["article 3.4"],
                    data=DocumentReferenceData(
                        type="self",
                    ),
                    reserved_data_attrs=dict(tag_id="1"),
                ),
            ],
        )
