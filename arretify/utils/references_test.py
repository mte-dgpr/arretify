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

from arretify.semantic_tag_specs import DocumentReferenceData, SectionReferenceData
from arretify.types import DocumentType, SectionType

from .references import build_reference_tree, iter_reference_trees, traverse_reference_tree


class TestBuildReferenceTree(unittest.TestCase):

    def test_get_all_branches(self):
        # Arrange
        soup = BeautifulSoup(
            """
            <div>
                <a
                    data-spec="section_reference"
                    data-tag_id="1"
                    data-parent_reference="3"
                >
                    Section 1.1
                </a>
                <a
                    data-spec="section_reference"
                    data-tag_id="2"
                    data-parent_reference="3"
                >
                    Section 1.2
                </a>
                <a
                    data-spec="section_reference"
                    data-tag_id="3"
                    data-parent_reference="4"
                >
                    Section 1
                </a>
                <a
                    data-spec="document_reference"
                    data-tag_id="4"
                >
                    Some Document
                </a>
            </div>
            """,
            features="html.parser",
        )
        section_reference_tag = soup.select_one("a[data-tag_id='3']")

        # Act
        branches = build_reference_tree(section_reference_tag)

        # Assert
        assert len(branches) == 2
        assert [tag["data-tag_id"] for tag in branches[0]] == ["4", "3", "1"]
        assert [tag["data-tag_id"] for tag in branches[1]] == ["4", "3", "2"]

    def test_leaf_no_element_id(self):
        # Arrange
        soup = BeautifulSoup(
            """
            <div>
                <a
                    id="tag1"
                    data-spec="section_reference"
                    data-parent_reference="1"
                >
                    Section 1.1
                </a>
                <a
                    id="tag2"
                    data-spec="section_reference"
                    data-tag_id="1"
                >
                    Section 1
                </a>
            </div>
            """,
            features="html.parser",
        )
        section_reference_tag = soup.select_one("[data-spec='section_reference']")

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
                    data-spec="section_reference"
                    data-tag_id="1"
                    data-parent_reference="3"
                >
                    Section 1.1
                </a>
                <a
                    data-spec="section_reference"
                    data-tag_id="2"
                    data-parent_reference="3"
                >
                    Section 1.2
                </a>
                <a
                    data-spec="section_reference"
                    data-tag_id="3"
                    data-parent_reference="4"
                >
                    Section 1
                </a>
                <a
                    data-spec="document_reference"
                    data-tag_id="4"
                >
                    Some Document
                </a>
            </div>
            """,
            features="html.parser",
        )
        section_reference_tag = soup.select_one("a[data-tag_id='4']")

        # Act
        branches = build_reference_tree(section_reference_tag)

        # Assert
        assert len(branches) == 2
        assert branches[0][0] is branches[1][0]  # Same instance
        assert branches[0][1] is branches[1][1]  # Same instance

    def test_section_reference_as_root(self):
        # Arrange
        soup = BeautifulSoup(
            """
            <div>
                <a
                    data-spec="section_reference"
                    data-tag_id="1"
                    data-parent_reference="2"
                >
                    Section 1
                </a>
                <a
                    data-spec="section_reference"
                    data-tag_id="2"
                >
                    Parent Document
                </a>
            </div>
            """,
            features="html.parser",
        )
        section_reference_tag = soup.select_one("a[data-tag_id='1']")

        # Act
        branches = build_reference_tree(section_reference_tag)

        # Assert
        assert len(branches) == 1
        assert [tag["data-tag_id"] for tag in branches[0]] == ["2", "1"]


class TestTraverseReferenceTree(unittest.TestCase):

    def test_traverse_section_references(self):
        # Arrange
        soup = BeautifulSoup(
            """
            <div>
                <a
                    data-spec="section_reference"
                    data-tag_id="1"
                    data-parent_reference="2"
                    data-start_num="456"
                    data-type="article"
                >
                    Section 1
                </a>
                <a
                    data-spec="document_reference"
                    data-tag_id="2"
                    data-id="L123"
                    data-type="arrete"
                >
                    Parent
                </a>
            </div>
            """,
            features="html.parser",
        )
        document_reference_tag = soup.select_one("[data-spec='document_reference']")
        section_reference_tag = soup.select_one("[data-spec='section_reference']")
        reference_tree = [[document_reference_tag, section_reference_tag]]

        # Act
        results = list(traverse_reference_tree(reference_tree))

        # Assert
        assert len(results) == 2

        document_reference_tag, document, sections = results[0]
        assert document_reference_tag["data-tag_id"] == "2"
        assert document == DocumentReferenceData(type=DocumentType.unknown_arrete, id="L123")
        assert sections == []

        section_reference_tag, document, sections = results[1]
        assert section_reference_tag["data-tag_id"] == "1"
        assert document == DocumentReferenceData(type=DocumentType.unknown_arrete, id="L123")
        assert sections == [
            SectionReferenceData(type=SectionType.ARTICLE, start_num="456", parent_reference="2")
        ]

    def test_traverse_section_as_root(self):
        # Arrange
        soup = BeautifulSoup(
            """
            <div>
                <a
                    data-spec="section_reference"
                    data-tag_id="1"
                    data-parent_reference="2"
                    data-start_num="456"
                    data-type="alinea"
                >
                    Section 1
                </a>
                <a
                    data-spec="section_reference"
                    data-tag_id="2"
                    data-start_num="L123"
                    data-type="article"
                >
                    Parent
                </a>
            </div>
            """,
            features="html.parser",
        )
        section_reference_tag1 = soup.select_one("[data-spec='section_reference'][data-tag_id='1']")
        section_reference_tag2 = soup.select_one("[data-spec='section_reference'][data-tag_id='2']")
        reference_tree = [[section_reference_tag2, section_reference_tag1]]

        # Act
        results = list(traverse_reference_tree(reference_tree))

        # Assert
        assert len(results) == 2

        article_reference_tag, document, sections = results[0]
        assert article_reference_tag["data-tag_id"] == "2"
        assert document is None
        assert sections == [SectionReferenceData(type=SectionType.ARTICLE, start_num="L123")]

        alinea_reference_tag, document, sections = results[1]
        assert alinea_reference_tag["data-tag_id"] == "1"
        assert document is None
        assert len(sections) == 2
        assert sections == [
            SectionReferenceData(type=SectionType.ARTICLE, start_num="L123"),
            SectionReferenceData(type=SectionType.ALINEA, start_num="456", parent_reference="2"),
        ]


class TestIterReferenceTrees(unittest.TestCase):

    def test_several_reference_trees(self):
        # Arrange
        soup = BeautifulSoup(
            """
            <div>
                <a
                    data-spec="section_reference"
                    data-tag_id="1"
                    data-parent_reference="2"
                    data-type="article"
                >
                    Section 1
                </a>
                <a
                    data-spec="document_reference"
                    data-tag_id="2"
                    data-type="arrete"
                >
                    Parent Document
                </a>
                <a
                    data-spec="section_reference"
                    data-tag_id="3"
                    data-parent_reference="4"
                    data-type="article"
                >
                    Section 2
                </a>
                <a
                    data-spec="document_reference"
                    data-tag_id="4"
                    data-type="arrete"
                >
                    Another Document
                </a>
            </div>
            """,
            features="html.parser",
        )

        # Act
        reference_trees = list(iter_reference_trees(soup))

        # Assert
        assert len(reference_trees) == 2

        assert len(reference_trees[0]) == 1
        assert [tag["data-tag_id"] for tag in reference_trees[0][0]] == ["2", "1"]

        assert len(reference_trees[1]) == 1
        assert [tag["data-tag_id"] for tag in reference_trees[1][0]] == ["4", "3"]
