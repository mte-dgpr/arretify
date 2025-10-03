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

from arretify.utils.testing import create_document_context
from arretify.utils.references import build_reference_tree
from arretify.law_data.types import Section, SectionType
from arretify.utils.testing import make_testing_function_for_children_list
from .unknown_sections_resolution import resolve_unknown_sections, remove_misdetected_sections


remove_misdetected_sections_ = make_testing_function_for_children_list(remove_misdetected_sections)


class TestResolveUnknownSections(unittest.TestCase):

    def test_resolve_unknown_section_of_document(self):
        # Arrange
        document_context = create_document_context(
            """
            <div>
                <a
                    data-schema="section_reference"
                    data-element_id="1"
                    data-parent_reference="2"
                    data-start_num="123"
                    data-type="unknown"
                >
                    Paragraphe 123
                </a>
                de l'
                <a
                    data-schema="document_reference"
                    data-element_id="2"
                    data-num="456"
                    data-type="arrete"
                >
                    arrêté n° 456
                </a>
            </div>
            """
        )
        reference_tree = build_reference_tree(
            document_context.soup.select_one("[data-schema='document_reference']")
        )

        # Act
        resolve_unknown_sections(document_context, reference_tree)

        # Assert
        section_reference_tag = document_context.soup.select_one(
            "[data-schema='section_reference']"
        )
        section = Section.from_tag(section_reference_tag)
        assert section.type == SectionType.ARTICLE

    def test_resolve_unknown_sub_section(self):
        # Arrange
        document_context = create_document_context(
            """
            <div>
                <a
                    data-schema="section_reference"
                    data-element_id="1"
                    data-parent_reference="2"
                    data-start_num="123"
                    data-type="unknown"
                >
                    Paragraphe 123
                </a>
                de l'
                <a
                    data-schema="section_reference"
                    data-element_id="2"
                    data-start_num="456"
                    data-type="article"
                >
                    Article 456
                </a>
            </div>
            """
        )
        reference_tree = build_reference_tree(
            document_context.soup.select_one(
                "[data-schema='section_reference'][data-element_id='1']"
            )
        )

        # Act
        resolve_unknown_sections(document_context, reference_tree)

        # Assert
        section_reference_tag = document_context.soup.select_one(
            "[data-schema='section_reference'][data-element_id='1']"
        )
        section = Section.from_tag(section_reference_tag)
        assert section.type == SectionType.ALINEA


class TestRemoveMisdetectedSections(unittest.TestCase):

    def test_appendix_all_alone(self):
        assert (
            remove_misdetected_sections_(
                """
            à l'
            <a
                data-schema="section_reference"
                data-element_id="1"
                data-type="annexe"
            >
                annexe
            </a>
            de la mairie
            """
            )
            == ["à l' ", "annexe", " de la mairie"]
        )
