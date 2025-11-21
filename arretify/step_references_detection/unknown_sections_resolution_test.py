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

from arretify.semantic_tag_specs import SectionReferenceSpec
from arretify.types import SectionType
from arretify.utils.html_semantic import get_semantic_tag_data
from arretify.utils.references import build_reference_tree
from arretify.utils.testing import create_document_context, make_testing_function_for_children_list

from .unknown_sections_resolution import remove_misdetected_sections, resolve_unknown_sections

remove_misdetected_sections_ = make_testing_function_for_children_list(remove_misdetected_sections)


class TestResolveUnknownSections(unittest.TestCase):

    def test_resolve_unknown_section_of_document(self):
        # Arrange
        document_context = create_document_context(
            """
            <div>
                <a
                    data-spec="section_reference"
                    data-tag_id="1"
                    data-parent_reference="2"
                    data-start_num="123"
                    data-type="unknown"
                >
                    Paragraphe 123
                </a>
                de l'
                <a
                    data-spec="document_reference"
                    data-tag_id="2"
                    data-num="456"
                    data-type="arrete"
                >
                    arrêté n° 456
                </a>
            </div>
            """
        )
        reference_tree = build_reference_tree(
            document_context.protected_soup.select_one("[data-spec='document_reference']")
        )

        # Act
        resolve_unknown_sections(document_context, reference_tree)

        # Assert
        section_reference_tag = document_context.protected_soup.select_one(
            "[data-spec='section_reference']"
        )
        section_reference = get_semantic_tag_data(SectionReferenceSpec, section_reference_tag)
        assert section_reference.type == SectionType.ARTICLE

    def test_resolve_unknown_sub_section(self):
        # Arrange
        document_context = create_document_context(
            """
            <div>
                <a
                    data-spec="section_reference"
                    data-tag_id="1"
                    data-parent_reference="2"
                    data-start_num="123"
                    data-type="unknown"
                >
                    Paragraphe 123
                </a>
                de l'
                <a
                    data-spec="section_reference"
                    data-tag_id="2"
                    data-start_num="456"
                    data-type="article"
                >
                    Article 456
                </a>
            </div>
            """
        )
        reference_tree = build_reference_tree(
            document_context.protected_soup.select_one(
                "[data-spec='section_reference'][data-tag_id='1']"
            )
        )

        # Act
        resolve_unknown_sections(document_context, reference_tree)

        # Assert
        section_reference_tag = document_context.protected_soup.select_one(
            "[data-spec='section_reference'][data-tag_id='1']"
        )
        section_reference = get_semantic_tag_data(SectionReferenceSpec, section_reference_tag)
        assert section_reference.type == SectionType.ALINEA


class TestRemoveMisdetectedSections(unittest.TestCase):

    def test_appendix_all_alone(self):
        assert (
            remove_misdetected_sections_(
                """
            à l'
            <a
                data-spec="section_reference"
                data-tag_id="1"
                data-type="annexe"
            >
                annexe
            </a>
            de la mairie
            """
            )
            == ["à l' ", "annexe", " de la mairie"]
        )
