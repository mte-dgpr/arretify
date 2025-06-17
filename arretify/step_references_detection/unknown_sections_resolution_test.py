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
from arretify.utils.references import build_and_traverse_reference_tree
from arretify.law_data.types import Section, SectionType
from .unknown_sections_resolution import resolve_unknown_sections_in_tree, resolve_unknown_sections


class TestResolveUnknownSections(unittest.TestCase):
    def test_resolve_several_unknown_sections(self):
        # Arrange
        document_context = create_document_context(
            """
            <div>
                <a
                    class="arretify-section_reference"
                    data-element_id="1"
                    data-parent_reference="2"
                    data-start_num="123"
                    data-type="unknown"
                >
                    Paragraphe 123
                </a>
                de l'
                <a
                    class="arretify-document_reference"
                    data-element_id="2"
                    data-num="456"
                    data-type="arrete"
                >
                    arrêté n° 456
                </a>

                et

                <a
                    class="arretify-section_reference"
                    data-element_id="3"
                    data-parent_reference="4"
                    data-start_num="789"
                    data-type="unknown"
                >
                    Paragraphe 789
                </a>
                de l'
                <a
                    class="arretify-document_reference"
                    data-element_id="4"
                    data-num="456"
                    data-type="arrete"
                >
                    arrêté n° 456
                </a>
            </div>
            """
        )

        # Act
        resolve_unknown_sections(document_context)

        # Assert
        section_reference_tag1 = document_context.soup.select_one(
            ".arretify-section_reference[data-element_id='1']"
        )
        section = Section.from_tag(section_reference_tag1)
        assert section.type == SectionType.ARTICLE

        section_reference_tag2 = document_context.soup.select_one(
            ".arretify-section_reference[data-element_id='3']"
        )
        section = Section.from_tag(section_reference_tag2)
        assert section.type == SectionType.ARTICLE


class TestResolveUnknownSectionsInTree(unittest.TestCase):

    def test_resolve_unknown_section_of_document(self):
        # Arrange
        document_context = create_document_context(
            """
            <div>
                <a
                    class="arretify-section_reference"
                    data-element_id="1"
                    data-parent_reference="2"
                    data-start_num="123"
                    data-type="unknown"
                >
                    Paragraphe 123
                </a>
                de l'
                <a
                    class="arretify-document_reference"
                    data-element_id="2"
                    data-num="456"
                    data-type="arrete"
                >
                    arrêté n° 456
                </a>
            </div>
            """
        )
        reference_tree_traversal = list(
            build_and_traverse_reference_tree(
                document_context.soup.select_one(".arretify-document_reference")
            )
        )

        # Act
        resolve_unknown_sections_in_tree(document_context, reference_tree_traversal)

        # Assert
        section_reference_tag = document_context.soup.select_one(".arretify-section_reference")
        section = Section.from_tag(section_reference_tag)
        assert section.type == SectionType.ARTICLE

    def test_resolve_unknown_sub_section(self):
        # Arrange
        document_context = create_document_context(
            """
            <div>
                <a
                    class="arretify-section_reference"
                    data-element_id="1"
                    data-parent_reference="2"
                    data-start_num="123"
                    data-type="unknown"
                >
                    Paragraphe 123
                </a>
                de l'
                <a
                    class="arretify-section_reference"
                    data-element_id="2"
                    data-start_num="456"
                    data-type="article"
                >
                    Article 456
                </a>
            </div>
            """
        )
        reference_tree_traversal = list(
            build_and_traverse_reference_tree(
                document_context.soup.select_one(".arretify-section_reference[data-element_id='1']")
            )
        )

        # Act
        resolve_unknown_sections_in_tree(document_context, reference_tree_traversal)

        # Assert
        section_reference_tag = document_context.soup.select_one(
            ".arretify-section_reference[data-element_id='1']"
        )
        section = Section.from_tag(section_reference_tag)
        assert section.type == SectionType.ALINEA
