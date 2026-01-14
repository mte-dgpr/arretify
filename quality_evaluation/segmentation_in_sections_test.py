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
    SectionTree,
    SectionTreeNode,
    _generate_string_for_section_tree,
    _generate_string_for_section_tree_node_list,
    _normalize_section_tree_string,
    build_section_tree,
    compute_evaluation,
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


class TestGenerateStringForSectionTreeNodeList(unittest.TestCase):
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
        result = _generate_string_for_section_tree_node_list(children)

        # Assert
        assert result == "1\n>1.1\n"


class TestGenerateStringForSectionTree(unittest.TestCase):
    def test_main_and_appendix(self):
        # Arrange
        section_tree = SectionTree(
            main=[
                SectionTreeNode(
                    data=SectionData(number="1", title="Article 1", type="article"),
                    children=[],
                ),
                SectionTreeNode(
                    data=SectionData(number="2", title="Article 2", type="article"),
                    children=[],
                ),
            ],
            appendix=[
                SectionTreeNode(
                    data=SectionData(number="A", title="Annexe A", type="annexe"),
                    children=[],
                ),
            ],
        )

        # Act
        string = _generate_string_for_section_tree(section_tree)

        # Assert
        assert string == "1\n2\n-\nA"


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


class TestComputeEvaluation(unittest.TestCase):
    def test_compute_evaluation_without_diff(self):
        # Arrange
        ground_truth = SectionTree(
            main=[
                SectionTreeNode(data=SectionData(number="1", type="titre"), children=[]),
            ],
            appendix=None,
        )
        result = SectionTree(
            main=[
                SectionTreeNode(data=SectionData(number="1", type="titre"), children=[]),
            ],
            appendix=None,
        )

        # Act
        evaluation, (string_result, string_ground_truth) = compute_evaluation(
            file_name="test.pdf",
            section_tree_result=result,
            section_tree_ground_truth=ground_truth,
            baseline_run=None,
        )

        # Assert
        assert evaluation.similarity == 1.0
        assert string_result == string_ground_truth

    def test_compute_evaluation_with_diff(self):
        # Arrange
        ground_truth = SectionTree(
            main=[
                SectionTreeNode(data=SectionData(number="1", type="titre"), children=[]),
            ],
            appendix=None,
        )
        result = SectionTree(
            main=[
                SectionTreeNode(data=SectionData(number="2", type="titre"), children=[]),
            ],
            appendix=None,
        )

        # Act
        evaluation, (string_result, string_ground_truth) = compute_evaluation(
            file_name="test.pdf",
            section_tree_result=result,
            section_tree_ground_truth=ground_truth,
            baseline_run=None,
        )

        # Assert
        assert evaluation.similarity < 1.0
        assert string_result != string_ground_truth
        assert "1" in string_ground_truth
        assert "2" in string_result
