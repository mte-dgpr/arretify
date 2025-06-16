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

from arretify.law_data.types import Document, DocumentType
from .references import (
    build_reference_tree,
    iter_section_references,
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

    def test_section_tags_same_instance(self):
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
        section_reference_tag = soup.select_one("a[data-element_id='4']")

        # Act
        branches = build_reference_tree(section_reference_tag)

        # Assert
        assert len(branches) == 2
        assert branches[0][0] is branches[1][0]  # Same instance
        assert branches[0][1] is branches[1][1]  # Same instance


class TestIterSectionReferences(unittest.TestCase):

    def test_iter_section_references(self):
        # Arrange
        soup = BeautifulSoup(
            """
            <div>
                <a
                    class="dsr-section_reference"
                    data-element_id="1"
                    data-parent_reference="2"
                    data-type="article"
                >
                    Section 1
                </a>
                <a
                    class="dsr-document_reference"
                    data-element_id="2"
                    data-id="L123"
                    data-type="arrete"
                >
                    Parent
                </a>
            </div>
            """,
            features="html.parser",
        )
        section_reference_tag = soup.select_one(".dsr-document_reference")

        # Act
        section_references = list(iter_section_references(section_reference_tag))

        # Assert
        assert len(section_references) == 1
        section_reference = section_references[0]
        assert section_reference[0]["data-element_id"] == "1"
        assert section_reference[1] == Document(type=DocumentType.unknown_arrete, id="L123")
        assert len(section_reference[2]) == 1
