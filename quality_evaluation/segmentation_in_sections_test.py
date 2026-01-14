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

# TODO : Refactor tests when this closed : https://github.com/mte-dgpr/arretify/pull/65
import unittest

from bs4 import BeautifulSoup
from segmentation_in_sections import (
    SectionTreeNode,
    _generate_string_for_section_tree,
    _normalize_section_tree_string,
    build_section_tree,
    compute_similarity,
)

from arretify.semantic_tag_specs import (
    AppendixSpec,
    ArreteData,
    ArreteSpec,
    MainSpec,
    SectionData,
    SectionSpec,
)
from arretify.utils.html_create import make_semantic_tag


class TestGenerateStringForSectionTree(unittest.TestCase):
    def test_nested_children(self):
        # Arrange
        children = [
            SectionTreeNode(
                data=SectionData(number="1", title="Section 1", type="article"),
                children=[
                    SectionTreeNode(
                        data=SectionData(number="1.1", title="Section 1.1", type="article"),
                        children=[],
                    ),
                ],
            )
        ]

        # Act
        result = _generate_string_for_section_tree(children)

        # Assert
        assert result == "1\n1.1\n"


class TestNormalizeSectionTreeString(unittest.TestCase):
    def test_pads_lines_to_max_length(self):
        # Arrange
        section_tree_string = "1\n10.5.3\n2"

        # Act
        result = _normalize_section_tree_string(section_tree_string)

        # Assert
        lines = result.splitlines()
        assert len(lines) == 3
        assert all(len(line) == 6 for line in lines)
        assert lines[0] == "1     "
        assert lines[1] == "10.5.3"
        assert lines[2] == "2     "


class TestBuildSectionTree(unittest.TestCase):

    def setUp(self):
        self.soup = BeautifulSoup("", "html.parser")

    def test_nested_sections(self):
        # Arrange
        arrete_tag = make_semantic_tag(
            self.soup,
            ArreteSpec,
            data=ArreteData(arretify_version="test-version"),
            contents=[
                make_semantic_tag(
                    self.soup,
                    MainSpec,
                    contents=[
                        make_semantic_tag(
                            self.soup,
                            SectionSpec,
                            data=SectionData(number="1", title="Section 1", type="article"),
                            contents=[
                                make_semantic_tag(
                                    self.soup,
                                    SectionSpec,
                                    data=SectionData(
                                        number="1.1", title="Section 1.1", type="article"
                                    ),
                                )
                            ],
                        )
                    ],
                )
            ],
        )
        self.soup.append(arrete_tag)

        # Act
        result = build_section_tree(self.soup)

        # Assert
        assert len(result.main) == 1
        assert result.main[0].data.number == "1"
        assert len(result.main[0].children) == 1
        assert result.main[0].children[0].data.number == "1.1"

    def test_with_appendix(self):
        # Arrange
        arrete_tag = make_semantic_tag(
            self.soup,
            ArreteSpec,
            data=ArreteData(arretify_version="test-version"),
            contents=[
                make_semantic_tag(
                    self.soup,
                    MainSpec,
                    contents=[
                        make_semantic_tag(
                            self.soup,
                            SectionSpec,
                            data=SectionData(number="1", title="Article 1", type="article"),
                        )
                    ],
                ),
                make_semantic_tag(
                    self.soup,
                    AppendixSpec,
                    contents=[
                        make_semantic_tag(
                            self.soup,
                            SectionSpec,
                            data=SectionData(number="A", title="Annexe A", type="annexe"),
                        )
                    ],
                ),
            ],
        )
        self.soup.append(arrete_tag)

        # Act
        result = build_section_tree(self.soup)

        # Assert
        assert len(result.main) == 1
        assert result.main[0].data.number == "1"
        assert result.appendix is not None
        assert len(result.appendix) == 1
        assert result.appendix[0].data.number == "A"


class TestComputeSimilarity(unittest.TestCase):
    def test_identical_trees(self):
        # Arrange
        children1 = [
            SectionTreeNode(
                data=SectionData(number="1", title="Section 1", type="article"),
                children=[
                    SectionTreeNode(
                        data=SectionData(number="1.1", title="Section 1.1", type="article"),
                        children=[],
                    ),
                ],
            )
        ]
        children2 = [
            SectionTreeNode(
                data=SectionData(number="1", title="Section 1", type="article"),
                children=[
                    SectionTreeNode(
                        data=SectionData(number="1.1", title="Section 1.1", type="article"),
                        children=[],
                    ),
                ],
            )
        ]

        # Act
        result = compute_similarity(children1, children2)

        # Assert
        assert result == 1.0

    def test_slightly_different_trees(self):
        # Arrange
        children1 = [
            SectionTreeNode(
                data=SectionData(number="1", title="Section 1", type="article"),
                children=[
                    SectionTreeNode(
                        data=SectionData(number="1.1", title="Section 1.1", type="article"),
                        children=[],
                    ),
                ],
            )
        ]
        children2 = [
            SectionTreeNode(
                data=SectionData(number="1", title="Section 1", type="article"),
                children=[
                    SectionTreeNode(
                        data=SectionData(number="1.2", title="Section 1.2", type="article"),
                        children=[],
                    ),
                ],
            )
        ]

        # Act
        result = compute_similarity(children1, children2)

        # Assert
        assert 0 < result < 1.0
